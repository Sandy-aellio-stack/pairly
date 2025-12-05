"""
Content Moderation Middleware

Pre-screens content before it reaches route handlers.
Blocks high-confidence explicit content immediately.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from backend.services.moderation.classifier_client import (
    analyze_text,
    should_block,
    should_quarantine,
    BLOCK_THRESHOLD,
    QUARANTINE_LOW
)
import json


class ContentModerationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to pre-screen content submissions.
    
    - Analyzes text in POST/PUT/PATCH requests
    - Blocks high-confidence explicit content
    - Marks suspicious content for quarantine
    - Allows safe content to proceed
    """
    
    # Routes that should be moderated
    MODERATED_ROUTES = [
        "/api/posts",
        "/api/posts/",
        "/api/profiles",
        "/api/profiles/",
        "/api/media",
        "/api/media/",
        "/api/messaging",
        "/api/messaging/",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Only check POST/PUT/PATCH requests
        if request.method not in ["POST", "PUT", "PATCH"]:
            return await call_next(request)
        
        # Check if route should be moderated
        path = request.url.path
        should_moderate = any(path.startswith(route) for route in self.MODERATED_ROUTES)
        
        if not should_moderate:
            return await call_next(request)
        
        # Try to extract text content from request body
        try:
            # Read body (but we need to restore it for the route handler)
            body = await request.body()
            
            # Parse JSON body
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                # Not JSON, skip moderation (might be multipart/form-data)
                # We'll handle images in the route itself
                return await call_next(request)
            
            # Extract text fields to analyze
            text_fields = []
            if "text" in data:
                text_fields.append(data["text"])
            if "content" in data:
                text_fields.append(data["content"])
            if "message" in data:
                text_fields.append(data["message"])
            if "bio" in data:
                text_fields.append(data["bio"])
            if "description" in data:
                text_fields.append(data["description"])
            
            combined_text = " ".join(text_fields)
            
            if combined_text.strip():
                # Analyze text
                result = analyze_text(combined_text, engine="local")
                
                # Store result in request state for route handler
                request.state.moderation = {
                    "score": result.score,
                    "is_explicit": result.is_explicit,
                    "is_suspicious": result.is_suspicious,
                    "categories": result.categories,
                    "engine": result.engine
                }
                
                # Block if explicit
                if should_block(result):
                    # Track metric
                    try:
                        from backend.services.moderation.metrics import track_block
                        track_block("text")
                    except:
                        pass
                    
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "content_policy_violation",
                            "message": "Your content violates our content policy. Please review our guidelines.",
                            "categories": result.categories,
                            "policy_url": "/docs/content-policy"
                        }
                    )
                
                # Mark for quarantine if suspicious
                if should_quarantine(result):
                    request.state.moderation["requires_quarantine"] = True
                    
                    # Track metric
                    try:
                        from backend.services.moderation.metrics import track_quarantine
                        track_quarantine("text")
                    except:
                        pass
            
            else:
                # No text content to analyze
                request.state.moderation = {
                    "score": 0.0,
                    "is_explicit": False,
                    "is_suspicious": False,
                    "categories": [],
                    "engine": "none"
                }
        
        except Exception as e:
            print(f"⚠️  Moderation middleware error: {e}")
            # On error, allow content through (fail open for now)
            # In production, consider failing closed for critical endpoints
            request.state.moderation = {
                "score": 0.0,
                "is_explicit": False,
                "is_suspicious": False,
                "categories": [],
                "engine": "error",
                "error": str(e)
            }
        
        # Continue to route handler
        response = await call_next(request)
        return response

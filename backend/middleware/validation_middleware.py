from fastapi import Request
from fastapi.responses import JSONResponse

async def validation_middleware(request: Request, call_next):
    # example: reject requests without content-type for POST/PUT
    if request.method in ("POST","PUT") and "application/json" not in request.headers.get("content-type",""):
        return JSONResponse({"detail":"Content-Type application/json required"}, status_code=415)
    return await call_next(request)

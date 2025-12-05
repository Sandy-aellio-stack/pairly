"""Post management routes.

Endpoints:
    POST /api/posts - Create new post
    GET /api/posts/{post_id} - Get post by ID
    PATCH /api/posts/{post_id} - Update post
    DELETE /api/posts/{post_id} - Soft delete post
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.models.post import Post, Visibility
from backend.models.user import User
from backend.routes.profiles import get_current_user
from beanie import PydanticObjectId

router = APIRouter(prefix="/api/posts", tags=["posts"])


class PostCreate(BaseModel):
    text: str = Field(max_length=5000)
    media: List[Dict[str, Any]] = Field(default_factory=list)
    visibility: Visibility = Visibility.PUBLIC


class PostUpdate(BaseModel):
    text: Optional[str] = Field(None, max_length=5000)
    visibility: Optional[Visibility] = None


class PostResponse(BaseModel):
    id: str
    creator_id: str
    text: str
    media: List[Dict[str, Any]]
    visibility: str
    is_archived: bool
    created_at: str
    updated_at: str


async def verify_creator_has_tiers(creator_id: PydanticObjectId) -> bool:
    """Check if creator has active subscription tiers (lazy import to avoid circular)."""
    try:
        from backend.models.subscription import SubscriptionTier
        tier = await SubscriptionTier.find_one(
            SubscriptionTier.creator_id == creator_id,
            SubscriptionTier.active == True
        )
        return tier is not None
    except Exception:
        # If subscription model not available or error, allow post
        return True


async def get_creator_profile_id(user_id: PydanticObjectId) -> Optional[PydanticObjectId]:
    """Get profile ID for a user (lazy import)."""
    try:
        from backend.models.profile import Profile
        profile = await Profile.find_one(Profile.user_id == user_id)
        return profile.id if profile else None
    except Exception:
        return None


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new post."""
    from fastapi import Request
    from backend.models.profile import Profile
    
    # Get creator's profile
    profile = await Profile.find_one(Profile.user_id == current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creator profile not found"
        )
    
    # If subscribers-only, verify creator has active tiers
    if post_data.visibility == Visibility.SUBSCRIBERS:
        has_tiers = await verify_creator_has_tiers(profile.id)
        if not has_tiers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create subscriber-only post without active subscription tiers"
            )
    
    # Check moderation status from middleware
    # Note: In a real implementation, you'd get the request object as a dependency
    # For now, we'll add default moderation fields
    moderation_status = "published"
    moderation_score = 0.0
    moderation_engine = "local_heuristic"
    
    # Create post
    post = Post(
        creator=profile,
        text=post_data.text,
        media=post_data.media,
        visibility=post_data.visibility,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Add moderation fields if they exist
    if hasattr(post, 'moderation_status'):
        post.moderation_status = moderation_status
        post.moderation_score = moderation_score
        post.moderation_engine = moderation_engine
    
    await post.insert()
    
    return PostResponse(
        id=str(post.id),
        creator_id=str(profile.id),
        text=post.text,
        media=post.media,
        visibility=post.visibility.value,
        is_archived=post.is_archived,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat()
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    """Get post by ID (public endpoint)."""
    try:
        post = await Post.get(PydanticObjectId(post_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if not post or post.is_archived:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Fetch creator to get ID
    creator = await post.creator.fetch()
    
    return PostResponse(
        id=str(post.id),
        creator_id=str(creator.id) if creator else "unknown",
        text=post.text,
        media=post.media,
        visibility=post.visibility.value,
        is_archived=post.is_archived,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat()
    )


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update post (creator only)."""
    try:
        post = await Post.get(PydanticObjectId(post_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if not post or post.is_archived:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Verify ownership
    creator = await post.creator.fetch()
    if not creator or creator.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own posts"
        )
    
    # Update fields
    if post_data.text is not None:
        post.text = post_data.text
    if post_data.visibility is not None:
        post.visibility = post_data.visibility
    
    post.updated_at = datetime.utcnow()
    await post.save()
    
    return PostResponse(
        id=str(post.id),
        creator_id=str(creator.id),
        text=post.text,
        media=post.media,
        visibility=post.visibility.value,
        is_archived=post.is_archived,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat()
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Soft delete post (creator only)."""
    try:
        post = await Post.get(PydanticObjectId(post_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Verify ownership
    creator = await post.creator.fetch()
    if not creator or creator.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts"
        )
    
    # Soft delete
    post.is_archived = True
    post.updated_at = datetime.utcnow()
    await post.save()
    
    return None

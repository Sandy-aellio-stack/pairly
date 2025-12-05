"""Feed routes with cursor pagination.

Endpoints:
    GET /api/feed/home - Personalized home feed
    GET /api/feed/creator/{creator_id} - Creator timeline

Cursor Format:
    {created_at.isoformat()}::{post_id}
    Example: 2024-12-05T10:30:00.000000::507f1f77bcf86cd799439011
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.models.post import Post, Visibility
from backend.models.user import User
from backend.routes.profiles import get_current_user
from beanie import PydanticObjectId
from beanie.operators import In, GTE, LT, And, Or

router = APIRouter(prefix="/api/feed", tags=["feed"])


class FeedPost(BaseModel):
    id: str
    creator_id: str
    creator_name: str
    creator_avatar: Optional[str]
    text: str
    media: List[dict]
    visibility: str
    created_at: str


class FeedResponse(BaseModel):
    posts: List[FeedPost]
    next_cursor: Optional[str] = None


def parse_cursor(cursor: Optional[str]) -> Optional[tuple[datetime, PydanticObjectId]]:
    """Parse cursor into (timestamp, post_id)."""
    if not cursor:
        return None
    
    try:
        timestamp_str, post_id_str = cursor.split('::')
        timestamp = datetime.fromisoformat(timestamp_str)
        post_id = PydanticObjectId(post_id_str)
        return (timestamp, post_id)
    except Exception:
        return None


def create_cursor(post: Post) -> str:
    """Create cursor from post."""
    return f"{post.created_at.isoformat()}::{str(post.id)}"


async def is_user_subscribed(user_id: PydanticObjectId, creator_id: PydanticObjectId) -> bool:
    """Check if user has active subscription to creator."""
    try:
        from backend.models.subscription import UserSubscription, SubscriptionStatus
        
        subscription = await UserSubscription.find_one(
            UserSubscription.user_id == user_id,
            UserSubscription.creator_id == creator_id,
            UserSubscription.status == SubscriptionStatus.ACTIVE
        )
        return subscription is not None
    except Exception:
        # If subscription system not available, return False
        return False


async def get_profile_by_id(profile_id: PydanticObjectId):
    """Get profile by ID (lazy import)."""
    try:
        from backend.models.profile import Profile
        return await Profile.get(profile_id)
    except Exception:
        return None


@router.get("/home", response_model=FeedResponse)
async def get_home_feed(
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=50, description="Number of posts per page"),
    current_user: User = Depends(get_current_user)
):
    """Get personalized home feed.
    
    Logic:
    1. Show public posts
    2. Show subscriber posts if user is subscribed to creator
    3. Order by created_at descending
    4. Use cursor pagination
    """
    # Parse cursor
    cursor_data = parse_cursor(cursor)
    
    # Build query
    query_conditions = [Post.is_archived == False]
    
    if cursor_data:
        timestamp, post_id = cursor_data
        # Posts older than cursor
        query_conditions.append(
            Or(
                Post.created_at < timestamp,
                And(Post.created_at == timestamp, Post.id < post_id)
            )
        )
    
    # Fetch posts (we'll filter visibility in Python for now)
    # In production, use aggregation pipeline for better performance
    posts = await Post.find(
        *query_conditions
    ).sort(-Post.created_at, -Post.id).limit(limit + 1).to_list()
    
    # Determine if there are more results
    has_more = len(posts) > limit
    if has_more:
        posts = posts[:limit]
    
    # Filter by visibility
    filtered_posts = []
    for post in posts:
        if post.visibility == Visibility.PUBLIC:
            filtered_posts.append(post)
        elif post.visibility == Visibility.SUBSCRIBERS:
            # Fetch creator
            creator = await post.creator.fetch()
            if creator:
                # Check if user is subscribed or is the creator
                if creator.user_id == current_user.id:
                    filtered_posts.append(post)
                else:
                    is_subscribed = await is_user_subscribed(current_user.id, creator.id)
                    if is_subscribed:
                        filtered_posts.append(post)
    
    # Build response
    response_posts = []
    for post in filtered_posts:
        creator = await post.creator.fetch()
        if creator:
            response_posts.append(FeedPost(
                id=str(post.id),
                creator_id=str(creator.id),
                creator_name=creator.display_name,
                creator_avatar=creator.profile_picture_url,
                text=post.text,
                media=post.media,
                visibility=post.visibility.value,
                created_at=post.created_at.isoformat()
            ))
    
    # Generate next cursor
    next_cursor = None
    if has_more and filtered_posts:
        next_cursor = create_cursor(filtered_posts[-1])
    
    return FeedResponse(
        posts=response_posts,
        next_cursor=next_cursor
    )


@router.get("/creator/{creator_id}", response_model=FeedResponse)
async def get_creator_feed(
    creator_id: str,
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=50, description="Number of posts per page"),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get creator's timeline.
    
    Respects visibility:
    - Public posts: everyone can see
    - Subscriber posts: only subscribers or creator can see
    """
    # Validate creator
    try:
        creator_profile = await get_profile_by_id(PydanticObjectId(creator_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Creator not found")
    
    if not creator_profile:
        raise HTTPException(status_code=404, detail="Creator not found")
    
    # Parse cursor
    cursor_data = parse_cursor(cursor)
    
    # Build query
    query_conditions = [
        Post.creator == creator_profile,
        Post.is_archived == False
    ]
    
    if cursor_data:
        timestamp, post_id = cursor_data
        query_conditions.append(
            Or(
                Post.created_at < timestamp,
                And(Post.created_at == timestamp, Post.id < post_id)
            )
        )
    
    # Fetch posts
    posts = await Post.find(
        *query_conditions
    ).sort(-Post.created_at, -Post.id).limit(limit + 1).to_list()
    
    # Determine if there are more results
    has_more = len(posts) > limit
    if has_more:
        posts = posts[:limit]
    
    # Check subscription status once
    is_creator = current_user and creator_profile.user_id == current_user.id
    is_subscribed = False
    if current_user and not is_creator:
        is_subscribed = await is_user_subscribed(current_user.id, creator_profile.id)
    
    # Filter by visibility
    filtered_posts = []
    for post in posts:
        if post.visibility == Visibility.PUBLIC:
            filtered_posts.append(post)
        elif post.visibility == Visibility.SUBSCRIBERS:
            if is_creator or is_subscribed:
                filtered_posts.append(post)
    
    # Build response
    response_posts = []
    for post in filtered_posts:
        response_posts.append(FeedPost(
            id=str(post.id),
            creator_id=str(creator_profile.id),
            creator_name=creator_profile.display_name,
            creator_avatar=creator_profile.profile_picture_url,
            text=post.text,
            media=post.media,
            visibility=post.visibility.value,
            created_at=post.created_at.isoformat()
        ))
    
    # Generate next cursor
    next_cursor = None
    if has_more and filtered_posts:
        next_cursor = create_cursor(filtered_posts[-1])
    
    return FeedResponse(
        posts=response_posts,
        next_cursor=next_cursor
    )

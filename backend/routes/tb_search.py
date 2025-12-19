from fastapi import APIRouter, Depends, Query
from typing import Optional

from backend.models.tb_user import TBUser
from backend.routes.tb_auth import get_current_user

router = APIRouter(prefix="/api/search", tags=["TrueBond Search"])


@router.get("/users")
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    user: TBUser = Depends(get_current_user)
):
    """Search for users by name"""
    # Search by name (case-insensitive)
    users = await TBUser.find(
        {"name": {"$regex": q, "$options": "i"}},
        {"_id": 1, "name": 1, "age": 1, "gender": 1, "bio": 1, "profile_pictures": 1, "is_online": 1}
    ).limit(limit).to_list()
    
    # Exclude current user from results
    results = [
        {
            "id": str(u.id),
            "name": u.name,
            "age": u.age,
            "gender": u.gender,
            "bio": u.bio,
            "profilePicture": u.profile_pictures[0] if u.profile_pictures else None,
            "isOnline": u.is_online
        }
        for u in users
        if str(u.id) != str(user.id)
    ]
    
    return {"results": results, "total": len(results)}

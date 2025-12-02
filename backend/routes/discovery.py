from fastapi import APIRouter, Depends, Query
from typing import Optional
from backend.models.profile import Profile
from backend.models.user import User
from backend.routes.profiles import get_current_user

router = APIRouter(prefix="/api/discover")


@router.get("/")
async def discover(
    age_min: Optional[int] = Query(None),
    age_max: Optional[int] = Query(None),
    price_max: Optional[int] = Query(None),
    online: Optional[bool] = Query(None),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius_km: Optional[int] = Query(None),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user)
):
    filters = {}

    if age_min is not None:
        filters.setdefault("age", {})
        filters["age"]["$gte"] = age_min

    if age_max is not None:
        filters.setdefault("age", {})
        filters["age"]["$lte"] = age_max

    if price_max is not None:
        filters["price_per_message"] = {"$lte": price_max}

    if online is not None:
        filters["is_online"] = online

    if lat is not None and lng is not None and radius_km is not None:
        filters["location"] = {
            "$nearSphere": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "$maxDistance": radius_km * 1000
            }
        }

    profiles = (
        await Profile.find(filters)
        .sort([("is_online", -1), ("created_at", -1)])
        .skip(offset)
        .limit(limit)
        .to_list()
    )

    return [p.dict(by_alias=True) for p in profiles]

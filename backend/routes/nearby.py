from fastapi import APIRouter, HTTPException, Depends, Query
from backend.models.user import User
from backend.models.profile import Profile
from backend.routes.auth import get_current_user
from backend.database import init_db
from motor.motor_asyncio import AsyncIOMotorClient
import os

router = APIRouter(prefix="/api/nearby", tags=["Nearby"])


@router.get("")
async def get_nearby_users(
    lat: float = Query(..., description="User's latitude"),
    lng: float = Query(..., description="User's longitude"),
    radius_km: int = Query(5, ge=1, le=50, description="Search radius in kilometers"),
    limit: int = Query(50, ge=1, le=100, description="Maximum users to return"),
    user: User = Depends(get_current_user)
):
    """
    Find nearby users using MongoDB's $geoNear aggregation.
    Returns users within the specified radius, sorted by distance.
    """
    
    # Get the MongoDB collection directly for aggregation
    from backend.config import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client.get_database("pairly")
    profiles_collection = db.profiles
    
    # Convert radius from km to meters
    max_distance_meters = radius_km * 1000
    
    pipeline = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "distanceField": "distance",
                "maxDistance": max_distance_meters,
                "spherical": True,
                "query": {
                    "is_visible_on_map": {"$ne": False},  # Include if not explicitly false
                    "location": {"$exists": True, "$ne": None}
                }
            }
        },
        {
            "$match": {
                "user_id": {"$ne": user.id}  # Exclude current user
            }
        },
        {
            "$limit": limit
        },
        {
            "$project": {
                "_id": 0,
                "user_id": {"$toString": "$user_id"},
                "display_name": 1,
                "bio": 1,
                "profile_picture_url": 1,
                "is_online": 1,
                "last_seen": 1,
                "distance": 1,
                "location": 1
            }
        }
    ]
    
    try:
        cursor = profiles_collection.aggregate(pipeline)
        nearby_users = await cursor.to_list(length=limit)
        
        # Format the response
        result = []
        for u in nearby_users:
            lat_coord = None
            lng_coord = None
            if u.get("location") and u["location"].get("coordinates"):
                lng_coord = u["location"]["coordinates"][0]
                lat_coord = u["location"]["coordinates"][1]
            
            result.append({
                "user_id": u.get("user_id"),
                "display_name": u.get("display_name", "Unknown"),
                "bio": u.get("bio", ""),
                "avatar": u.get("profile_picture_url"),
                "is_online": u.get("is_online", False),
                "last_seen": u.get("last_seen").isoformat() if u.get("last_seen") else None,
                "distance": round(u.get("distance", 0)),  # Distance in meters
                "distance_km": round(u.get("distance", 0) / 1000, 2),  # Distance in km
                "lat": lat_coord,
                "lng": lng_coord
            })
        
        return {
            "users": result,
            "count": len(result),
            "search_center": {"lat": lat, "lng": lng},
            "radius_km": radius_km
        }
        
    except Exception as e:
        # If geoNear fails (e.g., no 2dsphere index), return empty
        print(f"Nearby query error: {e}")
        raise HTTPException(500, f"Error querying nearby users: {str(e)}")
    finally:
        client.close()

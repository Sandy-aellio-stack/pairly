from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, Query
from pydantic import BaseModel
import math

from backend.models.tb_user import TBUser, GeoLocation, UserPublicProfile
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/truebond")


class LocationUpdateRequest(BaseModel):
    latitude: float
    longitude: float


class LocationService:
    @staticmethod
    async def update_location(user_id: str, lat: float, lng: float) -> dict:
        """Update user's location"""
        user = await TBUser.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.location = GeoLocation(coordinates=[lng, lat])
        user.location_updated_at = datetime.now(timezone.utc)
        user.is_online = True
        await user.save()

        return {
            "status": "updated",
            "location": {"lat": lat, "lng": lng},
            "updated_at": user.location_updated_at.isoformat()
        }

    @staticmethod
    async def get_nearby_users(
        user_id: str,
        lat: float,
        lng: float,
        radius_km: int = 50,
        limit: int = 50
    ) -> List[dict]:
        """Get nearby users based on location and preferences"""
        # Get current user for preferences
        current_user = await TBUser.get(user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update current user's location
        await LocationService.update_location(user_id, lat, lng)

        # Use user's max_distance preference if smaller than requested
        max_distance = min(radius_km, current_user.preferences.max_distance_km)
        max_distance_meters = max_distance * 1000

        # Connect to MongoDB directly for aggregation
        client = AsyncIOMotorClient(MONGO_URL)
        db = client.get_default_database()
        collection = db.tb_users

        pipeline = [
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [lng, lat]},
                    "distanceField": "distance",
                    "maxDistance": max_distance_meters,
                    "spherical": True,
                    "query": {
                        "is_active": True,
                        "location": {"$exists": True, "$ne": None}
                    }
                }
            },
            # Exclude self
            {"$match": {"_id": {"$ne": current_user.id}}},
            # Filter by preferences
            {
                "$match": {
                    "gender": current_user.preferences.interested_in,
                    "age": {
                        "$gte": current_user.preferences.min_age,
                        "$lte": current_user.preferences.max_age
                    }
                }
            },
            # Sort by distance, then last activity
            {"$sort": {"distance": 1, "location_updated_at": -1}},
            {"$limit": limit},
            # Project only public fields - NEVER include address, email, mobile
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "age": 1,
                    "gender": 1,
                    "bio": 1,
                    "profile_pictures": 1,
                    "preferences": 1,
                    "intent": 1,
                    "is_online": 1,
                    "distance": 1,
                    "location_updated_at": 1
                }
            }
        ]

        try:
            cursor = collection.aggregate(pipeline)
            users = await cursor.to_list(length=limit)

            result = []
            for u in users:
                distance_km = round(u.get("distance", 0) / 1000, 1)
                result.append({
                    "id": str(u["_id"]),
                    "name": u.get("name"),
                    "age": u.get("age"),
                    "gender": u.get("gender"),
                    "bio": u.get("bio"),
                    "profile_pictures": u.get("profile_pictures", []),
                    "intent": u.get("intent"),
                    "is_online": u.get("is_online", False),
                    "distance_km": distance_km,
                    "last_active": u.get("location_updated_at").isoformat() if u.get("location_updated_at") else None
                })

            return result

        except Exception as e:
            print(f"Nearby users query error: {e}")
            raise HTTPException(status_code=500, detail="Error fetching nearby users")
        finally:
            client.close()

    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in km using Haversine formula"""
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)

        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

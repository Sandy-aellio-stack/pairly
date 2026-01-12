"""
Privacy-Safe Geolocation Service for TrueBond
Handles location updates and nearby user queries with strict privacy controls.

Privacy Safeguards:
1. Location precision reduction before storage (~100m accuracy)
2. Grid-based approximation for nearby user distances
3. No raw coordinates in API responses
4. Short TTL for location freshness (ephemeral)
5. No historical location tracking

Architecture:
- MongoDB 2dsphere index for geo queries
- Redis for rate limiting and location freshness TTL
- Database stores reduced-precision coordinates only
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException
from pydantic import BaseModel, Field
import math
import logging
import hashlib

from backend.models.tb_user import TBUser, GeoLocation
from backend.core.redis_client import redis_client
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
import os

logger = logging.getLogger("location")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/truebond")

# Privacy configuration
LOCATION_PRECISION_DECIMALS = 3  # ~111m accuracy (0.001 degrees)
LOCATION_TTL_SECONDS = 900  # 15 minutes - location considered "stale" after this
LOCATION_UPDATE_THROTTLE_SECONDS = 30  # Minimum time between updates
DISTANCE_BUCKET_SIZE_KM = 1  # Round distances to 1km buckets


def get_db_name(mongo_url: str) -> str:
    """Extract database name from MongoDB URL"""
    db_name = mongo_url.split("/")[-1].split("?")[0] if "/" in mongo_url else "truebond"
    return db_name if db_name else "truebond"


class LocationUpdateRequest(BaseModel):
    """Request model for location update"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class PrivacyLocation:
    """
    Privacy-safe location utilities.
    All methods reduce precision to protect user privacy.
    """
    
    @staticmethod
    def reduce_precision(lat: float, lng: float, decimals: int = LOCATION_PRECISION_DECIMALS) -> Tuple[float, float]:
        """
        Reduce coordinate precision for privacy.
        
        Precision levels:
        - 3 decimals: ~111m (city block level)
        - 2 decimals: ~1.1km (neighborhood level)
        - 1 decimal: ~11km (city level)
        
        We use 3 decimals by default for reasonable nearby matching
        while protecting exact location.
        """
        reduced_lat = round(lat, decimals)
        reduced_lng = round(lng, decimals)
        return reduced_lat, reduced_lng
    
    @staticmethod
    def add_random_offset(lat: float, lng: float, max_offset_meters: int = 100) -> Tuple[float, float]:
        """
        Add small random offset to coordinates.
        Provides additional privacy without affecting nearby queries significantly.
        
        Note: Using deterministic offset based on coordinate hash for consistency.
        """
        # Create deterministic but unpredictable offset based on coordinates
        coord_hash = hashlib.md5(f"{lat:.6f},{lng:.6f}".encode()).hexdigest()
        
        # Convert hash to offset values (-1 to 1)
        lat_factor = (int(coord_hash[:8], 16) / 0xFFFFFFFF) * 2 - 1
        lng_factor = (int(coord_hash[8:16], 16) / 0xFFFFFFFF) * 2 - 1
        
        # Convert meters to degrees (approximate)
        lat_offset = (lat_factor * max_offset_meters) / 111000
        lng_offset = (lng_factor * max_offset_meters) / (111000 * math.cos(math.radians(lat)))
        
        return lat + lat_offset, lng + lng_offset
    
    @staticmethod
    def bucket_distance(distance_km: float, bucket_size: float = DISTANCE_BUCKET_SIZE_KM) -> float:
        """
        Round distance to bucket for privacy.
        Returns "< 1 km", "1-2 km", etc. style bucketed distance.
        """
        if distance_km < bucket_size:
            return bucket_size  # Show as "< 1 km"
        return math.ceil(distance_km / bucket_size) * bucket_size
    
    @staticmethod
    def format_distance_display(distance_km: float) -> str:
        """
        Format distance for display with privacy.
        Never shows exact distance.
        """
        if distance_km < 1:
            return "< 1 km"
        elif distance_km < 5:
            return f"~{int(distance_km)} km"
        elif distance_km < 10:
            return "< 10 km"
        elif distance_km < 25:
            return "< 25 km"
        elif distance_km < 50:
            return "< 50 km"
        else:
            return f"~{int(distance_km / 10) * 10} km"
    
    @staticmethod
    def is_location_fresh(updated_at: Optional[datetime], ttl_seconds: int = LOCATION_TTL_SECONDS) -> bool:
        """Check if location is still fresh (within TTL)"""
        if not updated_at:
            return False
        
        age = (datetime.now(timezone.utc) - updated_at).total_seconds()
        return age < ttl_seconds


class LocationService:
    """
    Production location service with privacy controls.
    
    Features:
    - Precision reduction before storage
    - Rate limiting on updates
    - TTL-based freshness tracking
    - Privacy-safe distance bucketing
    """
    
    @staticmethod
    async def can_update_location(user_id: str) -> bool:
        """
        Check if user can update location (rate limiting).
        Prevents high-frequency writes.
        """
        if not redis_client.is_connected():
            return True  # Allow without Redis
        
        throttle_key = f"location:throttle:{user_id}"
        
        try:
            exists = await redis_client.redis.exists(throttle_key)
            return not exists
        except Exception as e:
            logger.warning(f"Throttle check failed: {e}")
            return True
    
    @staticmethod
    async def set_update_throttle(user_id: str):
        """Set throttle marker for location updates"""
        if not redis_client.is_connected():
            return
        
        throttle_key = f"location:throttle:{user_id}"
        
        try:
            await redis_client.redis.setex(
                throttle_key,
                LOCATION_UPDATE_THROTTLE_SECONDS,
                "1"
            )
        except Exception as e:
            logger.warning(f"Failed to set throttle: {e}")
    
    @staticmethod
    async def update_location(user_id: str, lat: float, lng: float) -> dict:
        """
        Update user's location with privacy protection.
        
        Privacy measures:
        1. Reduce coordinate precision before storage
        2. Rate limit updates to prevent tracking
        3. Mark location with timestamp for TTL
        """
        user = await TBUser.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check rate limit
        can_update = await LocationService.can_update_location(user_id)
        if not can_update:
            # Return success but don't update (throttled)
            return {
                "status": "throttled",
                "message": "Location update rate limited",
                "updated_at": user.location_updated_at.isoformat() if user.location_updated_at else None
            }
        
        # Reduce precision for privacy (stores ~100m accuracy)
        safe_lat, safe_lng = PrivacyLocation.reduce_precision(lat, lng)
        
        # Update user location
        user.location = GeoLocation(coordinates=[safe_lng, safe_lat])
        user.location_updated_at = datetime.now(timezone.utc)
        user.is_online = True
        await user.save()
        
        # Set update throttle
        await LocationService.set_update_throttle(user_id)
        
        # Track location freshness in Redis for TTL
        await LocationService._set_location_freshness(user_id)
        
        logger.debug(f"Location updated for user {user_id}")
        
        return {
            "status": "updated",
            "updated_at": user.location_updated_at.isoformat()
            # NOTE: We do NOT return coordinates in response
        }
    
    @staticmethod
    async def _set_location_freshness(user_id: str):
        """Track location freshness with TTL in Redis"""
        if not redis_client.is_connected():
            return
        
        freshness_key = f"location:fresh:{user_id}"
        
        try:
            await redis_client.redis.setex(
                freshness_key,
                LOCATION_TTL_SECONDS,
                datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            logger.warning(f"Failed to set freshness: {e}")
    
    @staticmethod
    async def is_location_fresh_redis(user_id: str) -> bool:
        """Check if user's location is fresh via Redis TTL"""
        if not redis_client.is_connected():
            return False
        
        freshness_key = f"location:fresh:{user_id}"
        
        try:
            exists = await redis_client.redis.exists(freshness_key)
            return exists > 0
        except Exception:
            return False
    
    @staticmethod
    async def get_nearby_users(
        user_id: str,
        lat: float,
        lng: float,
        radius_km: int = 50,
        limit: int = 50
    ) -> List[dict]:
        """
        Get nearby users with privacy-safe distance display.
        
        Privacy measures:
        1. Query uses reduced-precision coordinates
        2. Distances are bucketed (not exact)
        3. No raw coordinates returned
        4. Only public profile fields included
        5. Stale locations excluded
        
        Geo Query:
        - Uses MongoDB $geoNear with 2dsphere index
        - Filters by user preferences (gender, age, distance)
        - Sorts by distance, then activity
        """
        current_user = await TBUser.get(user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update requester's location (this respects throttling)
        await LocationService.update_location(user_id, lat, lng)
        
        # Reduce precision for query
        query_lat, query_lng = PrivacyLocation.reduce_precision(lat, lng)
        
        # Respect user's max distance preference
        max_distance = min(radius_km, current_user.preferences.max_distance_km)
        max_distance_meters = max_distance * 1000
        
        # Calculate location freshness cutoff
        freshness_cutoff = datetime.now(timezone.utc) - timedelta(seconds=LOCATION_TTL_SECONDS)
        
        # Connect to MongoDB for aggregation
        client_kwargs = {}
        if "mongodb+srv" in MONGO_URL or "ssl=true" in MONGO_URL.lower():
            client_kwargs["tlsCAFile"] = certifi.where()
        
        client = AsyncIOMotorClient(MONGO_URL, **client_kwargs)
        db_name = get_db_name(MONGO_URL)
        db = client[db_name]
        collection = db.tb_users
        
        pipeline = [
            # Stage 1: Geo query with distance calculation
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [query_lng, query_lat]},
                    "distanceField": "distance_meters",
                    "maxDistance": max_distance_meters,
                    "spherical": True,
                    "query": {
                        "is_active": True,
                        "location": {"$exists": True, "$ne": None},
                        # Only include users with fresh locations
                        "location_updated_at": {"$gte": freshness_cutoff},
                        # Respect privacy: exclude users who hide from search
                        "settings.safety.hide_from_search": {"$ne": True}
                    }
                }
            },
            # Stage 2: Exclude self
            {"$match": {"_id": {"$ne": current_user.id}}},
            # Stage 3: Filter by preferences
            {
                "$match": {
                    "gender": current_user.preferences.interested_in,
                    "age": {
                        "$gte": current_user.preferences.min_age,
                        "$lte": current_user.preferences.max_age
                    }
                }
            },
            # Stage 4: Check mutual visibility preferences
            # Only show users who want to be visible
            {
                "$match": {
                    "$or": [
                        {"settings.privacy.show_distance": True},
                        {"settings.privacy.show_distance": {"$exists": False}}
                    ]
                }
            },
            # Stage 5: Sort by distance, then activity
            {"$sort": {"distance_meters": 1, "location_updated_at": -1}},
            # Stage 6: Limit results
            {"$limit": limit},
            # Stage 7: Project ONLY public fields
            # NEVER include: address, email, mobile, exact location
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
                    "distance_meters": 1,
                    "location_updated_at": 1,
                    "settings.privacy": 1
                }
            }
        ]
        
        try:
            cursor = collection.aggregate(pipeline)
            users = await cursor.to_list(length=limit)
            
            result = []
            for u in users:
                # Convert distance to km and apply privacy bucketing
                distance_km_raw = u.get("distance_meters", 0) / 1000
                distance_km_bucketed = PrivacyLocation.bucket_distance(distance_km_raw)
                distance_display = PrivacyLocation.format_distance_display(distance_km_raw)
                
                # Check if user allows showing distance
                privacy = u.get("settings", {}).get("privacy", {})
                show_distance = privacy.get("show_distance", True)
                
                # Determine online status display
                show_online = privacy.get("show_online", True)
                is_online = u.get("is_online", False) if show_online else None
                
                # Calculate last active (respecting privacy)
                location_updated = u.get("location_updated_at")
                last_active = None
                if privacy.get("show_last_seen", True) and location_updated:
                    last_active = LocationService._format_last_active(location_updated)
                
                result.append({
                    "id": str(u["_id"]),
                    "name": u.get("name"),
                    "age": u.get("age"),
                    "gender": u.get("gender"),
                    "bio": u.get("bio"),
                    "profile_pictures": u.get("profile_pictures", []),
                    "intent": u.get("intent"),
                    # Privacy-safe distance (bucketed, not exact)
                    "distance_km": distance_km_bucketed if show_distance else None,
                    "distance_display": distance_display if show_distance else "Nearby",
                    # Privacy-respecting presence
                    "is_online": is_online,
                    "last_active": last_active,
                    # Location freshness indicator (not exact time)
                    "location_fresh": PrivacyLocation.is_location_fresh(location_updated)
                })
            
            logger.debug(f"Found {len(result)} nearby users for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Nearby users query error: {e}")
            raise HTTPException(status_code=500, detail="Error fetching nearby users")
        finally:
            client.close()
    
    @staticmethod
    def _format_last_active(dt: datetime) -> str:
        """Format last active time with privacy (no exact times)"""
        if not dt:
            return None
        
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        if diff.total_seconds() < 300:  # 5 minutes
            return "Active now"
        elif diff.total_seconds() < 3600:  # 1 hour
            return "Active recently"
        elif diff.total_seconds() < 86400:  # 24 hours
            hours = int(diff.total_seconds() / 3600)
            return f"Active {hours}h ago"
        else:
            days = int(diff.total_seconds() / 86400)
            if days == 1:
                return "Active yesterday"
            return f"Active {days}d ago"
    
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
    
    @staticmethod
    async def mark_location_stale(user_id: str):
        """
        Mark user's location as stale.
        Called when user goes offline or logs out.
        """
        if redis_client.is_connected():
            freshness_key = f"location:fresh:{user_id}"
            try:
                await redis_client.redis.delete(freshness_key)
            except Exception as e:
                logger.warning(f"Failed to mark location stale: {e}")
        
        # Also update is_online in database
        try:
            user = await TBUser.get(user_id)
            if user:
                user.is_online = False
                await user.save()
        except Exception as e:
            logger.warning(f"Failed to update online status: {e}")
    
    @staticmethod
    async def get_location_stats() -> dict:
        """Get location system stats (for admin/monitoring)"""
        stats = {
            "config": {
                "precision_decimals": LOCATION_PRECISION_DECIMALS,
                "precision_meters": round(111000 * (10 ** -LOCATION_PRECISION_DECIMALS)),
                "ttl_seconds": LOCATION_TTL_SECONDS,
                "throttle_seconds": LOCATION_UPDATE_THROTTLE_SECONDS,
                "distance_bucket_km": DISTANCE_BUCKET_SIZE_KM
            }
        }
        
        # Get count of fresh locations from Redis
        if redis_client.is_connected():
            try:
                keys = await redis_client.redis.keys("location:fresh:*")
                stats["active_users_with_fresh_location"] = len(keys)
            except Exception:
                stats["active_users_with_fresh_location"] = "unknown"
        
        return stats

"""
Privacy-Safe Geolocation Service for Luveloop
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
from backend.models.tb_user import TBUser, GeoLocation
from backend.core.redis_client import redis_client

logger = logging.getLogger("location")

# Privacy configuration

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
        print("=" * 60)
        print("DEBUG: update_location called")
        print(f"  user_id: {user_id}")
        print(f"  lat: {lat}, lng: {lng}")
        print("=" * 60)
        
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
        print(f"DEBUG: Reduced precision - safe_lat: {safe_lat}, safe_lng: {safe_lng}")
        
        # Update user location
        user.location = GeoLocation(coordinates=[safe_lng, safe_lat])
        user.location_updated_at = datetime.now(timezone.utc)
        user.is_online = True
        await user.save()
        
        print(f"DEBUG: Location saved - location={user.location}, updated_at={user.location_updated_at}")
        
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
        Uses the global Beanie/MongoDB connection.
        """
        current_user = await TBUser.get(user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update requester's location (this respects throttling)
        await LocationService.update_location(user_id, lat, lng)
        
        # Reduce precision for query
        query_lat, query_lng = PrivacyLocation.reduce_precision(lat, lng)
        max_distance_meters = radius_km * 1000
        
        # Build geo query - keep simple for $geoNear stage (nested fields cause issues)
        geo_query = {
            "is_active": True,
            "location": {"$exists": True, "$ne": None},
        }
        
        pipeline = [
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [query_lng, query_lat]},
                    "distanceField": "distance_meters",
                    "maxDistance": max_distance_meters,
                    "spherical": True,
                    "query": geo_query
                }
            },
            {
                "$match": {
                    "_id": {"$ne": current_user.id},
                    "settings.safety.hide_from_search": {"$ne": True}
                }
            },
            {"$limit": limit}
        ]
        
        try:
            # Use Beanie's aggregate
            users = await TBUser.aggregate(pipeline).to_list()
            
            result = []
            for u in users:
                # Convert distance to km and apply privacy bucketing
                distance_km_raw = u.get("distance_meters", 0) / 1000
                distance_km_bucketed = PrivacyLocation.bucket_distance(distance_km_raw)
                distance_display = PrivacyLocation.format_distance_display(distance_km_raw)
                
                # Get privacy settings
                privacy = u.get("settings", {}).get("privacy", {})
                show_distance = privacy.get("show_distance", True)
                show_online = privacy.get("show_online", True)
                is_online = u.get("is_online", False) if show_online else None
                
                location_updated = u.get("location_updated_at")
                last_active = None
                if privacy.get("show_last_seen", True) and location_updated:
                    last_active = LocationService._format_last_active(location_updated)
                
                first_photo = u.get("profile_pictures", [None])[0] if u.get("profile_pictures") else None
                logger.debug(f"Nearby: user {str(u['_id'])} ({u.get('name')}) distance_km={distance_km_bucketed}")
                result.append({
                    "id": str(u["_id"]),
                    "name": u.get("name"),
                    "age": u.get("age"),
                    "gender": u.get("gender"),
                    "bio": u.get("bio"),
                    "photo": first_photo,
                    "profile_picture": first_photo,
                    "profile_pictures": u.get("profile_pictures", []),
                    "intent": u.get("intent"),
                    "distance_km": distance_km_bucketed if show_distance else None,
                    "distance_display": distance_display if show_distance else "Nearby",
                    "is_online": is_online,
                    "status": "suspended" if u.get("is_suspended") else "active",
                    "last_active": last_active,
                    "location_fresh": PrivacyLocation.is_location_fresh(location_updated)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Nearby users query error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error fetching nearby users")

    @staticmethod
    async def get_nearby_users_with_location(
        user_id: str,
        lat: float,
        lng: float,
        radius_km: int = 50,
        limit: int = 50
    ) -> List[dict]:
        """
        Get nearby users WITH jittered location for map display.
        Uses the global Beanie/MongoDB connection.
        """
        import random
        
        current_user = await TBUser.get(user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Reduce precision for query
        query_lat, query_lng = PrivacyLocation.reduce_precision(lat, lng)
        max_distance_meters = radius_km * 1000
        
        geo_query = {
            "is_active": True,
            "location": {"$exists": True, "$ne": None},
        }
        
        pipeline = [
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [query_lng, query_lat]},
                    "distanceField": "distance_meters",
                    "maxDistance": max_distance_meters,
                    "spherical": True,
                    "query": geo_query
                }
            },
            {
                "$match": {
                    "_id": {"$ne": current_user.id},
                    "settings.safety.hide_from_search": {"$ne": True}
                }
            },
            {"$sort": {"distance_meters": 1}},
            {"$limit": limit}
        ]
        
        try:
            users = await TBUser.aggregate(pipeline).to_list()
            
            result = []
            for u in users:
                distance_km_raw = u.get("distance_meters", 0) / 1000
                distance_km_bucketed = PrivacyLocation.bucket_distance(distance_km_raw)
                distance_display = PrivacyLocation.format_distance_display(distance_km_raw)
                
                privacy = u.get("settings", {}).get("privacy", {})
                show_distance = privacy.get("show_distance", True)
                show_online = privacy.get("show_online", True)
                is_online = u.get("is_online", False) if show_online else None
                
                # Jitter location for privacy
                loc = u.get("location", {})
                coords = loc.get("coordinates", [lng, lat])
                u_lng, u_lat = coords
                
                # Add random jitter (~50-100m)
                jitter_lat = u_lat + (random.random() - 0.5) * 0.001
                jitter_lng = u_lng + (random.random() - 0.5) * 0.001
                
                map_first_photo = u.get("profile_pictures", [None])[0] if u.get("profile_pictures") else None
                logger.debug(f"Map nearby: user {str(u['_id'])} ({u.get('name')}) lat={jitter_lat:.4f} lng={jitter_lng:.4f}")
                result.append({
                    "id": str(u["_id"]),
                    "name": u.get("name"),
                    "age": u.get("age"),
                    "gender": u.get("gender"),
                    "bio": u.get("bio"),
                    "photo": map_first_photo,
                    "profile_picture": map_first_photo,
                    "profile_pictures": u.get("profile_pictures", []),
                    "intent": u.get("intent"),
                    "lat": jitter_lat,
                    "lng": jitter_lng,
                    "distance_km": distance_km_bucketed if show_distance else None,
                    "distance_display": distance_display if show_distance else "Nearby",
                    "is_online": is_online,
                    "status": "suspended" if u.get("is_suspended") else "active",
                    "last_seen": u.get("last_seen").isoformat() if u.get("last_seen") else None
                })
            
            return result
        except Exception as e:
            logger.error(f"Nearby map query error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error fetching map users")
    
    @staticmethod
    async def mark_location_stale(user_id: str):
        """
        Mark user location as stale (e.g., on logout or disconnect).
        Clears location_updated_at and removes Redis freshness marker.
        """
        try:
            from bson import ObjectId
            user_oid = ObjectId(user_id)
            
            # 1. Update DB
            await TBUser.find_one(TBUser.id == user_oid).update({
                "$set": {
                    "location_updated_at": None,
                    "is_online": False
                }
            })
            
            # 2. Clear Redis
            if redis_client.is_connected():
                freshness_key = f"location:fresh:{user_id}"
                await redis_client.redis.delete(freshness_key)
                
            logger.info(f"Location marked stale for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to mark location stale for user {user_id}: {e}")

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

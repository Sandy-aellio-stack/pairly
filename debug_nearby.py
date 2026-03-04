#!/usr/bin/env python3
"""
Debug script to check MongoDB for nearby users functionality.
Run: python debug_nearby.py
"""
import asyncio
import os
from dotenv import load_dotenv

# Load backend .env
env_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
load_dotenv(dotenv_path=env_path)

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/truebond")

async def check_mongodb():
    """Check MongoDB for users and location data"""
    from motor.motor_asyncio import AsyncIOMotorClient
    import certifi
    
    print("=" * 60)
    print("MongoDB Nearby Debug Script")
    print("=" * 60)
    
    # Connect to MongoDB
    client_kwargs = {}
    if "mongodb+srv" in MONGO_URL:
        client_kwargs["tlsCAFile"] = certifi.where()
    
    client = AsyncIOMotorClient(MONGO_URL, **client_kwargs)
    db_name = MONGO_URL.split("/")[-1].split("?")[0] if "/" in MONGO_URL else "truebond"
    db = client[db_name]
    
    # Check 1: Get indexes on tb_users collection
    print("\n[1] Checking indexes on tb_users collection:")
    indexes = await db.tb_users.list_indexes().to_list(length=100)
    print(f"    Found {len(indexes)} indexes:")
    for idx in indexes:
        print(f"      - {idx}")
    
    has_2dsphere = any(
        "2dsphere" in str(idx.get("key", {})) or "2dsphere" in str(idx.get("2dsphere", {}))
        for idx in indexes
    )
    print(f"    2dsphere index exists: {has_2dsphere}")
    
    # Check 2: Count total users
    print("\n[2] User counts:")
    total_users = await db.tb_users.count_documents({})
    print(f"    Total users: {total_users}")
    
    # Check 3: Users with location
    with_location = await db.tb_users.count_documents({
        "location": {"$exists": True, "$ne": None}
    })
    print(f"    Users with location: {with_location}")
    
    # Check 4: Users with is_active=True
    active_users = await db.tb_users.count_documents({"is_active": True})
    print(f"    Active users: {active_users}")
    
    # Check 5: Sample user data (first 3)
    print("\n[3] Sample user data (first 3 users with location):")
    cursor = db.tb_users.find({
        "location": {"$exists": True, "$ne": None}
    }).limit(3)
    
    async for user in cursor:
        print(f"    User ID: {user.get('_id')}")
        print(f"      name: {user.get('name')}")
        print(f"      gender: {user.get('gender')}")
        print(f"      age: {user.get('age')}")
        print(f"      is_active: {user.get('is_active')}")
        print(f"      location: {user.get('location')}")
        print(f"      location_updated_at: {user.get('location_updated_at')}")
        print(f"      preferences: {user.get('preferences')}")
        print(f"      settings.safety.hide_from_search: {user.get('settings', {}).get('safety', {}).get('hide_from_search')}")
        print()
    
    # Check 6: Sample user WITHOUT location
    print("\n[4] Sample user WITHOUT location:")
    cursor2 = db.tb_users.find({
        "location": {"$exists": False}
    }).limit(1)
    
    async for user in cursor2:
        print(f"    User ID: {user.get('_id')}")
        print(f"      name: {user.get('name')}")
        print(f"      location: {user.get('location')}")
        print(f"      preferences: {user.get('preferences')}")
    
    # Check 7: Try a test geo query
    print("\n[5] Test geo query (Chennai: 13.1959, 80.1685):")
    test_lat, test_lng = 13.1959, 80.1685
    
    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [test_lng, test_lat]},
                "distanceField": "distance_meters",
                "maxDistance": 50000,  # 50km
                "spherical": True,
                "query": {
                    "is_active": True,
                    "location": {"$exists": True, "$ne": None},
                    "settings.safety.hide_from_search": {"$ne": True}
                }
            }
        },
        {"$limit": 5}
    ]
    
    try:
        cursor3 = db.tb_users.aggregate(pipeline)
        results = await cursor3.to_list(length=5)
        print(f"    Found {len(results)} users in 50km radius")
        for r in results:
            print(f"      - {r.get('name')}: {r.get('distance_meters', 0)/1000:.1f}km away")
    except Exception as e:
        print(f"    ERROR in geo query: {e}")
        print(f"    This usually means the 2dsphere index is missing!")
    
    print("\n" + "=" * 60)
    print("Debug complete!")
    print("=" * 60)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_mongodb())

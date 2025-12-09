"""Migration: Add Post and Subscription models.

This migration:
1. Creates indexes for Post collection
2. Creates indexes for SubscriptionTier collection
3. Creates indexes for UserSubscription collection
4. Optionally adds a default subscription tier (commented out)

Run this migration AFTER:
- Adding Post, SubscriptionTier, and UserSubscription to database.py init_beanie()

Manual Steps Required:
----------------------
1. Update backend/database.py:
   
   from backend.models.post import Post
   from backend.models.subscription import SubscriptionTier, UserSubscription
   
   await init_beanie(
       database=database,
       document_models=[
           User,
           Session,
           # ... existing models ...
           Post,              # ADD THIS
           SubscriptionTier,  # ADD THIS
           UserSubscription,  # ADD THIS
       ]
   )

2. Update backend/main.py to include new routes:
   
   from backend.routes import posts, feed
   
   app.include_router(posts.router)
   app.include_router(feed.router)

3. Run this migration script:
   python -m backend.migrations.0001_add_post_and_subscription
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings


async def run_migration():
    """Run the migration."""
    print("Starting migration: 0001_add_post_and_subscription")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client.get_database("pairly")
    
    try:
        # Create indexes for posts collection
        print("Creating indexes for 'posts' collection...")
        posts_collection = db.posts
        
        await posts_collection.create_index(
            [("creator", 1), ("created_at", -1)],
            name="creator_timeline"
        )
        print("  ✓ Created index: creator_timeline")
        
        await posts_collection.create_index(
            [("visibility", 1), ("created_at", -1)],
            name="public_feed"
        )
        print("  ✓ Created index: public_feed")
        
        await posts_collection.create_index(
            [("is_archived", 1), ("created_at", -1)],
            name="active_posts"
        )
        print("  ✓ Created index: active_posts")
        
        # Create indexes for subscription_tiers collection
        print("\nCreating indexes for 'subscription_tiers' collection...")
        tiers_collection = db.subscription_tiers
        
        await tiers_collection.create_index(
            [("creator_id", 1), ("active", 1)],
            name="creator_active_tiers"
        )
        print("  ✓ Created index: creator_active_tiers")
        
        await tiers_collection.create_index(
            [("tier_id", 1)],
            name="tier_lookup"
        )
        print("  ✓ Created index: tier_lookup")
        
        # Create indexes for user_subscriptions collection
        print("\nCreating indexes for 'user_subscriptions' collection...")
        subs_collection = db.user_subscriptions
        
        await subs_collection.create_index(
            [("user_id", 1), ("status", 1)],
            name="user_active_subs"
        )
        print("  ✓ Created index: user_active_subs")
        
        await subs_collection.create_index(
            [("creator_id", 1), ("status", 1)],
            name="creator_subscribers"
        )
        print("  ✓ Created index: creator_subscribers")
        
        await subs_collection.create_index(
            [("stripe_subscription_id", 1)],
            name="stripe_sub_lookup"
        )
        print("  ✓ Created index: stripe_sub_lookup")
        
        await subs_collection.create_index(
            [("razorpay_subscription_id", 1)],
            name="razorpay_sub_lookup"
        )
        print("  ✓ Created index: razorpay_sub_lookup")
        
        # Optional: Create a default subscription tier
        # Uncomment and modify to add default tiers for testing
        """
        print("\nCreating default subscription tier...")
        from bson import ObjectId
        from datetime import datetime, timezone
        
        default_tier = {
            "_id": ObjectId(),
            "creator_id": ObjectId("YOUR_CREATOR_ID_HERE"),  # Replace with actual creator ID
            "tier_id": "default_tier",
            "name": "Basic Tier",
            "price_cents": 999,  # $9.99
            "currency": "usd",
            "interval": "month",
            "benefits": [
                "Access to subscriber-only posts",
                "Priority support",
                "Exclusive content"
            ],
            "active": True,
            "is_default": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        await tiers_collection.insert_one(default_tier)
        print("  ✓ Created default subscription tier")
        """
        
        print("\n✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("  1. Update backend/database.py to include new models")
        print("  2. Update backend/main.py to include new routes")
        print("  3. Restart backend server")
        print("  4. Test with: curl http://localhost:8001/api/posts")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(run_migration())

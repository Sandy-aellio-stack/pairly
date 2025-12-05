"""Migration: Sync Subscription State and Create Indexes

This migration:
1. Creates indexes for UserSubscription and PaymentMethod collections
2. Backfills subscription data from existing payment records (if any)
3. Generates migration report
4. Provides manual review checklist

Run: python -m backend.migrations.0002_sync_subscription_state
"""

import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import os
from beanie import init_beanie

from backend.models.payment_subscription import UserSubscription, PaymentMethod
from backend.config import settings

async def create_indexes():
    """Create database indexes for subscription collections"""
    print("Creating indexes...")
    
    # UserSubscription indexes
    await UserSubscription.get_motor_collection().create_index("user_id")
    await UserSubscription.get_motor_collection().create_index("tier_id")
    await UserSubscription.get_motor_collection().create_index("provider_subscription_id")
    await UserSubscription.get_motor_collection().create_index(
        [("user_id", 1), ("tier_id", 1)]
    )
    await UserSubscription.get_motor_collection().create_index(
        [("status", 1), ("current_period_end", 1)]
    )
    
    # PaymentMethod indexes
    await PaymentMethod.get_motor_collection().create_index("user_id")
    await PaymentMethod.get_motor_collection().create_index("provider_payment_method_id")
    
    print("✓ Indexes created successfully")

async def backfill_subscriptions():
    """Backfill subscription data from existing payment records
    
    This is a safe no-op since we're adding subscriptions as a new feature.
    Existing credits transactions remain independent.
    """
    print("Checking for existing payment data to backfill...")
    
    # In a real scenario, you might have legacy subscription data
    # to migrate from another system or table
    # For now, this is intentionally a no-op
    
    existing_subscriptions = await UserSubscription.count()
    print(f"✓ Found {existing_subscriptions} existing subscription records")
    
    return existing_subscriptions

async def generate_migration_report():
    """Generate migration report"""
    report = {
        "migration_id": "0002_sync_subscription_state",
        "executed_at": datetime.now().isoformat(),
        "indexes_created": True,
        "subscriptions_count": await UserSubscription.count(),
        "payment_methods_count": await PaymentMethod.count()
    }
    
    print("\n" + "="*60)
    print("MIGRATION REPORT")
    print("="*60)
    for key, value in report.items():
        print(f"{key}: {value}")
    print("="*60)
    
    return report

async def run_migration():
    """Execute the migration"""
    print("Starting migration: 0002_sync_subscription_state")
    print(f"Database: {settings.MONGODB_URI}\n")
    
    # Initialize Beanie
    client = AsyncIOMotorClient(settings.MONGO_URL)
    db = client.get_default_database()
    
    await init_beanie(
        database=db,
        document_models=[
            UserSubscription,
            PaymentMethod
        ]
    )
    
    try:
        # Step 1: Create indexes
        await create_indexes()
        
        # Step 2: Backfill data
        await backfill_subscriptions()
        
        # Step 3: Generate report
        await generate_migration_report()
        
        print("\n✓ Migration completed successfully\n")
        
        # Manual review checklist
        print("MANUAL REVIEW CHECKLIST:")
        print("[ ] Verify indexes exist in MongoDB Atlas/Compass")
        print("[ ] Check that UserSubscription documents have correct schema")
        print("[ ] Verify Redis connection is working")
        print("[ ] Test webhook endpoints with provider test events")
        print("[ ] Confirm Stripe/Razorpay API keys are configured")
        print("[ ] Review subscription tier metadata (price_ids)")
        print("[ ] Test subscription creation flow end-to-end")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(run_migration())

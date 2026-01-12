"""
Migration: Add Production-Safe MongoDB Indexes
Date: January 2026
Purpose: Add missing indexes for high-traffic collections

This migration adds indexes in the BACKGROUND to avoid blocking operations.
Safe to run on production databases with existing data.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, GEOSPHERE
from pymongo.errors import OperationFailure
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("index_migration")


# Index definitions per collection
# Format: (collection_name, index_spec, index_options)
INDEXES_TO_ADD = [
    # ============================================
    # tb_users collection (TBUser model)
    # ============================================
    (
        "tb_users",
        [("email", ASCENDING)],
        {"name": "email_1", "unique": True, "background": True}
    ),
    (
        "tb_users",
        [("mobile_number", ASCENDING)],
        {"name": "mobile_number_1", "unique": True, "background": True}
    ),
    (
        "tb_users",
        [("location", GEOSPHERE)],
        {"name": "location_2dsphere", "background": True}
    ),
    (
        "tb_users",
        [("is_active", ASCENDING)],
        {"name": "is_active_1", "background": True}
    ),
    (
        "tb_users",
        [("created_at", DESCENDING)],
        {"name": "created_at_-1", "background": True}
    ),
    (
        "tb_users",
        [("gender", ASCENDING), ("age", ASCENDING)],
        {"name": "gender_1_age_1", "background": True}
    ),
    (
        "tb_users",
        [("is_online", ASCENDING), ("location_updated_at", DESCENDING)],
        {"name": "is_online_1_location_updated_at_-1", "background": True}
    ),
    
    # ============================================
    # users collection (legacy User model)
    # ============================================
    (
        "users",
        [("email", ASCENDING)],
        {"name": "email_1", "unique": True, "background": True}
    ),
    (
        "users",
        [("role", ASCENDING)],
        {"name": "role_1", "background": True}
    ),
    (
        "users",
        [("is_suspended", ASCENDING)],
        {"name": "is_suspended_1", "background": True}
    ),
    (
        "users",
        [("created_at", DESCENDING)],
        {"name": "created_at_-1", "background": True}
    ),
    
    # ============================================
    # messages_v2 collection (MessageV2 model)
    # ============================================
    (
        "messages_v2",
        [("sender_id", ASCENDING), ("receiver_id", ASCENDING), ("created_at", DESCENDING)],
        {"name": "conversation_idx", "background": True}
    ),
    (
        "messages_v2",
        [("receiver_id", ASCENDING), ("status", ASCENDING)],
        {"name": "unread_messages_idx", "background": True}
    ),
    (
        "messages_v2",
        [("created_at", DESCENDING)],
        {"name": "created_at_-1", "background": True}
    ),
    (
        "messages_v2",
        [("moderation_status", ASCENDING), ("created_at", DESCENDING)],
        {"name": "moderation_queue_idx", "background": True}
    ),
    
    # ============================================
    # tb_messages collection (TBMessage model)
    # ============================================
    (
        "tb_messages",
        [("sender_id", ASCENDING), ("receiver_id", ASCENDING), ("created_at", DESCENDING)],
        {"name": "conversation_idx", "background": True}
    ),
    (
        "tb_messages",
        [("receiver_id", ASCENDING), ("is_read", ASCENDING)],
        {"name": "unread_messages_idx", "background": True}
    ),
    (
        "tb_messages",
        [("created_at", DESCENDING)],
        {"name": "created_at_-1", "background": True}
    ),
    
    # ============================================
    # tb_conversations collection
    # ============================================
    (
        "tb_conversations",
        [("participants", ASCENDING)],
        {"name": "participants_1", "background": True}
    ),
    (
        "tb_conversations",
        [("last_message_at", DESCENDING)],
        {"name": "last_message_at_-1", "background": True}
    ),
    
    # ============================================
    # credits_transactions collection
    # ============================================
    (
        "credits_transactions",
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
        {"name": "user_history_idx", "background": True}
    ),
    (
        "credits_transactions",
        [("idempotency_key", ASCENDING)],
        {"name": "idempotency_key_1", "unique": True, "sparse": True, "background": True}
    ),
    (
        "credits_transactions",
        [("payment_id", ASCENDING)],
        {"name": "payment_id_1", "sparse": True, "background": True}
    ),
    (
        "credits_transactions",
        [("status", ASCENDING), ("created_at", DESCENDING)],
        {"name": "status_created_idx", "background": True}
    ),
    (
        "credits_transactions",
        [("transaction_type", ASCENDING), ("created_at", DESCENDING)],
        {"name": "type_created_idx", "background": True}
    ),
    
    # ============================================
    # tb_credit_transactions collection
    # ============================================
    (
        "tb_credit_transactions",
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
        {"name": "user_history_idx", "background": True}
    ),
    (
        "tb_credit_transactions",
        [("reason", ASCENDING), ("created_at", DESCENDING)],
        {"name": "reason_created_idx", "background": True}
    ),
    (
        "tb_credit_transactions",
        [("reference_id", ASCENDING)],
        {"name": "reference_id_1", "sparse": True, "background": True}
    ),
    
    # ============================================
    # payment_intents collection
    # ============================================
    (
        "payment_intents",
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
        {"name": "user_payments_idx", "background": True}
    ),
    (
        "payment_intents",
        [("idempotency_key", ASCENDING)],
        {"name": "idempotency_key_1", "unique": True, "background": True}
    ),
    (
        "payment_intents",
        [("provider_intent_id", ASCENDING)],
        {"name": "provider_intent_id_1", "sparse": True, "background": True}
    ),
    (
        "payment_intents",
        [("status", ASCENDING), ("created_at", DESCENDING)],
        {"name": "status_created_idx", "background": True}
    ),
    (
        "payment_intents",
        [("provider", ASCENDING), ("status", ASCENDING)],
        {"name": "provider_status_idx", "background": True}
    ),
    (
        "payment_intents",
        [("credits_added", ASCENDING), ("status", ASCENDING)],
        {"name": "fulfillment_idx", "background": True}
    ),
    
    # ============================================
    # tb_payments collection
    # ============================================
    (
        "tb_payments",
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
        {"name": "user_payments_idx", "background": True}
    ),
    (
        "tb_payments",
        [("provider_order_id", ASCENDING)],
        {"name": "provider_order_id_1", "unique": True, "background": True}
    ),
    (
        "tb_payments",
        [("provider_payment_id", ASCENDING)],
        {"name": "provider_payment_id_1", "sparse": True, "background": True}
    ),
    (
        "tb_payments",
        [("status", ASCENDING), ("created_at", DESCENDING)],
        {"name": "status_created_idx", "background": True}
    ),
    
    # ============================================
    # presence_v2 collection
    # ============================================
    (
        "presence_v2",
        [("user_id", ASCENDING)],
        {"name": "user_id_1", "unique": True, "background": True}
    ),
    (
        "presence_v2",
        [("status", ASCENDING), ("last_activity", DESCENDING)],
        {"name": "status_activity_idx", "background": True}
    ),
    (
        "presence_v2",
        [("last_seen", DESCENDING)],
        {"name": "last_seen_-1", "background": True}
    ),
    
    # ============================================
    # presence collection (legacy)
    # ============================================
    (
        "presence",
        [("user_id", ASCENDING)],
        {"name": "user_id_1", "unique": True, "background": True}
    ),
    (
        "presence",
        [("status", ASCENDING), ("last_seen", DESCENDING)],
        {"name": "status_last_seen_idx", "background": True}
    ),
    
    # ============================================
    # sessions collection
    # ============================================
    (
        "sessions",
        [("user_id", ASCENDING), ("revoked", ASCENDING)],
        {"name": "user_active_sessions_idx", "background": True}
    ),
    (
        "sessions",
        [("refresh_token_id", ASCENDING)],
        {"name": "refresh_token_id_1", "background": True}
    ),
    (
        "sessions",
        [("last_active_at", DESCENDING)],
        {"name": "last_active_at_-1", "background": True}
    ),
    
    # ============================================
    # audit_logs collection
    # ============================================
    (
        "audit_logs",
        [("actor_user_id", ASCENDING), ("created_at", DESCENDING)],
        {"name": "user_audit_idx", "background": True}
    ),
    (
        "audit_logs",
        [("action", ASCENDING), ("created_at", DESCENDING)],
        {"name": "action_created_idx", "background": True}
    ),
    (
        "audit_logs",
        [("severity", ASCENDING), ("created_at", DESCENDING)],
        {"name": "severity_created_idx", "background": True}
    ),
    
    # ============================================
    # notifications collection
    # ============================================
    (
        "notifications",
        [("user_id", ASCENDING), ("is_read", ASCENDING), ("created_at", DESCENDING)],
        {"name": "user_unread_idx", "background": True}
    ),
    (
        "notifications",
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
        {"name": "user_notifications_idx", "background": True}
    ),
]


async def get_existing_indexes(collection) -> set:
    """Get set of existing index names for a collection"""
    existing = set()
    try:
        indexes = await collection.index_information()
        for name in indexes.keys():
            existing.add(name)
    except Exception as e:
        logger.warning(f"Could not get indexes for collection: {e}")
    return existing


async def create_index_safe(db, collection_name: str, index_spec: list, options: dict) -> dict:
    """
    Create an index safely - skip if already exists, handle errors gracefully.
    
    Returns:
        dict with status: 'created', 'skipped', or 'error'
    """
    collection = db[collection_name]
    index_name = options.get("name", "unnamed")
    
    result = {
        "collection": collection_name,
        "index_name": index_name,
        "spec": index_spec,
        "status": "unknown"
    }
    
    try:
        # Check if index already exists
        existing = await get_existing_indexes(collection)
        
        if index_name in existing:
            result["status"] = "skipped"
            result["reason"] = "Index already exists"
            logger.info(f"SKIPPED: {collection_name}.{index_name} - already exists")
            return result
        
        # Create the index
        await collection.create_index(index_spec, **options)
        result["status"] = "created"
        logger.info(f"CREATED: {collection_name}.{index_name}")
        return result
        
    except OperationFailure as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            result["status"] = "skipped"
            result["reason"] = "Index already exists (different spec)"
            logger.info(f"SKIPPED: {collection_name}.{index_name} - similar index exists")
        else:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"ERROR: {collection_name}.{index_name} - {e}")
        return result
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"ERROR: {collection_name}.{index_name} - {e}")
        return result


async def run_migration():
    """Run the index migration"""
    
    # Get MongoDB connection
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/truebond")
    
    logger.info("=" * 60)
    logger.info("MongoDB Index Migration - Production Safe")
    logger.info("=" * 60)
    logger.info(f"Connecting to: {mongo_url.split('@')[-1] if '@' in mongo_url else mongo_url}")
    
    client = AsyncIOMotorClient(mongo_url)
    
    # Extract database name from URL or use default
    if "/" in mongo_url:
        db_name = mongo_url.split("/")[-1].split("?")[0]
    else:
        db_name = "truebond"
    
    db = client[db_name]
    
    logger.info(f"Database: {db_name}")
    logger.info(f"Total indexes to process: {len(INDEXES_TO_ADD)}")
    logger.info("-" * 60)
    
    results = {
        "created": [],
        "skipped": [],
        "errors": []
    }
    
    for collection_name, index_spec, options in INDEXES_TO_ADD:
        result = await create_index_safe(db, collection_name, index_spec, options)
        
        if result["status"] == "created":
            results["created"].append(result)
        elif result["status"] == "skipped":
            results["skipped"].append(result)
        else:
            results["errors"].append(result)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Created: {len(results['created'])} indexes")
    logger.info(f"⏭️  Skipped: {len(results['skipped'])} indexes (already exist)")
    logger.info(f"❌ Errors:  {len(results['errors'])} indexes")
    
    if results["created"]:
        logger.info("\nNewly created indexes:")
        for r in results["created"]:
            logger.info(f"  + {r['collection']}.{r['index_name']}")
    
    if results["skipped"]:
        logger.info("\nSkipped indexes (already exist):")
        for r in results["skipped"]:
            logger.info(f"  - {r['collection']}.{r['index_name']}")
    
    if results["errors"]:
        logger.info("\nFailed indexes:")
        for r in results["errors"]:
            logger.info(f"  ! {r['collection']}.{r['index_name']}: {r.get('error', 'Unknown error')}")
    
    client.close()
    
    return results


async def verify_indexes():
    """Verify all indexes are in place"""
    
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/truebond")
    client = AsyncIOMotorClient(mongo_url)
    
    if "/" in mongo_url:
        db_name = mongo_url.split("/")[-1].split("?")[0]
    else:
        db_name = "truebond"
    
    db = client[db_name]
    
    logger.info("=" * 60)
    logger.info("INDEX VERIFICATION REPORT")
    logger.info("=" * 60)
    
    collections_checked = set()
    
    for collection_name, _, _ in INDEXES_TO_ADD:
        if collection_name in collections_checked:
            continue
        collections_checked.add(collection_name)
        
        collection = db[collection_name]
        try:
            indexes = await collection.index_information()
            logger.info(f"\n{collection_name}:")
            for name, info in indexes.items():
                key_spec = info.get("key", [])
                unique = "UNIQUE" if info.get("unique") else ""
                sparse = "SPARSE" if info.get("sparse") else ""
                flags = " ".join(filter(None, [unique, sparse]))
                logger.info(f"  - {name}: {key_spec} {flags}")
        except Exception as e:
            logger.warning(f"\n{collection_name}: Could not retrieve indexes - {e}")
    
    client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        asyncio.run(verify_indexes())
    else:
        asyncio.run(run_migration())

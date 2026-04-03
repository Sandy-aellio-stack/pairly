"""Simple infra check script for local development.

Checks:
- Redis connectivity using REDIS_URL
- SendGrid client import and env var

Run: python backend/scripts/check_infra.py
"""
import os
import asyncio
import sys

REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379')


async def check_redis():
    try:
        import redis.asyncio as aioredis
    except Exception as e:
        print(f"redis.asyncio import failed: {e}")
        return False

    try:
        r = aioredis.from_url(REDIS_URL, encoding='utf-8', decode_responses=True)
        await r.ping()
        await r.close()
        print(f"✅ Redis reachable at {REDIS_URL}")
        return True
    except Exception as e:
        print(f"❌ Redis not reachable ({REDIS_URL}): {e}")
        return False


def check_sendgrid():
    key = os.getenv('SENDGRID_API_KEY')
    try:
        from sendgrid import SendGridAPIClient
        print("✅ sendgrid package import OK")
    except Exception as e:
        print(f"❌ sendgrid import failed: {e}")
        return False

    if not key:
        print("❌ SENDGRID_API_KEY not set in environment")
        return False

    print("✅ SENDGRID_API_KEY present (not validated)")
    return True


async def main():
    print("Checking infrastructure...\n")
    r = await check_redis()
    s = check_sendgrid()
    ok = r and s
    if ok:
        print("\nAll checks passed (Redis + SendGrid import + env). You can start the backend.")
        sys.exit(0)
    else:
        print("\nOne or more checks failed. See messages above.")
        sys.exit(2)


if __name__ == '__main__':
    asyncio.run(main())

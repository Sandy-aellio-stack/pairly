"""
Moderation Service
==================
Single source of truth for all block/report enforcement.

Used by:
- Messaging (send_message, get_conversations)
- Discovery (nearby, search, feed)
- Calling (initiate_call)

NEVER duplicate block logic in individual routes or services.
Always import and call functions from here.
"""
from __future__ import annotations

import logging
from typing import Set

from beanie import PydanticObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

logger = logging.getLogger("moderation_service")


# ---------------------------------------------------------------------------
# Block enforcement
# ---------------------------------------------------------------------------

async def is_blocked(user_id_a: str, user_id_b: str) -> bool:
    """
    Return True if *either* user has blocked the other.

    Accepts string IDs; converts internally to ObjectId.
    Never raises – returns False on any conversion error so
    legitimate traffic is never blocked by bad data.
    """
    from backend.models.user_block import UserBlock

    try:
        oid_a = PydanticObjectId(user_id_a)
        oid_b = PydanticObjectId(user_id_b)
    except (InvalidId, Exception):
        logger.warning(
            "is_blocked: invalid ObjectId(s) (%s, %s) – skipping block check",
            user_id_a,
            user_id_b,
        )
        return False

    block = await UserBlock.find_one(
        {
            "$or": [
                {"blocker_id": oid_a, "blocked_id": oid_b},
                {"blocker_id": oid_b, "blocked_id": oid_a},
            ]
        }
    )
    return block is not None


async def get_blocked_ids(user_id: str) -> Set[str]:
    """
    Return the set of *all* user IDs that are in a block relationship
    with ``user_id`` (both directions: blocked-by-me and blocked-me).

    Returns an empty set on any error.
    """
    from backend.models.user_block import UserBlock

    try:
        user_oid = PydanticObjectId(user_id)
    except (InvalidId, Exception):
        return set()

    try:
        # Users I blocked
        outgoing = await UserBlock.find({"blocker_id": user_oid}).to_list()
        blocked_by_me: Set[str] = {str(b.blocked_id) for b in outgoing}

        # Users who blocked me
        incoming = await UserBlock.find({"blocked_id": user_oid}).to_list()
        blocked_me: Set[str] = {str(b.blocker_id) for b in incoming}

        return blocked_by_me | blocked_me
    except Exception as exc:
        logger.error("get_blocked_ids failed for %s: %s", user_id, exc)
        return set()


async def assert_not_blocked(sender_id: str, receiver_id: str) -> None:
    """
    Raise HTTP 403 if either user has blocked the other.
    Use this as a guard at the start of any action between two users.
    """
    if await is_blocked(sender_id, receiver_id):
        raise HTTPException(
            status_code=403,
            detail="Action not allowed: user is blocked.",
        )


# ---------------------------------------------------------------------------
# Report helpers (thin wrappers — actual storage handled in route)
# ---------------------------------------------------------------------------

async def has_pending_report(reporter_id: str, reported_id: str) -> bool:
    """Return True if reporter already has a pending report against reported."""
    from backend.models.tb_report import TBReport, ReportStatus

    try:
        r_oid = PydanticObjectId(reporter_id)
        d_oid = PydanticObjectId(reported_id)
    except (InvalidId, Exception):
        return False

    existing = await TBReport.find_one(
        {
            "reported_by_user_id": r_oid,
            "reported_user_id": d_oid,
            "status": ReportStatus.PENDING,
        }
    )
    return existing is not None

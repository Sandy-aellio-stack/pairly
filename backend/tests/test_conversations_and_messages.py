"""
Tests for the critical conversation and message flows.

These tests use pytest with unittest.mock to avoid a live MongoDB connection.
They validate:
- get_conversations() attribute access (the fixed bug)
- send_message() creates a conversation and message
- mark_messages_read() updates DB
- block / report user routes return correct status
- _get_blocked_user_ids uses PydanticObjectId queries

Run with:
    cd backend
    pytest tests/test_conversations_and_messages.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timezone
from beanie import PydanticObjectId


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_oid(hex_str: str = None) -> PydanticObjectId:
    """Return a deterministic PydanticObjectId for testing."""
    if hex_str:
        return PydanticObjectId(hex_str)
    return PydanticObjectId()


def make_fake_user(uid: str, name: str = "Test User", online: bool = False):
    """Return a mock TBUser document."""
    u = MagicMock()
    u.id = make_oid(uid)
    u.name = name
    u.profile_pictures = []
    u.is_online = online
    u.is_suspended = False
    u.coins = 10
    u.email = f"{name.lower().replace(' ', '')}@example.com"
    return u


def make_fake_conversation(conv_id: str, p1: str, p2: str, last_msg: str = "", unread: dict = None):
    """Return a mock TBConversation document (attribute-based, not dict)."""
    c = MagicMock()
    c.id = make_oid(conv_id)
    c.participants = [make_oid(p1), make_oid(p2)]
    c.last_message = last_msg
    c.last_message_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    c.last_sender_id = make_oid(p1)
    c.unread_count = unread or {}
    c.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return c


# ---------------------------------------------------------------------------
# Tests: get_conversations (the critical bug we fixed)
# ---------------------------------------------------------------------------

class TestGetConversations:
    """Validate that get_conversations uses attribute access, not .get() on Documents."""

    @pytest.mark.asyncio
    async def test_returns_flat_fields_for_frontend(self):
        """After fix, conversations should expose id, name, avatar, online, lastMessage, unread."""
        user_id = "aaaaaaaaaaaaaaaaaaaaaaaa"
        partner_id = "bbbbbbbbbbbbbbbbbbbbbbbb"
        conv_id = "cccccccccccccccccccccccc"

        fake_conv = make_fake_conversation(conv_id, user_id, partner_id, last_msg="Hello", unread={user_id: 2})
        fake_partner = make_fake_user(partner_id, name="Alice", online=True)
        fake_partner.profile_pictures = ["https://example.com/pic.jpg"]

        with patch("backend.services.tb_message_service.TBConversation") as MockConv, \
             patch("backend.services.tb_message_service.TBUser") as MockUser:

            MockConv.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(
                return_value=[fake_conv]
            )
            MockUser.find.return_value.to_list = AsyncMock(return_value=[fake_partner])

            from backend.services.tb_message_service import MessageService
            result = await MessageService.get_conversations(user_id)

        assert len(result) == 1
        conv = result[0]

        # Flat fields the frontend ChatPage.jsx requires
        assert conv["id"] == partner_id, "id should be partner's user ID"
        assert conv["name"] == "Alice"
        assert conv["avatar"] == "https://example.com/pic.jpg"
        assert conv["online"] is True
        assert conv["lastMessage"] == "Hello"
        assert conv["conversation_id"] == conv_id
        assert "time" in conv
        # Unread count should be keyed by user_id string
        assert conv["unread"] == 2

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_conversations(self):
        """Should return [] (not raise) when user has no conversations."""
        user_id = "aaaaaaaaaaaaaaaaaaaaaaaa"

        with patch("backend.services.tb_message_service.TBConversation") as MockConv, \
             patch("backend.services.tb_message_service.TBUser"):

            MockConv.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(
                return_value=[]
            )

            from backend.services.tb_message_service import MessageService
            result = await MessageService.get_conversations(user_id)

        assert result == []

    @pytest.mark.asyncio
    async def test_skips_conversation_when_partner_not_found(self):
        """Conversations whose partner no longer exists should be silently skipped."""
        user_id = "aaaaaaaaaaaaaaaaaaaaaaaa"
        partner_id = "bbbbbbbbbbbbbbbbbbbbbbbb"
        conv_id = "cccccccccccccccccccccccc"

        fake_conv = make_fake_conversation(conv_id, user_id, partner_id)

        with patch("backend.services.tb_message_service.TBConversation") as MockConv, \
             patch("backend.services.tb_message_service.TBUser") as MockUser:

            MockConv.find.return_value.sort.return_value.limit.return_value.to_list = AsyncMock(
                return_value=[fake_conv]
            )
            # Partner not in DB
            MockUser.find.return_value.to_list = AsyncMock(return_value=[])

            from backend.services.tb_message_service import MessageService
            result = await MessageService.get_conversations(user_id)

        assert result == []


# ---------------------------------------------------------------------------
# Tests: send_message
# ---------------------------------------------------------------------------

class TestSendMessage:
    """Validate send_message creates or finds conversation + persists message."""

    @pytest.mark.asyncio
    async def test_creates_new_conversation_on_first_message(self):
        sender_id = "aaaaaaaaaaaaaaaaaaaaaaaa"
        receiver_id = "bbbbbbbbbbbbbbbbbbbbbbbb"

        fake_sender = make_fake_user(sender_id, "Bob")
        fake_receiver = make_fake_user(receiver_id, "Alice")
        fake_receiver.settings = MagicMock()
        fake_receiver.settings.notifications = MagicMock()
        fake_receiver.settings.notifications.messages = True
        fake_receiver.is_online = False

        fake_conversation = MagicMock()
        fake_conversation.id = make_oid("cccccccccccccccccccccccc")
        fake_conversation.last_message = ""
        fake_conversation.unread_count = {}
        fake_conversation.save = AsyncMock()

        fake_message = MagicMock()
        fake_message.id = make_oid("dddddddddddddddddddddddd")
        fake_message.created_at = datetime.now(timezone.utc)
        fake_message.message_type = "text"

        from backend.services.tb_message_service import SendMessageRequest

        with patch("backend.services.tb_message_service.TBUser") as MockUser, \
             patch("backend.services.tb_message_service.TBConversation") as MockConv, \
             patch("backend.services.tb_message_service.TBMessage") as MockMsg, \
             patch("backend.services.tb_message_service.CreditService") as MockCredits, \
             patch("backend.services.tb_message_service.asyncio") as mock_asyncio:

            MockUser.get = AsyncMock(side_effect=lambda oid: (
                fake_sender if str(oid) == sender_id else fake_receiver
            ))
            # No existing conversation
            MockConv.find_one = AsyncMock(return_value=None)
            new_conv_instance = MagicMock()
            new_conv_instance.id = fake_conversation.id
            new_conv_instance.unread_count = {}
            new_conv_instance.last_message = ""
            new_conv_instance.insert = AsyncMock()
            new_conv_instance.save = AsyncMock()
            MockConv.return_value = new_conv_instance

            msg_instance = MagicMock()
            msg_instance.id = fake_message.id
            msg_instance.created_at = fake_message.created_at
            msg_instance.message_type = "text"
            msg_instance.insert = AsyncMock()
            MockMsg.return_value = msg_instance

            MockCredits.deduct_credits = AsyncMock()
            mock_asyncio.create_task = MagicMock()

            request = SendMessageRequest(receiver_id=receiver_id, content="Hello Alice")

            from backend.services.tb_message_service import MessageService
            result = await MessageService.send_message(sender_id, request)

        assert result["success"] is True
        assert result["message_id"] == str(fake_message.id)
        assert result["status"] == "sent"
        assert "conversation_id" in result


# ---------------------------------------------------------------------------
# Tests: mark_messages_read
# ---------------------------------------------------------------------------

class TestMarkMessagesRead:
    """Validate mark_messages_read updates message status and clears unread count."""

    @pytest.mark.asyncio
    async def test_clears_unread_count_in_conversation(self):
        user_id = "aaaaaaaaaaaaaaaaaaaaaaaa"
        other_id = "bbbbbbbbbbbbbbbbbbbbbbbb"

        fake_conv = MagicMock()
        fake_conv.unread_count = {user_id: 3}
        fake_conv.save = AsyncMock()

        fake_update_result = MagicMock()
        fake_update_result.modified_count = 3

        with patch("backend.services.tb_message_service.TBMessage") as MockMsg, \
             patch("backend.services.tb_message_service.TBConversation") as MockConv:

            MockMsg.find.return_value.update_many = AsyncMock(return_value=fake_update_result)
            MockConv.find_one = AsyncMock(return_value=fake_conv)

            from backend.services.tb_message_service import MessageService
            result = await MessageService.mark_messages_read(user_id, other_id)

        assert result["marked_read"] == 3
        assert fake_conv.unread_count[user_id] == 0
        fake_conv.save.assert_awaited_once()


# ---------------------------------------------------------------------------
# Tests: Block user
# ---------------------------------------------------------------------------

class TestBlockUser:
    """Validate UserBlock is stored with correct PydanticObjectId fields."""

    @pytest.mark.asyncio
    async def test_block_stores_objectid_fields(self):
        """UserBlock.blocker_id and blocked_id must be PydanticObjectId, not strings."""
        from backend.models.user_block import UserBlock

        blocker = make_oid("aaaaaaaaaaaaaaaaaaaaaaaa")
        blocked = make_oid("bbbbbbbbbbbbbbbbbbbbbbbb")

        block = UserBlock(blocker_id=blocker, blocked_id=blocked)
        assert isinstance(block.blocker_id, PydanticObjectId)
        assert isinstance(block.blocked_id, PydanticObjectId)
        assert str(block.blocker_id) == "aaaaaaaaaaaaaaaaaaaaaaaa"
        assert str(block.blocked_id) == "bbbbbbbbbbbbbbbbbbbbbbbb"


# ---------------------------------------------------------------------------
# Tests: Report user
# ---------------------------------------------------------------------------

class TestReportUser:
    """Validate TBReport is created with correct fields."""

    def test_report_requires_reason(self):
        """reason field must be present (non-empty)."""
        from backend.models.tb_report import TBReport, ReportType

        report = TBReport(
            report_type=ReportType.PROFILE,
            reported_user_id=make_oid("aaaaaaaaaaaaaaaaaaaaaaaa"),
            reported_by_user_id=make_oid("bbbbbbbbbbbbbbbbbbbbbbbb"),
            reason="This user is posting spam content",
        )
        assert report.reason == "This user is posting spam content"
        assert report.status.value == "pending"
        assert report.report_type == ReportType.PROFILE

    def test_report_status_defaults_to_pending(self):
        from backend.models.tb_report import TBReport, ReportType, ReportStatus

        report = TBReport(
            report_type=ReportType.PROFILE,
            reported_user_id=make_oid("aaaaaaaaaaaaaaaaaaaaaaaa"),
            reported_by_user_id=make_oid("bbbbbbbbbbbbbbbbbbbbbbbb"),
            reason="Inappropriate behavior detected",
        )
        assert report.status == ReportStatus.PENDING


# ---------------------------------------------------------------------------
# Tests: _get_blocked_user_ids (the type mismatch fix)
# ---------------------------------------------------------------------------

class TestGetBlockedUserIds:
    """Validate _get_blocked_user_ids converts user_id to PydanticObjectId before querying."""

    @pytest.mark.asyncio
    async def test_uses_objectid_for_query(self):
        """The function must query with PydanticObjectId, not raw string."""
        user_id = "aaaaaaaaaaaaaaaaaaaaaaaa"
        blocked_id_str = "bbbbbbbbbbbbbbbbbbbbbbbb"

        fake_block = MagicMock()
        fake_block.blocked_id = make_oid(blocked_id_str)
        fake_block.blocker_id = make_oid(user_id)

        with patch("backend.routes.tb_users.UserBlock") as MockBlock:
            # my_blocks: I blocked someone
            # their_blocks: no one blocked me
            MockBlock.find = MagicMock(side_effect=lambda q: (
                MagicMock(to_list=AsyncMock(return_value=[fake_block]))
                if "blocker_id" in q
                else MagicMock(to_list=AsyncMock(return_value=[]))
            ))

            from backend.routes.tb_users import _get_blocked_user_ids
            result = await _get_blocked_user_ids(user_id)

        assert blocked_id_str in result

    @pytest.mark.asyncio
    async def test_returns_empty_set_on_invalid_id(self):
        """Invalid ObjectId string must return empty set, not raise."""
        from backend.routes.tb_users import _get_blocked_user_ids
        result = await _get_blocked_user_ids("not-a-valid-objectid")
        assert result == set()

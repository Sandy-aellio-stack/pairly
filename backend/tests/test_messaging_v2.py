"""
Comprehensive tests for Phase 9: Messaging V2
Tests: send message, delivery receipts, read receipts, unread counter, conversation listing, admin operations
"""
import pytest
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.models.user import User
from backend.models.message_v2 import MessageV2, MessageType, MessageStatus, ModerationStatus
from backend.models.credits_transaction import CreditsTransaction
from backend.services.messaging_v2 import MessagingServiceV2
from backend.config import settings

@pytest.fixture
async def db():
    """Initialize test database"""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    database = client.get_database("pairly_test")
    
    await init_beanie(
        database=database,
        document_models=[User, MessageV2, CreditsTransaction]
    )
    
    yield database
    
    # Cleanup
    await database.client.drop_database("pairly_test")

@pytest.fixture
async def test_users(db):
    """Create test users"""
    user1 = User(
        email="sender@test.com",
        password_hash="hashed_password",
        role="user",
        is_active=True,
        credits=100
    )
    await user1.insert()
    
    user2 = User(
        email="receiver@test.com",
        password_hash="hashed_password",
        role="user",
        is_active=True,
        credits=100
    )
    await user2.insert()
    
    return {"sender": user1, "receiver": user2}

@pytest.fixture
def service():
    """Create messaging service instance"""
    return MessagingServiceV2()

@pytest.mark.asyncio
async def test_send_message_success(db, test_users, service):
    """Test: Send a message successfully with credit deduction"""
    sender = test_users["sender"]
    receiver = test_users["receiver"]
    
    initial_credits = sender.credits
    
    # Send message
    message = await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Hello, this is a test message",
        message_type=MessageType.TEXT
    )
    
    # Verify message was created
    assert message is not None
    assert message.sender_id == str(sender.id)
    assert message.receiver_id == str(receiver.id)
    assert message.content == "Hello, this is a test message"
    assert message.status == MessageStatus.SENT
    assert message.moderation_status == ModerationStatus.APPROVED
    assert message.credits_cost == 1
    
    # Verify message in database
    db_message = await MessageV2.find_one(MessageV2.id == message.id)
    assert db_message is not None
    
    # Verify credits were deducted
    updated_sender = await User.get(sender.id)
    assert updated_sender.credits == initial_credits - 1
    
    print("✅ Test passed: Send message with credit deduction")

@pytest.mark.asyncio
async def test_send_message_insufficient_credits(db, test_users, service):
    """Test: Cannot send message with insufficient credits"""
    sender = test_users["sender"]
    receiver = test_users["receiver"]
    
    # Set credits to 0
    sender.credits = 0
    await sender.save()
    
    # Attempt to send message
    with pytest.raises(ValueError, match="Insufficient credits"):
        await service.send_message(
            sender_id=str(sender.id),
            receiver_id=str(receiver.id),
            content="This should fail",
            message_type=MessageType.TEXT
        )
    
    # Verify no message was created
    messages = await MessageV2.find(MessageV2.sender_id == str(sender.id)).to_list()
    assert len(messages) == 0
    
    print("✅ Test passed: Insufficient credits handling")

@pytest.mark.asyncio
async def test_mark_delivered(db, test_users, service):
    """Test: Mark message as delivered"""
    sender = test_users["sender"]
    receiver = test_users["receiver"]
    
    # Send message
    message = await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Test message for delivery",
        message_type=MessageType.TEXT
    )
    
    assert message.status == MessageStatus.SENT
    assert message.delivered_at is None
    
    # Mark as delivered
    success = await service.mark_delivered(message.id, str(receiver.id))
    assert success is True
    
    # Verify status updated
    updated_message = await MessageV2.find_one(MessageV2.id == message.id)
    assert updated_message.status == MessageStatus.DELIVERED
    assert updated_message.delivered_at is not None
    
    print("✅ Test passed: Mark message as delivered")

@pytest.mark.asyncio
async def test_mark_read(db, test_users, service):
    """Test: Mark message as read"""
    sender = test_users["sender"]
    receiver = test_users["receiver"]
    
    # Send message
    message = await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Test message for read receipt",
        message_type=MessageType.TEXT
    )
    
    # Mark as delivered first
    await service.mark_delivered(message.id, str(receiver.id))
    
    # Mark as read
    success = await service.mark_read(message.id, str(receiver.id))
    assert success is True
    
    # Verify status updated
    updated_message = await MessageV2.find_one(MessageV2.id == message.id)
    assert updated_message.status == MessageStatus.READ
    assert updated_message.read_at is not None
    
    print("✅ Test passed: Mark message as read")

@pytest.mark.asyncio
async def test_unread_count(db, test_users, service):
    """Test: Get unread message count"""
    sender = test_users["sender"]
    receiver = test_users["receiver"]
    
    # Send 3 messages
    msg1 = await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Message 1",
        message_type=MessageType.TEXT
    )
    
    msg2 = await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Message 2",
        message_type=MessageType.TEXT
    )
    
    msg3 = await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Message 3",
        message_type=MessageType.TEXT
    )
    
    # Check unread count
    unread = await service.get_unread_count(str(receiver.id))
    assert unread == 3
    
    # Mark one as read
    await service.mark_read(msg1.id, str(receiver.id))
    
    # Check unread count again
    unread = await service.get_unread_count(str(receiver.id))
    assert unread == 2
    
    # Check unread from specific sender
    unread_from_sender = await service.get_unread_count(str(receiver.id), str(sender.id))
    assert unread_from_sender == 2
    
    print("✅ Test passed: Unread message count")

@pytest.mark.asyncio
async def test_fetch_conversation(db, test_users, service):
    """Test: Fetch conversation between two users"""
    sender = test_users["sender"]
    receiver = test_users["receiver"]
    
    # Send messages back and forth
    await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Hello from sender",
        message_type=MessageType.TEXT
    )
    
    await service.send_message(
        sender_id=str(receiver.id),
        receiver_id=str(sender.id),
        content="Hello from receiver",
        message_type=MessageType.TEXT
    )
    
    await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="How are you?",
        message_type=MessageType.TEXT
    )
    
    # Fetch conversation
    messages = await service.fetch_conversation(
        user1_id=str(sender.id),
        user2_id=str(receiver.id),
        limit=50
    )
    
    assert len(messages) == 3
    # Should be in chronological order
    assert messages[0].content == "Hello from sender"
    assert messages[1].content == "Hello from receiver"
    assert messages[2].content == "How are you?"
    
    print("✅ Test passed: Fetch conversation")

@pytest.mark.asyncio
async def test_list_conversations(db, test_users, service):
    """Test: List all conversations for a user"""
    sender = test_users["sender"]
    receiver = test_users["receiver"]
    
    # Create another user
    user3 = User(
        email="user3@test.com",
        password_hash="hashed_password",
        role="user",
        is_active=True,
        credits=100
    )
    await user3.insert()
    
    # Send messages to two different users
    await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Message to receiver",
        message_type=MessageType.TEXT
    )
    
    await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(user3.id),
        content="Message to user3",
        message_type=MessageType.TEXT
    )
    
    await service.send_message(
        sender_id=str(receiver.id),
        receiver_id=str(sender.id),
        content="Reply from receiver",
        message_type=MessageType.TEXT
    )
    
    # List conversations for sender
    conversations = await service.list_conversations(str(sender.id))
    
    assert len(conversations) == 2
    
    # Check conversation structure
    conv = conversations[0]
    assert "partner_id" in conv
    assert "last_message" in conv
    assert "unread_count" in conv
    assert "total_messages" in conv
    
    print("✅ Test passed: List conversations")

@pytest.mark.asyncio
async def test_mark_multiple_as_read(db, test_users, service):
    """Test: Mark multiple messages as read (bulk operation)"""
    sender = test_users["sender"]
    receiver = test_users["receiver"]
    
    # Send 3 messages
    msg1 = await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Message 1",
        message_type=MessageType.TEXT
    )
    
    msg2 = await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Message 2",
        message_type=MessageType.TEXT
    )
    
    msg3 = await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Message 3",
        message_type=MessageType.TEXT
    )
    
    # Mark all as read
    count = await service.mark_multiple_as_read(
        [msg1.id, msg2.id, msg3.id],
        str(receiver.id)
    )
    
    assert count == 3
    
    # Verify all are read
    updated_msg1 = await MessageV2.find_one(MessageV2.id == msg1.id)
    updated_msg2 = await MessageV2.find_one(MessageV2.id == msg2.id)
    updated_msg3 = await MessageV2.find_one(MessageV2.id == msg3.id)
    
    assert updated_msg1.status == MessageStatus.READ
    assert updated_msg2.status == MessageStatus.READ
    assert updated_msg3.status == MessageStatus.READ
    
    print("✅ Test passed: Bulk mark as read")

@pytest.mark.asyncio
async def test_delete_message(db, test_users, service):
    """Test: Soft delete a message"""
    sender = test_users["sender"]
    receiver = test_users["receiver"]
    
    # Send message
    message = await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Message to delete",
        message_type=MessageType.TEXT
    )
    
    assert message.is_deleted is False
    
    # Delete message
    success = await service.delete_message(message.id, str(sender.id))
    assert success is True
    
    # Verify soft delete
    updated_message = await MessageV2.find_one(MessageV2.id == message.id)
    assert updated_message.is_deleted is True
    assert updated_message.deleted_at is not None
    
    print("✅ Test passed: Soft delete message")

@pytest.mark.asyncio
async def test_message_stats(db, test_users, service):
    """Test: Get messaging statistics"""
    sender = test_users["sender"]
    receiver = test_users["receiver"]
    
    # Send 2 messages
    await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Message 1",
        message_type=MessageType.TEXT
    )
    
    await service.send_message(
        sender_id=str(sender.id),
        receiver_id=str(receiver.id),
        content="Message 2",
        message_type=MessageType.TEXT
    )
    
    # Receive 1 message
    await service.send_message(
        sender_id=str(receiver.id),
        receiver_id=str(sender.id),
        content="Reply",
        message_type=MessageType.TEXT
    )
    
    # Get stats for sender
    stats = await service.get_message_stats(str(sender.id))
    
    assert stats["sent"] == 2
    assert stats["received"] == 1
    assert stats["total"] == 3
    assert stats["unread"] == 1
    
    print("✅ Test passed: Message statistics")

if __name__ == "__main__":
    print("Running Phase 9 Messaging V2 Tests")
    print("=" * 50)
    pytest.main([__file__, "-v", "-s"])

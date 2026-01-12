"""
Redis Pub/Sub Service for Real-Time Messaging
Provides production-ready pub/sub for WebSocket events.

Architecture:
- All real-time events are published to Redis channels
- Each server instance subscribes and handles local delivery
- Stateless WebSocket layer - no in-memory message buffering
- Database remains the source of truth

Channels:
- user:{user_id} - User-specific events (messages, notifications)
- typing:{user_id} - Typing indicators for a user
- presence:{user_id} - Online/offline status
"""
import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime, timezone
import redis.asyncio as aioredis

from backend.core.redis_client import redis_client

logger = logging.getLogger("redis_pubsub")


class RedisPubSub:
    """
    Redis Pub/Sub manager for real-time messaging.
    
    Features:
    - Automatic reconnection
    - Message serialization/deserialization
    - Channel-based routing
    - Graceful degradation when Redis unavailable
    """
    
    def __init__(self):
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._subscriber_task: Optional[asyncio.Task] = None
        self._running = False
        self._handlers: Dict[str, Callable] = {}
        self._channel_prefix = "truebond:"
    
    @property
    def is_connected(self) -> bool:
        """Check if pub/sub is connected and running"""
        return self._running and redis_client.is_connected()
    
    async def connect(self):
        """Initialize pub/sub connection"""
        if not redis_client.is_connected():
            logger.warning("Redis not connected - pub/sub disabled")
            return False
        
        try:
            self._pubsub = redis_client.redis.pubsub()
            self._running = True
            logger.info("Redis Pub/Sub initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize pub/sub: {e}")
            return False
    
    async def disconnect(self):
        """Close pub/sub connection"""
        self._running = False
        
        if self._subscriber_task:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass
            self._subscriber_task = None
        
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
            self._pubsub = None
        
        logger.info("Redis Pub/Sub disconnected")
    
    def _get_channel(self, channel_type: str, identifier: str) -> str:
        """Get full channel name with prefix"""
        return f"{self._channel_prefix}{channel_type}:{identifier}"
    
    async def subscribe_user(self, user_id: str, handler: Callable):
        """
        Subscribe to all channels for a user.
        
        Channels:
        - user:{user_id} - Messages and notifications
        - typing:{user_id} - Typing indicators
        - presence:{user_id} - Presence updates
        """
        if not self._pubsub:
            return False
        
        channels = [
            self._get_channel("user", user_id),
            self._get_channel("typing", user_id),
            self._get_channel("presence", user_id),
        ]
        
        try:
            for channel in channels:
                self._handlers[channel] = handler
            
            await self._pubsub.subscribe(*channels)
            logger.debug(f"Subscribed to channels for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe for user {user_id}: {e}")
            return False
    
    async def unsubscribe_user(self, user_id: str):
        """Unsubscribe from all user channels"""
        if not self._pubsub:
            return
        
        channels = [
            self._get_channel("user", user_id),
            self._get_channel("typing", user_id),
            self._get_channel("presence", user_id),
        ]
        
        try:
            for channel in channels:
                self._handlers.pop(channel, None)
            
            await self._pubsub.unsubscribe(*channels)
            logger.debug(f"Unsubscribed from channels for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe for user {user_id}: {e}")
    
    async def publish(
        self,
        channel_type: str,
        identifier: str,
        event: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Publish an event to a channel.
        
        Args:
            channel_type: Type of channel (user, typing, presence)
            identifier: Channel identifier (usually user_id)
            event: Event name (new_message, typing, etc.)
            data: Event payload
        
        Returns:
            True if published successfully, False otherwise
        """
        if not redis_client.is_connected():
            logger.debug("Redis not connected - publish skipped")
            return False
        
        channel = self._get_channel(channel_type, identifier)
        
        message = {
            "event": event,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await redis_client.redis.publish(channel, json.dumps(message))
            logger.debug(f"Published {event} to {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return False
    
    async def publish_new_message(
        self,
        receiver_id: str,
        message_data: Dict[str, Any]
    ) -> bool:
        """Publish new message event to receiver"""
        return await self.publish(
            channel_type="user",
            identifier=receiver_id,
            event="new_message",
            data=message_data
        )
    
    async def publish_message_notification(
        self,
        receiver_id: str,
        notification_data: Dict[str, Any]
    ) -> bool:
        """Publish message notification to receiver"""
        return await self.publish(
            channel_type="user",
            identifier=receiver_id,
            event="new_message_notification",
            data=notification_data
        )
    
    async def publish_typing(
        self,
        receiver_id: str,
        sender_id: str,
        is_typing: bool
    ) -> bool:
        """Publish typing indicator"""
        event = "user_typing" if is_typing else "user_stopped_typing"
        return await self.publish(
            channel_type="typing",
            identifier=receiver_id,
            event=event,
            data={
                "user_id": sender_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def publish_read_receipt(
        self,
        sender_id: str,
        reader_id: str,
        count: int
    ) -> bool:
        """Publish read receipt to original message sender"""
        return await self.publish(
            channel_type="user",
            identifier=sender_id,
            event="messages_read",
            data={
                "reader_id": reader_id,
                "count": count,
                "read_at": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def publish_message_delivered(
        self,
        sender_id: str,
        message_id: str
    ) -> bool:
        """Publish delivery receipt to message sender"""
        return await self.publish(
            channel_type="user",
            identifier=sender_id,
            event="message_delivered",
            data={
                "message_id": message_id,
                "delivered_at": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def publish_presence(
        self,
        user_id: str,
        is_online: bool
    ) -> bool:
        """Publish user presence change"""
        event = "user_online" if is_online else "user_offline"
        data = {"user_id": user_id}
        
        if not is_online:
            data["last_seen"] = datetime.now(timezone.utc).isoformat()
        
        # Publish to a global presence channel for contacts
        return await self.publish(
            channel_type="presence",
            identifier="global",
            event=event,
            data=data
        )
    
    async def start_subscriber(self, message_handler: Callable):
        """
        Start the subscriber loop.
        
        Args:
            message_handler: Async function to handle incoming messages
                            Signature: async def handler(channel, event, data)
        """
        if not self._pubsub:
            logger.warning("Cannot start subscriber - pub/sub not initialized")
            return
        
        self._subscriber_task = asyncio.create_task(
            self._subscriber_loop(message_handler)
        )
        logger.info("Pub/Sub subscriber started")
    
    async def _subscriber_loop(self, message_handler: Callable):
        """Main subscriber loop"""
        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )
                
                if message is None:
                    continue
                
                if message["type"] == "message":
                    channel = message["channel"]
                    try:
                        payload = json.loads(message["data"])
                        event = payload.get("event")
                        data = payload.get("data", {})
                        
                        await message_handler(channel, event, data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in message: {e}")
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Subscriber loop error: {e}")
                await asyncio.sleep(1)  # Brief pause before retry
        
        logger.info("Subscriber loop ended")


# Global singleton
redis_pubsub = RedisPubSub()

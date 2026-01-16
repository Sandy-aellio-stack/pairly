"""
Firebase Cloud Messaging (FCM) Service for Luveloop
Production-ready, non-blocking push notification system.

Architecture:
- Fire-and-forget: Notifications are sent asynchronously, failures don't block
- Event-driven: Triggered by specific events (message, match, call)
- Idempotent: Each event generates at most one notification
- Socket-aware: Skips push if user is active on WebSocket

Supported Events:
- new_message: When user receives a new message
- new_match: When a new match is created
- incoming_call: When user receives an incoming call

FCM Token Lifecycle:
1. Client requests notification permission
2. Client gets FCM token from Firebase SDK
3. Client sends token to backend via POST /api/users/fcm-token
4. Backend stores token(s) per user (multiple devices supported)
5. On logout/uninstall, client should call DELETE /api/users/fcm-token
6. Backend invalidates tokens that fail delivery
"""
import os
import asyncio
import logging
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger("fcm_service")

# FCM Configuration
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")
FCM_API_URL = "https://fcm.googleapis.com/fcm/send"
FCM_ENABLED = bool(FCM_SERVER_KEY)


class NotificationEvent:
    """Notification event types"""
    NEW_MESSAGE = "new_message"
    NEW_MATCH = "new_match"
    INCOMING_CALL = "incoming_call"


class FCMService:
    """
    Firebase Cloud Messaging Service
    
    Sends push notifications to user devices in a non-blocking manner.
    Respects user settings and socket connection state.
    """
    
    def __init__(self):
        self._sent_notifications: Dict[str, datetime] = {}  # idempotency cache
        self._cache_ttl_seconds = 60  # prevent duplicate notifications within 60s
    
    def _generate_idempotency_key(self, user_id: str, event_type: str, reference_id: str) -> str:
        """Generate unique key for notification deduplication"""
        raw = f"{user_id}:{event_type}:{reference_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    
    def _is_duplicate(self, idempotency_key: str) -> bool:
        """Check if notification was recently sent"""
        if idempotency_key not in self._sent_notifications:
            return False
        
        sent_at = self._sent_notifications[idempotency_key]
        elapsed = (datetime.now(timezone.utc) - sent_at).total_seconds()
        
        if elapsed > self._cache_ttl_seconds:
            del self._sent_notifications[idempotency_key]
            return False
        
        return True
    
    def _mark_sent(self, idempotency_key: str):
        """Mark notification as sent"""
        self._sent_notifications[idempotency_key] = datetime.now(timezone.utc)
        
        # Clean old entries periodically
        if len(self._sent_notifications) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove expired cache entries"""
        now = datetime.now(timezone.utc)
        expired = [
            key for key, sent_at in self._sent_notifications.items()
            if (now - sent_at).total_seconds() > self._cache_ttl_seconds
        ]
        for key in expired:
            del self._sent_notifications[key]
    
    async def _is_user_active_on_socket(self, user_id: str) -> bool:
        """Check if user has active WebSocket connection"""
        try:
            from backend.socket_server import user_sockets
            return user_id in user_sockets and len(user_sockets[user_id]) > 0
        except ImportError:
            return False
    
    async def _get_user_notification_settings(self, user_id: str) -> Dict[str, bool]:
        """Get user's notification preferences"""
        try:
            from backend.models.tb_user import TBUser
            user = await TBUser.get(user_id)
            if user and hasattr(user, 'settings') and user.settings:
                return {
                    "messages": user.settings.notifications.messages,
                    "matches": user.settings.notifications.matches,
                    "calls": True,  # Always allow call notifications for safety
                }
            return {"messages": True, "matches": True, "calls": True}
        except Exception as e:
            logger.warning(f"Failed to get user settings: {e}")
            return {"messages": True, "matches": True, "calls": True}
    
    async def _get_user_fcm_tokens(self, user_id: str) -> List[str]:
        """Get user's FCM device tokens"""
        try:
            from backend.models.tb_user import TBUser
            user = await TBUser.get(user_id)
            if user and hasattr(user, 'fcm_tokens') and user.fcm_tokens:
                return user.fcm_tokens
            return []
        except Exception as e:
            logger.warning(f"Failed to get FCM tokens for user {user_id}: {e}")
            return []
    
    async def _send_fcm_message(self, token: str, title: str, body: str, data: Dict[str, Any]) -> bool:
        """
        Send FCM message to a single device token.
        Returns True if successful, False otherwise.
        
        In test mode (no FCM_SERVER_KEY), logs the notification instead.
        """
        if not FCM_ENABLED:
            logger.info(f"[FCM-TEST] Would send to token {token[:20]}...: {title} - {body}")
            return True
        
        try:
            import aiohttp
            
            payload = {
                "to": token,
                "notification": {
                    "title": title,
                    "body": body,
                    "sound": "default",
                    "badge": 1
                },
                "data": data,
                "priority": "high",
                "content_available": True
            }
            
            headers = {
                "Authorization": f"key={FCM_SERVER_KEY}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(FCM_API_URL, json=payload, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success", 0) > 0:
                            logger.debug(f"FCM sent successfully to token {token[:20]}...")
                            return True
                        else:
                            # Token might be invalid
                            logger.warning(f"FCM delivery failed for token {token[:20]}...: {result}")
                            return False
                    else:
                        logger.error(f"FCM API error: {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.warning("FCM request timed out")
            return False
        except Exception as e:
            logger.error(f"FCM send error: {e}")
            return False
    
    async def _invalidate_token(self, user_id: str, token: str):
        """Remove invalid token from user's device list"""
        try:
            from backend.models.tb_user import TBUser
            user = await TBUser.get(user_id)
            if user and hasattr(user, 'fcm_tokens') and user.fcm_tokens:
                if token in user.fcm_tokens:
                    user.fcm_tokens.remove(token)
                    await user.save()
                    logger.info(f"Invalidated FCM token for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate token: {e}")
    
    async def send_notification(
        self,
        user_id: str,
        event_type: str,
        title: str,
        body: str,
        data: Dict[str, Any],
        reference_id: str,
        skip_socket_check: bool = False
    ) -> bool:
        """
        Send push notification to user (fire-and-forget pattern).
        
        Args:
            user_id: Target user ID
            event_type: Type of notification event (new_message, new_match, incoming_call)
            title: Notification title
            body: Notification body text
            data: Additional data payload for the app
            reference_id: Unique reference for idempotency (e.g., message_id, match_id)
            skip_socket_check: If True, send even if user is on socket (for calls)
        
        Returns:
            True if notification was sent to at least one device
        """
        # Idempotency check
        idempotency_key = self._generate_idempotency_key(user_id, event_type, reference_id)
        if self._is_duplicate(idempotency_key):
            logger.debug(f"Skipping duplicate notification: {idempotency_key}")
            return False
        
        # Check if user is active on socket (skip push if they're already receiving real-time)
        if not skip_socket_check:
            is_active = await self._is_user_active_on_socket(user_id)
            if is_active:
                logger.debug(f"User {user_id} is active on socket, skipping push")
                return False
        
        # Check user notification settings
        settings = await self._get_user_notification_settings(user_id)
        setting_key = {
            NotificationEvent.NEW_MESSAGE: "messages",
            NotificationEvent.NEW_MATCH: "matches",
            NotificationEvent.INCOMING_CALL: "calls"
        }.get(event_type, "messages")
        
        if not settings.get(setting_key, True):
            logger.debug(f"User {user_id} has disabled {setting_key} notifications")
            return False
        
        # Get user's FCM tokens
        tokens = await self._get_user_fcm_tokens(user_id)
        if not tokens:
            logger.debug(f"No FCM tokens for user {user_id}")
            return False
        
        # Mark as sent (before actual send to prevent race conditions)
        self._mark_sent(idempotency_key)
        
        # Prepare notification data
        notification_data = {
            "event_type": event_type,
            "reference_id": reference_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }
        
        # Send to all user devices (fire-and-forget, parallel)
        success_count = 0
        tasks = []
        
        for token in tokens:
            tasks.append(self._send_fcm_message(token, title, body, notification_data))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, bool) and result:
                success_count += 1
            elif isinstance(result, bool) and not result:
                # Token might be invalid, schedule invalidation
                asyncio.create_task(self._invalidate_token(user_id, tokens[i]))
        
        logger.info(f"Sent notification to {success_count}/{len(tokens)} devices for user {user_id}")
        return success_count > 0
    
    # Convenience methods for specific events
    
    async def notify_new_message(
        self,
        receiver_id: str,
        sender_name: str,
        message_preview: str,
        message_id: str,
        sender_id: str
    ):
        """
        Send push notification for new message.
        
        Decision Logic (Socket vs Push):
        - If user is active on WebSocket: Skip push (they get real-time)
        - If user is offline or inactive: Send push notification
        """
        await self.send_notification(
            user_id=receiver_id,
            event_type=NotificationEvent.NEW_MESSAGE,
            title=f"New message from {sender_name}",
            body=message_preview[:100] if message_preview else "You have a new message",
            data={
                "sender_id": sender_id,
                "sender_name": sender_name,
                "click_action": "OPEN_CHAT"
            },
            reference_id=message_id
        )
    
    async def notify_new_match(
        self,
        user_id: str,
        matched_user_name: str,
        match_id: str,
        matched_user_id: str
    ):
        """Send push notification for new match"""
        await self.send_notification(
            user_id=user_id,
            event_type=NotificationEvent.NEW_MATCH,
            title="New Match! 💕",
            body=f"You matched with {matched_user_name}!",
            data={
                "matched_user_id": matched_user_id,
                "matched_user_name": matched_user_name,
                "click_action": "OPEN_MATCH"
            },
            reference_id=match_id
        )
    
    async def notify_incoming_call(
        self,
        receiver_id: str,
        caller_name: str,
        call_id: str,
        caller_id: str,
        call_type: str = "audio"
    ):
        """
        Send push notification for incoming call.
        
        Note: Calls always send push even if user is on socket,
        as the socket might be in a different screen.
        """
        call_type_display = "Video" if call_type == "video" else "Audio"
        await self.send_notification(
            user_id=receiver_id,
            event_type=NotificationEvent.INCOMING_CALL,
            title=f"Incoming {call_type_display} Call",
            body=f"{caller_name} is calling you",
            data={
                "caller_id": caller_id,
                "caller_name": caller_name,
                "call_type": call_type,
                "click_action": "ANSWER_CALL"
            },
            reference_id=call_id,
            skip_socket_check=True  # Always send for calls
        )


# Singleton instance
fcm_service = FCMService()


# ============================================
# Notification Event Payloads Documentation
# ============================================
"""
Notification Event → Trigger → Payload

1. NEW_MESSAGE
   Trigger: When a message is sent via REST API or WebSocket
   Payload:
   {
     "event_type": "new_message",
     "reference_id": "<message_id>",
     "sender_id": "<user_id>",
     "sender_name": "<name>",
     "click_action": "OPEN_CHAT",
     "timestamp": "<iso_datetime>"
   }

2. NEW_MATCH
   Trigger: When two users mutually like each other
   Payload:
   {
     "event_type": "new_match",
     "reference_id": "<match_id>",
     "matched_user_id": "<user_id>",
     "matched_user_name": "<name>",
     "click_action": "OPEN_MATCH",
     "timestamp": "<iso_datetime>"
   }

3. INCOMING_CALL
   Trigger: When a call is initiated to a user
   Payload:
   {
     "event_type": "incoming_call",
     "reference_id": "<call_id>",
     "caller_id": "<user_id>",
     "caller_name": "<name>",
     "call_type": "audio|video",
     "click_action": "ANSWER_CALL",
     "timestamp": "<iso_datetime>"
   }

Socket vs Push Decision Logic:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─────────────────┬───────────────────┬──────────────┐
│ Event Type      │ User on Socket?   │ Send Push?   │
├─────────────────┼───────────────────┼──────────────┤
│ new_message     │ Yes               │ No           │
│ new_message     │ No                │ Yes          │
│ new_match       │ Yes               │ No           │
│ new_match       │ No                │ Yes          │
│ incoming_call   │ Yes               │ Yes (always) │
│ incoming_call   │ No                │ Yes          │
└─────────────────┴───────────────────┴──────────────┘

FCM Token Lifecycle:
━━━━━━━━━━━━━━━━━━━━
1. App Launch → Firebase SDK generates token
2. Token Received → App calls POST /api/users/fcm-token
3. Backend stores token in user.fcm_tokens array
4. On token refresh → App calls POST /api/users/fcm-token with new token
5. On logout → App calls DELETE /api/users/fcm-token
6. On failed delivery → Backend auto-removes invalid token
"""

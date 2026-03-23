import os
import logging
from typing import List, Dict, Optional
import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger("fcm")

class FCMService:
    _initialized = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return
        
        try:
            # First try FIREBASE_CREDENTIALS env var (path to JSON file)
            cred_path = os.getenv("FIREBASE_CREDENTIALS")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                cls._initialized = True
                logger.info("Firebase Admin initialized via FIREBASE_CREDENTIALS path.")
            else:
                # Try default credentials (works well in GCP/AWS if service account is attached)
                firebase_admin.initialize_app()
                cls._initialized = True
                logger.info("Firebase Admin initialized using application default credentials.")
        except Exception as e:
            logger.warning(f"Firebase Admin initialization failed. Push notifications will be disabled: {e}")

    @classmethod
    async def send_notification(
        cls, 
        tokens: List[str], 
        title: str, 
        body: str, 
        data: Optional[Dict[str, str]] = None
    ):
        """
        Sends an FCM push notification to the specified tokens.
        Tokens should be fetched from TBUser.fcm_tokens.
        """
        if not cls._initialized:
            logger.debug(f"FCM skipped (not initialized): to {len(tokens)} tokens, title='{title}'")
            return

        if not tokens:
            return

        # Ensure all data values are strings (FCM requirement)
        fcm_data = {}
        if data:
            fcm_data = {k: str(v) for k, v in data.items()}

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=fcm_data,
                tokens=tokens
            )
            response = messaging.send_each_for_multicast(message)
            logger.info(f"FCM Multicast sent: {response.success_count} success, {response.failure_count} failed")
            
            # Optionally handle failed tokens (e.g. invalid permissions) to remove them from DB.
        except Exception as e:
            logger.error(f"FCM Multicast error: {e}")

    @classmethod
    async def notify_new_message(
        cls,
        receiver_id: str,
        sender_name: str,
        message_preview: str,
        message_id: str,
        sender_id: str
    ):
        """
        Safe no-op fallback for now as requested. 
        Logs arguments and returns True without raising.
        """
        logger.debug(f"[FCM DEBUG] notify_new_message: receiver={receiver_id}, sender={sender_name}, preview={message_preview}")
        return True

fcm_service = FCMService()
# Auto-init on import
# We do this asynchronously or simply try it once
fcm_service.initialize()

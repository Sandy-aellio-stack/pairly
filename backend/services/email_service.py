"""
Email Service for Luveloop
Handles sending emails for password resets, notifications, etc.
"""
import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger("email_service")

class EmailService:
    """
    Email service for sending transactional emails.
    In production, integrate with SendGrid, AWS SES, or similar service.
    """

    def __init__(self):
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.from_email = os.getenv("EMAIL_FROM", "noreply@luveloop.app")
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = os.getenv("SMTP_PORT")
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")

        if not self.enabled:
            logger.warning("⚠️ Email service is DISABLED. Using mock mode.")
            logger.warning("⚠️ Set EMAIL_ENABLED=true to enable real emails.")

    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> bool:
        """
        Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML content
            text: Plain text content (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"📧 [MOCK] Email to {to}: {subject}")
            logger.info(f"📧 [MOCK] Content: {html[:100]}...")
            return True

        try:
            # TODO: Implement actual email sending
            # For production, use services like:
            # - SendGrid: https://sendgrid.com/
            # - AWS SES: https://aws.amazon.com/ses/
            # - Mailgun: https://www.mailgun.com/
            # - Postmark: https://postmarkapp.com/

            logger.info(f"📧 Sending email to {to}: {subject}")

            # Example with SMTP (basic implementation)
            # import smtplib
            # from email.mime.text import MIMEText
            # from email.mime.multipart import MIMEMultipart
            #
            # msg = MIMEMultipart('alternative')
            # msg['Subject'] = subject
            # msg['From'] = self.from_email
            # msg['To'] = to
            #
            # if text:
            #     msg.attach(MIMEText(text, 'plain'))
            # msg.attach(MIMEText(html, 'html'))
            #
            # with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            #     server.starttls()
            #     server.login(self.smtp_user, self.smtp_password)
            #     server.send_message(msg)

            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def send_password_reset_email(
        self,
        to: str,
        reset_link: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Send password reset email.

        Args:
            to: User email address
            reset_link: Password reset link
            user_name: User's name (optional)

        Returns:
            True if email sent successfully
        """
        greeting = f"Hi {user_name}" if user_name else "Hi"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea;
                          color: white; text-decoration: none; border-radius: 5px;
                          font-weight: bold; margin: 20px 0; }}
                .button:hover {{ background: #5568d3; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107;
                           padding: 10px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>{greeting},</p>
                    <p>We received a request to reset your password for your Luveloop account.</p>
                    <p>Click the button below to reset your password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #667eea;">{reset_link}</p>
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong><br>
                        • This link will expire in 10 minutes<br>
                        • If you didn't request this, please ignore this email<br>
                        • Never share this link with anyone
                    </div>
                    <p>If you didn't request a password reset, you can safely ignore this email.
                       Your password will remain unchanged.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} Luveloop. All rights reserved.</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text = f"""
        {greeting},

        We received a request to reset your password for your Luveloop account.

        Click this link to reset your password:
        {reset_link}

        Security Notice:
        - This link will expire in 10 minutes
        - If you didn't request this, please ignore this email
        - Never share this link with anyone

        If you didn't request a password reset, you can safely ignore this email.

        Luveloop Team
        """

        return await self.send_email(
            to=to,
            subject="Reset Your Luveloop Password",
            html=html,
            text=text
        )

    async def send_password_changed_notification(
        self,
        to: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Send notification that password was successfully changed.
        """
        greeting = f"Hi {user_name}" if user_name else "Hi"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #28a745; color: white; padding: 30px;
                           text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Password Changed Successfully</h1>
                </div>
                <div class="content">
                    <p>{greeting},</p>
                    <p>Your Luveloop password has been successfully changed.</p>
                    <p><strong>Changed at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <p>If you didn't make this change, please contact our support team immediately.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} Luveloop. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to=to,
            subject="Your Password Was Changed",
            html=html
        )


email_service = EmailService()

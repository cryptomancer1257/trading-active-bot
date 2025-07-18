"""
Simple Email Service for Testing
This service logs emails instead of sending them when email is not configured
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleEmailService:
    """Simple email service that logs emails instead of sending them"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', '')
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@botmarketplace.com')
        self.from_name = os.getenv('FROM_NAME', 'Bot Marketplace')
        
        # Check if email is configured
        self.email_configured = bool(self.smtp_server and self.smtp_username and self.smtp_password)
        
        if not self.email_configured:
            logger.warning("Email service not configured - emails will be logged instead of sent")
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Send email or log it if not configured"""
        if self.email_configured:
            return self._send_real_email(to_email, subject, html_body, text_body)
        else:
            return self._log_email(to_email, subject, html_body, text_body)
    
    def _send_real_email(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Send actual email using SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text version
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, int(os.getenv('SMTP_PORT', 587))) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _log_email(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Log email instead of sending it"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info("="*60)
        logger.info(f"📧 EMAIL NOTIFICATION (LOGGED) - {timestamp}")
        logger.info("="*60)
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info("-"*60)
        
        if text_body:
            logger.info("Text Body:")
            logger.info(text_body)
        else:
            # Extract text from HTML for logging
            import re
            clean_text = re.sub('<[^<]+?>', '', html_body)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            logger.info("Body:")
            logger.info(clean_text)
        
        logger.info("="*60)
        
        return True

# Global instance
email_service = SimpleEmailService() 
"""
Gmail SMTP Service - Backup solution for SendGrid
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GmailSMTPService:
    """Gmail SMTP service for email sending"""
    
    def __init__(self):
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.smtp_username = os.getenv('GMAIL_USERNAME', '')
        self.smtp_password = os.getenv('GMAIL_PASSWORD', '')  # App password
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.from_name = os.getenv('FROM_NAME', 'Bot Marketplace')
        
        self.email_configured = bool(self.smtp_username and self.smtp_password)
        
        if not self.email_configured:
            logger.warning("Gmail SMTP not configured - emails will be logged")
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Send email using Gmail SMTP"""
        if not self.email_configured:
            return self._log_email(to_email, subject, html_body, text_body)
            
        try:
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
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _log_email(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Log email instead of sending"""
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
            import re
            clean_text = re.sub('<[^<]+?>', '', html_body)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            logger.info("Body:")
            logger.info(clean_text)
        
        logger.info("="*60)
        logger.info("💡 To enable Gmail SMTP:")
        logger.info("   1. Enable 2-factor authentication on Gmail")
        logger.info("   2. Generate App Password: https://myaccount.google.com/apppasswords")
        logger.info("   3. Add to .env: GMAIL_USERNAME=your_email@gmail.com")
        logger.info("   4. Add to .env: GMAIL_PASSWORD=your_16_char_app_password")
        logger.info("="*60)
        
        return True
    
    def send_bot_notification(self, to_email: str, bot_name: str, action: str, details: dict):
        """Send formatted bot notification"""
        # Similar to SendGrid version but using Gmail SMTP
        action_emoji = {
            "BUY": "🟢",
            "SELL": "🔴", 
            "HOLD": "🟡",
            "ERROR": "❌"
        }.get(action, "📊")
        
        subject = f"{action_emoji} Bot {action} Signal - {bot_name}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2>{action_emoji} Bot {action} Signal</h2>
            <h3>{bot_name}</h3>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px;">
                <p><strong>Symbol:</strong> {details.get('symbol', 'N/A')}</p>
                <p><strong>Price:</strong> ${details.get('price', 'N/A')}</p>
                <p><strong>Action:</strong> {action}</p>
                <p><strong>Time:</strong> {details.get('timestamp', 'N/A')}</p>
                <p><strong>Reason:</strong> {details.get('reason', 'N/A')}</p>
            </div>
            
            {'<p style="background-color: #fff3cd; padding: 10px; border-radius: 5px;">🧪 TESTNET MODE</p>' if details.get('is_testnet', True) else ''}
            
            <p><small>Bot Marketplace - Automated Trading Platform</small></p>
        </body>
        </html>
        """
        
        text_body = f"""
{action_emoji} Bot {action} Signal - {bot_name}

Symbol: {details.get('symbol', 'N/A')}
Price: ${details.get('price', 'N/A')}
Action: {action}
Time: {details.get('timestamp', 'N/A')}
Reason: {details.get('reason', 'N/A')}

{'🧪 TESTNET MODE' if details.get('is_testnet', True) else ''}

Bot Marketplace - Automated Trading Platform
        """
        
        return self.send_email(to_email, subject, html_body, text_body)

# Global instance
email_service = GmailSMTPService() 
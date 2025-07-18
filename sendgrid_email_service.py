"""
SendGrid Email Service
Easy email sending without requiring users to configure SMTP/Gmail App passwords
"""

import os
import logging
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, HtmlContent, Content
from typing import Dict, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

logger = logging.getLogger(__name__)

class SendGridEmailService:
    """SendGrid email service for easy email sending"""
    
    def __init__(self):
        # SendGrid configuration - only admin needs to set this once
        self.api_key = os.getenv('SENDGRID_API_KEY', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@botmarketplace.com')
        self.from_name = os.getenv('FROM_NAME', 'Bot Marketplace')
        
        # Check if SendGrid is configured
        self.email_configured = bool(self.api_key)
        
        if self.email_configured:
            self.sg = SendGridAPIClient(api_key=self.api_key)
            logger.info("SendGrid email service initialized successfully")
        else:
            logger.warning("SendGrid not configured - emails will be logged instead of sent")
            logger.info("To enable email: Set SENDGRID_API_KEY in environment variables")
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Send email using SendGrid or log it if not configured"""
        if self.email_configured:
            return self._send_sendgrid_email(to_email, subject, html_body, text_body)
        else:
            return self._log_email(to_email, subject, html_body, text_body)
    
    def _send_sendgrid_email(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Send email using SendGrid API"""
        try:
            # Create the email
            from_email = From(self.from_email, self.from_name)
            to_email_obj = To(to_email)
            subject_obj = Subject(subject)
            
            # Add HTML content
            html_content = HtmlContent(html_body)
            
            # Create Mail object
            mail = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject_obj,
                html_content=html_content
            )
            
            # Add text content if provided
            if text_body:
                mail.add_content(Content("text/plain", text_body))
            
            # Send the email
            response = self.sg.send(mail)
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {to_email} via SendGrid")
                return True
            else:
                logger.error(f"SendGrid API returned status {response.status_code}: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid to {to_email}: {e}")
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
        logger.info("💡 To enable actual email sending:")
        logger.info("   1. Get SendGrid API key from https://app.sendgrid.com/settings/api_keys")
        logger.info("   2. Set SENDGRID_API_KEY in your .env file")
        logger.info("   3. Restart the application")
        logger.info("="*60)
        
        return True
    
    def send_bot_notification(self, to_email: str, bot_name: str, action: str, details: Dict[str, Any]):
        """Send formatted bot notification email"""
        # Action emojis
        action_emoji = {
            "BUY": "🟢",
            "SELL": "🔴", 
            "HOLD": "🟡",
            "ERROR": "❌"
        }.get(action, "📊")
        
        # Subject
        subject = f"{action_emoji} Bot {action} Signal - {bot_name}"
        
        # HTML content
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px; }}
                .action-badge {{ display: inline-block; background-color: #f8f9fa; color: #333; padding: 8px 16px; border-radius: 20px; font-weight: bold; margin: 10px 0; }}
                .details {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 8px 0; }}
                .detail-label {{ font-weight: bold; color: #555; }}
                .detail-value {{ color: #333; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px; text-align: center; }}
                .warning {{ background-color: #fff3cd; color: #856404; padding: 12px; border-radius: 6px; margin: 15px 0; border-left: 4px solid #ffc107; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{action_emoji} Bot Trading Alert</h2>
                    <p>{bot_name}</p>
                </div>
                
                <div class="action-badge">
                    Action: {action}
                </div>
                
                <div class="details">
                    <div class="detail-row">
                        <span class="detail-label">Symbol:</span>
                        <span class="detail-value">{details.get('symbol', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Price:</span>
                        <span class="detail-value">${details.get('price', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Confidence:</span>
                        <span class="detail-value">{details.get('confidence', 'N/A')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Time:</span>
                        <span class="detail-value">{details.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Timeframe:</span>
                        <span class="detail-value">{details.get('timeframe', 'N/A')}</span>
                    </div>
                </div>
                
                {f'<div class="warning">🧪 TESTNET MODE - No real trades executed</div>' if details.get('is_testnet', True) else ''}
                
                <div style="background-color: #e8f4f8; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <strong>📝 Reason:</strong><br>
                    {details.get('reason', 'Bot analysis complete')}
                </div>
                
                <div class="footer">
                    <p>Bot Marketplace - Automated Trading Platform</p>
                    <p>{'🧪 TESTNET MODE' if details.get('is_testnet', True) else '🚀 LIVE TRADING'}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text version
        text_body = f"""
{action_emoji} Bot {action} Signal - {bot_name}

Symbol: {details.get('symbol', 'N/A')}
Price: ${details.get('price', 'N/A')}
Action: {action}
Confidence: {details.get('confidence', 'N/A')}
Time: {details.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
Timeframe: {details.get('timeframe', 'N/A')}

Reason: {details.get('reason', 'Bot analysis complete')}

{'🧪 TESTNET MODE - No real trades executed' if details.get('is_testnet', True) else '🚀 LIVE TRADING'}

---
Bot Marketplace - Automated Trading Platform
        """
        
        return self.send_email(to_email, subject, html_body, text_body)

# Global instance
email_service = SendGridEmailService() 
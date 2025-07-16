"""
Email Notification Service
Handles all email notifications for bot activities, trades, and alerts
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending bot notifications"""
    
    def __init__(self):
        # Email configuration - these should be environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@botmarketplace.com')
        self.from_name = os.getenv('FROM_NAME', 'Bot Marketplace')
        
        # Setup Jinja2 for email templates
        template_dir = os.path.join(os.path.dirname(__file__), 'email_templates')
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        # Thread pool for async email sending
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def _send_email_sync(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Send email synchronously"""
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
    
    async def send_email_async(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Send email asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._send_email_sync, 
            to_email, 
            subject, 
            html_body, 
            text_body
        )
    
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None):
        """Send email synchronously (for use in non-async contexts)"""
        return self._send_email_sync(to_email, subject, html_body, text_body)
    
    def _render_template(self, template_name: str, **context) -> str:
        """Render email template with context"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            return self._get_fallback_html(template_name, context)
    
    def _get_fallback_html(self, template_name: str, context: Dict[str, Any]) -> str:
        """Fallback HTML when template rendering fails"""
        return f"""
        <html>
        <head><title>Bot Marketplace Notification</title></head>
        <body>
        <h2>Bot Marketplace Notification</h2>
        <p>Template: {template_name}</p>
        <p>Context: {json.dumps(context, indent=2, default=str)}</p>
        </body>
        </html>
        """
    
    # === Trade Notifications ===
    
    async def send_trade_notification(
        self, 
        user_email: str, 
        subscription_id: int,
        bot_name: str,
        trade_data: Dict[str, Any],
        is_testnet: bool = True
    ):
        """Send notification for new trade"""
        
        env_label = "🧪 TESTNET" if is_testnet else "🚀 MAINNET"
        subject = f"{env_label} Trade Alert: {bot_name}"
        
        context = {
            'bot_name': bot_name,
            'subscription_id': subscription_id,
            'trade_data': trade_data,
            'is_testnet': is_testnet,
            'env_label': env_label,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trade_side': trade_data.get('side', 'UNKNOWN'),
            'symbol': trade_data.get('symbol', 'UNKNOWN'),
            'quantity': trade_data.get('quantity', '0'),
            'price': trade_data.get('price', '0'),
            'trade_type': trade_data.get('type', 'MARKET')
        }
        
        html_body = self._render_template('trade_notification.html', **context)
        text_body = self._render_template('trade_notification.txt', **context)
        
        await self.send_email_async(user_email, subject, html_body, text_body)
    
    async def send_signal_notification(
        self, 
        user_email: str,
        subscription_id: int,
        bot_name: str,
        signal_data: Dict[str, Any],
        is_testnet: bool = True
    ):
        """Send notification for trading signal"""
        
        env_label = "🧪 TESTNET" if is_testnet else "🚀 MAINNET"
        signal_type = signal_data.get('signal_type', 'UNKNOWN').upper()
        subject = f"{env_label} Signal: {signal_type} - {bot_name}"
        
        context = {
            'bot_name': bot_name,
            'subscription_id': subscription_id,
            'signal_data': signal_data,
            'is_testnet': is_testnet,
            'env_label': env_label,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'signal_type': signal_type,
            'symbol': signal_data.get('symbol', 'UNKNOWN'),
            'price': signal_data.get('current_price', '0'),
            'confidence': signal_data.get('confidence', '0'),
            'message': signal_data.get('message', '')
        }
        
        html_body = self._render_template('signal_notification.html', **context)
        text_body = self._render_template('signal_notification.txt', **context)
        
        await self.send_email_async(user_email, subject, html_body, text_body)
    
    async def send_bot_error_notification(
        self,
        user_email: str,
        subscription_id: int,
        bot_name: str,
        error_data: Dict[str, Any],
        is_testnet: bool = True
    ):
        """Send notification for bot errors"""
        
        env_label = "🧪 TESTNET" if is_testnet else "🚀 MAINNET"
        subject = f"{env_label} Bot Error: {bot_name}"
        
        context = {
            'bot_name': bot_name,
            'subscription_id': subscription_id,
            'error_data': error_data,
            'is_testnet': is_testnet,
            'env_label': env_label,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_type': error_data.get('error_type', 'UNKNOWN'),
            'error_message': error_data.get('message', ''),
            'error_details': error_data.get('details', '')
        }
        
        html_body = self._render_template('bot_error_notification.html', **context)
        text_body = self._render_template('bot_error_notification.txt', **context)
        
        await self.send_email_async(user_email, subject, html_body, text_body)
    
    async def send_performance_summary(
        self,
        user_email: str,
        subscription_id: int,
        bot_name: str,
        performance_data: Dict[str, Any],
        is_testnet: bool = True
    ):
        """Send daily/weekly performance summary"""
        
        env_label = "🧪 TESTNET" if is_testnet else "🚀 MAINNET"
        subject = f"{env_label} Performance Summary: {bot_name}"
        
        context = {
            'bot_name': bot_name,
            'subscription_id': subscription_id,
            'performance_data': performance_data,
            'is_testnet': is_testnet,
            'env_label': env_label,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_trades': performance_data.get('total_trades', 0),
            'winning_trades': performance_data.get('winning_trades', 0),
            'total_pnl': performance_data.get('total_pnl', 0),
            'win_rate': performance_data.get('win_rate', 0),
            'period': performance_data.get('period', 'Daily')
        }
        
        html_body = self._render_template('performance_summary.html', **context)
        text_body = self._render_template('performance_summary.txt', **context)
        
        await self.send_email_async(user_email, subject, html_body, text_body)
    
    async def send_trial_expiry_notification(
        self,
        user_email: str,
        subscription_id: int,
        bot_name: str,
        expires_in_hours: int
    ):
        """Send notification when trial is about to expire"""
        
        subject = f"🧪 Trial Expiring Soon: {bot_name}"
        
        context = {
            'bot_name': bot_name,
            'subscription_id': subscription_id,
            'expires_in_hours': expires_in_hours,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        html_body = self._render_template('trial_expiry_notification.html', **context)
        text_body = self._render_template('trial_expiry_notification.txt', **context)
        
        await self.send_email_async(user_email, subject, html_body, text_body)

# Global email service instance
email_service = EmailService()

# Utility functions for easy usage
async def notify_trade(user_email: str, subscription_id: int, bot_name: str, trade_data: Dict[str, Any], is_testnet: bool = True):
    """Quick function to send trade notification"""
    await email_service.send_trade_notification(user_email, subscription_id, bot_name, trade_data, is_testnet)

async def notify_signal(user_email: str, subscription_id: int, bot_name: str, signal_data: Dict[str, Any], is_testnet: bool = True):
    """Quick function to send signal notification"""
    await email_service.send_signal_notification(user_email, subscription_id, bot_name, signal_data, is_testnet)

async def notify_error(user_email: str, subscription_id: int, bot_name: str, error_data: Dict[str, Any], is_testnet: bool = True):
    """Quick function to send error notification"""
    await email_service.send_bot_error_notification(user_email, subscription_id, bot_name, error_data, is_testnet) 
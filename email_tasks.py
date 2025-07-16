"""
Email Notification Tasks
Celery tasks for sending asynchronous email notifications for bot activities
"""

import logging
from typing import Dict, Any
from celery import Celery
from datetime import datetime

from email_service import email_service

logger = logging.getLogger(__name__)

# Use the same Celery app as main tasks
celery_app = Celery(
    'bot_marketplace',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task(bind=True, name='send_trade_notification')
def send_trade_notification_task(self, user_email: str, subscription_id: int, bot_name: str, 
                                trade_data: Dict[str, Any], is_testnet: bool = True):
    """Celery task to send trade notification email"""
    try:
        # Use synchronous email sending in Celery worker
        env_label = "🧪 TESTNET" if is_testnet else "🚀 MAINNET"
        subject = f"{env_label} Trade Alert: {bot_name}"
        
        # Create HTML content
        html_content = f"""
        <html>
        <head><title>Trade Alert</title></head>
        <body>
            <h2>{env_label} Trade Alert</h2>
            <h3>{bot_name}</h3>
            <p><strong>Action:</strong> {trade_data.get('side', 'UNKNOWN')}</p>
            <p><strong>Symbol:</strong> {trade_data.get('symbol', 'UNKNOWN')}</p>
            <p><strong>Quantity:</strong> {trade_data.get('quantity', '0')}</p>
            <p><strong>Price:</strong> ${trade_data.get('price', '0')}</p>
            <p><strong>Type:</strong> {trade_data.get('type', 'MARKET')}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <p><a href="http://localhost:8000/subscriptions/{subscription_id}">View Details</a></p>
        </body>
        </html>
        """
        
        # Create text content
        text_content = f"""
        {env_label} TRADE ALERT - {bot_name}
        
        Action: {trade_data.get('side', 'UNKNOWN')}
        Symbol: {trade_data.get('symbol', 'UNKNOWN')}
        Quantity: {trade_data.get('quantity', '0')}
        Price: ${trade_data.get('price', '0')}
        Type: {trade_data.get('type', 'MARKET')}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        View Details: http://localhost:8000/subscriptions/{subscription_id}
        """
        
        # Send email synchronously
        success = email_service.send_email(user_email, subject, html_content, text_content)
        
        if success:
            logger.info(f"Trade notification sent successfully to {user_email}")
        else:
            logger.error(f"Failed to send trade notification to {user_email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in trade notification task: {e}")
        return False

@celery_app.task(bind=True, name='send_signal_notification')
def send_signal_notification_task(self, user_email: str, subscription_id: int, bot_name: str, 
                                 signal_data: Dict[str, Any], is_testnet: bool = True):
    """Celery task to send signal notification email"""
    try:
        env_label = "🧪 TESTNET" if is_testnet else "🚀 MAINNET"
        signal_type = signal_data.get('signal_type', 'UNKNOWN').upper()
        subject = f"{env_label} Signal: {signal_type} - {bot_name}"
        
        # Create HTML content
        html_content = f"""
        <html>
        <head><title>Signal Alert</title></head>
        <body>
            <h2>{env_label} Signal Alert</h2>
            <h3>{bot_name}</h3>
            <p><strong>Signal Type:</strong> {signal_type}</p>
            <p><strong>Symbol:</strong> {signal_data.get('symbol', 'UNKNOWN')}</p>
            <p><strong>Current Price:</strong> ${signal_data.get('current_price', '0')}</p>
            <p><strong>Confidence:</strong> {signal_data.get('confidence', '0')}%</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            {f"<p><strong>Message:</strong> {signal_data.get('message', '')}</p>" if signal_data.get('message') else ""}
            
            <p><a href="http://localhost:8000/subscriptions/{subscription_id}">View Details</a></p>
        </body>
        </html>
        """
        
        # Create text content
        text_content = f"""
        {env_label} SIGNAL ALERT - {bot_name}
        
        Signal Type: {signal_type}
        Symbol: {signal_data.get('symbol', 'UNKNOWN')}
        Current Price: ${signal_data.get('current_price', '0')}
        Confidence: {signal_data.get('confidence', '0')}%
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        {f"Message: {signal_data.get('message', '')}" if signal_data.get('message') else ""}
        
        View Details: http://localhost:8000/subscriptions/{subscription_id}
        """
        
        # Send email synchronously
        success = email_service.send_email(user_email, subject, html_content, text_content)
        
        if success:
            logger.info(f"Signal notification sent successfully to {user_email}")
        else:
            logger.error(f"Failed to send signal notification to {user_email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in signal notification task: {e}")
        return False

@celery_app.task(bind=True, name='send_bot_error_notification')
def send_bot_error_notification_task(self, user_email: str, subscription_id: int, bot_name: str, 
                                    error_data: Dict[str, Any], is_testnet: bool = True):
    """Celery task to send bot error notification email"""
    try:
        env_label = "🧪 TESTNET" if is_testnet else "🚀 MAINNET"
        subject = f"{env_label} Bot Error: {bot_name}"
        
        # Create HTML content
        html_content = f"""
        <html>
        <head><title>Bot Error Alert</title></head>
        <body>
            <h2>{env_label} Bot Error Alert</h2>
            <h3>{bot_name}</h3>
            <p><strong>Error Type:</strong> {error_data.get('error_type', 'UNKNOWN')}</p>
            <p><strong>Error Message:</strong> {error_data.get('message', '')}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            {f"<p><strong>Details:</strong> {error_data.get('details', '')}</p>" if error_data.get('details') else ""}
            
            <p><a href="http://localhost:8000/subscriptions/{subscription_id}">View Details</a></p>
        </body>
        </html>
        """
        
        # Create text content
        text_content = f"""
        {env_label} BOT ERROR ALERT - {bot_name}
        
        Error Type: {error_data.get('error_type', 'UNKNOWN')}
        Error Message: {error_data.get('message', '')}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        {f"Details: {error_data.get('details', '')}" if error_data.get('details') else ""}
        
        View Details: http://localhost:8000/subscriptions/{subscription_id}
        """
        
        # Send email synchronously
        success = email_service.send_email(user_email, subject, html_content, text_content)
        
        if success:
            logger.info(f"Error notification sent successfully to {user_email}")
        else:
            logger.error(f"Failed to send error notification to {user_email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in bot error notification task: {e}")
        return False

# Helper functions for easy usage
def notify_trade_async(user_email: str, subscription_id: int, bot_name: str, 
                      trade_data: Dict[str, Any], is_testnet: bool = True):
    """Queue trade notification for async sending"""
    send_trade_notification_task.apply_async(
        args=[user_email, subscription_id, bot_name, trade_data, is_testnet],
        countdown=1  # Send after 1 second
    )

def notify_signal_async(user_email: str, subscription_id: int, bot_name: str, 
                       signal_data: Dict[str, Any], is_testnet: bool = True):
    """Queue signal notification for async sending"""
    send_signal_notification_task.apply_async(
        args=[user_email, subscription_id, bot_name, signal_data, is_testnet],
        countdown=1  # Send after 1 second
    )

def notify_error_async(user_email: str, subscription_id: int, bot_name: str, 
                      error_data: Dict[str, Any], is_testnet: bool = True):
    """Queue error notification for async sending"""
    send_bot_error_notification_task.apply_async(
        args=[user_email, subscription_id, bot_name, error_data, is_testnet],
        countdown=1  # Send after 1 second
    ) 
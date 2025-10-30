"""
Telegram bot service for airdrop verification
"""

import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

import telebot
from telebot import types

from core.models import TelegramVerification
from core.database import get_db

logger = logging.getLogger(__name__)

class TelegramVerificationBot:
    """Telegram bot for airdrop verification"""
    
    def __init__(self, bot_token: str, channel_id: str):
        self.bot = telebot.TeleBot(bot_token)
        self.channel_id = channel_id
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup bot command handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            welcome_text = """
🤖 Welcome to BOT Token Airdrop Verification Bot!

This bot helps verify your Telegram membership for the airdrop campaign.

Available commands:
/verify - Get verification code for airdrop
/help - Show this help message

Join our channel and use /verify to get your verification code!
            """
            self.bot.reply_to(message, welcome_text)
        
        @self.bot.message_handler(commands=['verify'])
        def verify_member(message):
            self.handle_verification_request(message)
        
        @self.bot.message_handler(commands=['help'])
        def send_help(message):
            help_text = """
📋 BOT Token Airdrop Verification Help

Commands:
/start - Welcome message
/verify - Get verification code
/help - Show this help

How to verify:
1. Make sure you're a member of our channel
2. Use /verify command
3. Copy the verification code
4. Enter the code on the airdrop page

Need help? Contact our support team.
            """
            self.bot.reply_to(message, help_text)
        
        @self.bot.message_handler(func=lambda message: True)
        def handle_all_messages(message):
            self.bot.reply_to(message, 
                "I don't understand that command. Use /help to see available commands.")
    
    def handle_verification_request(self, message):
        """Handle verification request from user"""
        
        user_id = str(message.from_user.id)
        username = message.from_user.username or message.from_user.first_name
        
        try:
            # Check if user is member of channel
            is_member = self.check_channel_membership(user_id)
            
            if is_member:
                # Generate verification code
                verification_code = self.generate_verification_code()
                
                # Store verification code in database
                self.store_verification_code(user_id, verification_code)
                
                # Send verification code to user
                response_text = f"""
✅ Verification Successful!

Your verification code: {verification_code}

📝 Instructions:
1. Go to the airdrop page
2. Enter this verification code
3. Complete the verification process

⏰ Code expires in 10 minutes
🔒 Keep this code private

Good luck with the airdrop! 🚀
                """
                
                self.bot.reply_to(message, response_text)
                
                logger.info(f"Verification code generated for user {user_id} ({username})")
                
            else:
                # User is not a member
                response_text = """
❌ Verification Failed

You are not a member of our channel.

📋 To verify:
1. Join our Telegram channel
2. Use /verify command again

Channel: @your_channel_name
                """
                
                self.bot.reply_to(message, response_text)
                
                logger.warning(f"Verification failed for user {user_id} - not a channel member")
                
        except Exception as e:
            logger.error(f"Error handling verification request: {e}")
            self.bot.reply_to(message, 
                "❌ An error occurred. Please try again later or contact support.")
    
    def check_channel_membership(self, user_id: str) -> bool:
        """Check if user is member of the channel"""
        
        try:
            member = self.bot.get_chat_member(self.channel_id, user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
            return False
    
    def generate_verification_code(self) -> str:
        """Generate random verification code"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    def store_verification_code(self, telegram_id: str, code: str):
        """Store verification code in database"""
        
        try:
            db = next(get_db())
            
            # Create verification record
            verification = TelegramVerification(
                telegram_id=telegram_id,
                code=code,
                expires_at=datetime.now() + timedelta(minutes=10)
            )
            
            db.add(verification)
            db.commit()
            db.close()
            
            logger.info(f"Verification code stored: {code} for {telegram_id}")
            
        except Exception as e:
            logger.error(f"Error storing verification code: {e}")
            raise
    
    def start_polling(self):
        """Start bot polling"""
        logger.info("Starting Telegram verification bot...")
        self.bot.polling(none_stop=True)


def create_telegram_bot(bot_token: str, channel_id: str) -> TelegramVerificationBot:
    """Create and return Telegram verification bot instance"""
    return TelegramVerificationBot(bot_token, channel_id)


# Example usage
if __name__ == "__main__":
    import os
    
    # Get configuration from environment
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
    
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.error("Telegram bot token and channel ID must be set")
        exit(1)
    
    # Create and start bot
    bot = create_telegram_bot(BOT_TOKEN, CHANNEL_ID)
    
    try:
        bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")

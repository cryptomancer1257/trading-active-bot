"""
 Telegram Service
"""
import asyncio
import os
import re
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import time
from telegram import Bot
from telegram.ext import ApplicationBuilder
from telegram.ext import MessageHandler, filters, ContextTypes
from telegram.ext import CallbackQueryHandler
from telegram import Update
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
import requests
import telegramify_markdown
from core.database import SessionLocal, get_db
from core import crud, models
import datetime
from core.tasks import run_bot_signal_logic, run_bot_logic

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        self.development_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'

    async def run(self):
        logger.info("Starting Telegram Service with mode %s", "development" if self.development_mode else "production")
        if self.development_mode:
            await self.run_polling()
        else:
            await self.run_webhook()

    async def run_webhook(self):
        try: 
            logger.info("Running Telegram bot in webhook mode")
            if not self.bot_token or not self.webhook_url:
                logger.error("❌ Missing Telegram bot token or webhook URL")
                return
            bot = Bot(token=self.bot_token)
            await bot.set_webhook(
                url=self.webhook_url,
                drop_pending_updates=True
            )
            logger.info(f"✅ Webhook configured for URL: {self.webhook_url}")
        except Exception as e:
            logger.error(f"❌ Error configuring webhook: {e}")

    async def run_polling(self):
        # Check if polling is enabled (useful for local dev to avoid conflicts)
        if os.getenv('ENABLE_TELEGRAM_BOT', 'true').lower() == 'false':
            logger.info("⚠️  Telegram bot polling is disabled (ENABLE_TELEGRAM_BOT=false)")
            return
        
        logger.info("Running Telegram bot in polling mode")
        try:
            # Use synchronous polling in a separate thread
            import threading
            import time
            
            def start_polling_sync():
                try:
                    # Create new event loop for this thread
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    app = ApplicationBuilder().token(self.bot_token).build()
                    self.add_handlers(app)
                    logger.info("🤖 Bot running in polling mode (dev)")
                    
                    # Initialize and start polling manually (without signal handlers)
                    async def run_bot():
                        await app.initialize()
                        await app.start()
                        await app.updater.start_polling(
                            allowed_updates=["message", "callback_query"],
                            drop_pending_updates=True
                        )
                        # Keep running
                        while True:
                            await asyncio.sleep(1)
                    
                    loop.run_until_complete(run_bot())
                except Exception as e:
                    logger.error(f"❌ Error in polling thread: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Start polling in background thread
            polling_thread = threading.Thread(target=start_polling_sync, daemon=True)
            polling_thread.start()
            logger.info("✅ Bot polling started in background thread")
            
            # Keep the async function alive
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")
            raise

    def add_handlers(self, app):
        app.add_handler(MessageHandler(filters.TEXT, self.on_message))
        app.add_handler(CallbackQueryHandler(self.on_callback_query))

    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            logger.info(f"📩 New message: {update.message.text}")
            await self.handle_telegram_message(update.to_dict())
        except Exception as e:
            logger.error(f"Polling error: {e}")

    async def on_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if update.callback_query:
                logger.info(f"🔘 Callback data: {update.callback_query.data}")
                await self.handle_telegram_message(body=update.to_dict())
        except Exception as e:
            logger.error(f"Polling error (callback): {e}")

    async def handle_telegram_message(self, body: dict):
        db = SessionLocal()
        try: 
            print(f"📨 Received Telegram message: {body}")
        
            if "callback_query" in body:
                data = body["callback_query"]["data"]
                chat_id = body["callback_query"]["message"]["chat"]["id"]
                print(f"🔘 Processing callback query: {data} from chat {chat_id}")

                if data.startswith("run_manual_bot_signal:"):
                    action = data.split(":")[1] 
                    bot_id, sub_id, bot_name = action.split("|")

                    # Sửa thành gọi không đồng bộ
                    await asyncio.to_thread(
                        requests.post,
                        f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery",
                        json={"callback_query_id": body["callback_query"]["id"]}
                    )

                    logger.info(f"trigger run_bot_signal_logic for sub_id: {sub_id}")
                    run_bot_signal_logic.delay(bot_id, sub_id)

                    await self.send_telegram_message(chat_id, f"🚀 Bot {bot_name} is starting...")
                    return {"ok": True}
                
                if data.startswith("run_manual_bot_active:"):
                    action = data.split(":")[1] 
                    bot_id, sub_id, bot_name = action.split("|")

                    # Sửa thành gọi không đồng bộ
                    await asyncio.to_thread(
                        requests.post,
                        f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery",
                        json={"callback_query_id": body["callback_query"]["id"]}
                    )
                    logger.info(f"trigger run_bot_logic for sub_id: {sub_id}")
                    run_bot_logic.delay(sub_id)

                    await self.send_telegram_message(chat_id, f"🚀 Bot {bot_name} is starting...")
                    return {"ok": True}

            # Implement your callback query handling logic here
            message = body.get("message", {})
            chat_id = str(message.get("chat", {}).get("id"))
            user_name = message.get("from", {}).get("username")
            text = message.get("text", "").strip().lower()

            if not chat_id or not user_name:
                return {"ok": False, "error": "Invalid message format"}
            if chat_id.startswith("-100"):
                chat_id = int(chat_id)
            else:
                try:
                    chat_id = int(chat_id)
                except ValueError:
                    pass
            
            print(f"🔍 DEBUG: Looking for user with telegram_username='{user_name}'")
            
            # First, try to find developer user (users table)
            developer_user = db.query(models.User).filter(
                models.User.telegram_username == user_name
            ).first()
            
            if developer_user:
                print(f"📱 Found developer user {developer_user.id} with telegram_username")
                # Update chat_id for developer user
                if developer_user.telegram_chat_id != chat_id:
                    developer_user.telegram_chat_id = chat_id
                    db.commit()
                    db.refresh(developer_user)
                    print(f"📱 Updated chat_id for developer user {developer_user.id}: {chat_id}")
                
                await self.send_telegram_message(chat_id, "✅ Welcome! You have successfully started the bot.")
                return {"ok": True}
            
            # If not developer, look for marketplace user (user_settings table)
            user_settings = crud.get_users_setting_by_telegram_username(db, telegram_username=user_name)
            print(f"🔍 DEBUG: Found {len(user_settings) if user_settings else 0} user_settings")
            
            if not user_settings or len(user_settings) == 0:
                print(f"❌ DEBUG: No user found for username '{user_name}'")
                await self.send_telegram_message(chat_id, "❌ Account not found. Please rent bot first.")
                return {"ok": False}
            
            # If multiple user_settings found, prioritize the one with active subscriptions
            if len(user_settings) > 1:
                # Find user_settings with most active subscriptions
                best_user_setting = None
                max_active_subs = 0
                
                for us in user_settings:
                    # Count active subscriptions for this user_principal_id
                    active_subs = db.query(models.Subscription).filter(
                        models.Subscription.user_principal_id == us.principal_id,
                        models.Subscription.status == 'ACTIVE'
                    ).count()
                    
                    if active_subs > max_active_subs:
                        max_active_subs = active_subs
                        best_user_setting = us
                
                if best_user_setting:
                    user_settings = [best_user_setting]
                    print(f"📱 Selected user_settings {best_user_setting.id} with {max_active_subs} active subscriptions")

            updated = False
            for user_setting in user_settings:
                if user_setting.telegram_chat_id != chat_id:
                    user_setting.telegram_chat_id = chat_id
                    updated = True
                    print(f"📱 Updated chat_id for user {user_name}: {chat_id}")
            if updated:
                db.commit()
                for user_setting in user_settings:
                    db.refresh(user_setting)

            if text.startswith("/start"):
                return await self.handle_start_command(chat_id)
            elif text.startswith("/query_signals"):
                bots = []
                for user_setting in user_settings:
                    bot_list = crud.get_all_subscription_by_principal_id(db, principal_id=user_setting.principal_id, bot_mode='PASSIVE')
                    if bot_list:
                        for bot in bot_list:
                            rent_date = getattr(bot, "started_at", None)
                            rent_date_str = rent_date.strftime("%d/%m %H:%M") if rent_date else "N/A"

                            # Lấy 5 ký tự đầu principal_id
                            principal_prefix = str(user_setting.principal_id)[:5]

                            bots.append({
                                "bot_name": bot.bot.name,
                                "bot_id": bot.bot.id,
                                "sub_id": bot.id,
                                "rent_date": rent_date_str,
                                "principal_prefix": principal_prefix
                            })
                return await self.handle_query_command(chat_id, bots, 'PASSIVE', db)
            elif text.startswith("/query_active"):
                bots = []
                for user_setting in user_settings:
                    bot_list = crud.get_all_subscription_by_principal_id(db, principal_id=user_setting.principal_id, bot_mode='ACTIVE')
                    if bot_list:
                        for bot in bot_list:
                            rent_date = getattr(bot, "started_at", None)
                            rent_date_str = rent_date.strftime("%d/%m %H:%M") if rent_date else "N/A"

                            # Lấy 5 ký tự đầu principal_id
                            principal_prefix = str(user_setting.principal_id)[:5]

                            bots.append({
                                "bot_name": bot.bot.name,
                                "bot_id": bot.bot.id,
                                "sub_id": bot.id,
                                "rent_date": rent_date_str,
                                "principal_prefix": principal_prefix
                            })
                return await self.handle_query_command(chat_id, bots, 'ACTIVE', db)
        except Exception as e:
            logger.error(f"Error handling Telegram message: {e}", exc_info=True)
            await self.send_telegram_message(chat_id, "❌ An error occurred while processing your request. Please try again later.")
            return {"ok": False, "error": str(e)}
    async def handle_start_command(self, chat_id: int):
        await self.send_telegram_message(
            chat_id,
            (
                "✅ Welcome! The bot has been successfully activated.\n\n"
                "ℹ️ With this bot, you can easily manage and monitor all your trading bots.\n\n"
                "📌 Available commands:\n"
                "• /query_signals – View all your signal bots.\n"
                "   👉 If you have rented passive bots, this command will also list them so you can run them manually.\n"
                "• /query_active – View all your active bots.\n"
                "   👉 If you have rented active bots, this command will also show them for easy control.\n\n"
                "🚀 Ready to take control? Start managing your trading bots now!"
            )
        )
        return {"ok": True}
    async def handle_query_command(self, chat_id: int, bots: list[str], bot_mode: str, db: Session):
        if not bots:
            await self.send_telegram_message(chat_id, "❌ No active subscriptions found. Please rent a bot first.")
            return {"ok": False}
        
        if bot_mode == 'ACTIVE':
            buttons = [
                [{"text": f"🚀 Run {bot['bot_name']}-{bot['principal_prefix']}-{bot['rent_date']}",
                "callback_data": f"run_manual_bot_active:{bot['bot_id']}|{bot['sub_id']}|{bot['bot_name']}"}]
                for bot in bots
            ]
        else:
            buttons = [
                [{"text": f"🚀 Run {bot['bot_name']}-{bot['principal_prefix']}-{bot['rent_date']}",
                "callback_data": f"run_manual_bot_signal:{bot['bot_id']}|{bot['sub_id']}|{bot['bot_name']}"}]
                for bot in bots
            ]

        self.send_telegram_message_v2(
            chat_id,
            "🤖 Please select a manual bot to run:",
            reply_markup={"inline_keyboard": buttons}
        )
        return {"ok": True}
    async def send_telegram_message(self, chat_id: str | int, text: str, parse_mode=None, reply_markup=None):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
            raise
    def send_telegram_message_v2(self, chat_id: str | int, text: str, parse_mode=None, reply_markup=None):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
            raise
    def send_message_safe_telegram(self, chat_id: str | int, text: str, use_markdown: bool = True):
        print(f"[{datetime.datetime.now(datetime.timezone.utc)}] ✅ Telegram sent")
        MAX_LENGTH = 4000

        if len(text) > MAX_LENGTH:
            print(f"📏 Message too long ({len(text)} chars), splitting into chunks...")
            return self.send_long_message(chat_id, text, use_markdown)

        if use_markdown:
            try:
                return self.send_markdown_v2(chat_id, text)
            except Exception as e:
                print(f"⚠️ MarkdownV2 failed, fallback to plain text: {e}")
                return self.send_telegram_message_v2(chat_id, text)
        else:
            return self.send_telegram_message_v2(chat_id, text)
    def send_markdown_v2(self, chat_id: str | int, text: str):
        formatted_text = self.format_telegram_message(text)
        try:
            # Escape MarkdownV2 an toàn
            safe_text = telegramify_markdown.standardize(formatted_text)
            # print(f"🔄 Safe text: {safe_text[:100]}...")
        except Exception as e:
            print(f"⚠️ telegramify_markdown failed: {e}")
            safe_text = formatted_text  # fallback nếu lỗi escape

        print(f"✅ Sending Markdown V2 message to {chat_id}")
        return self.send_telegram_message_v2(chat_id, safe_text, parse_mode="MarkdownV2")
    def send_long_message(self, chat_id: str | int, text: str, use_markdown: bool = True):
        MAX_LENGTH = 4000
        chunks = []
        current_chunk = ""

        formatted_text = self.format_telegram_message(text)
        sections = self.split_message_safely(formatted_text)

        for section in sections:
            if not section.strip():
                continue

            if len(current_chunk) + len(section) + 2 <= MAX_LENGTH:
                current_chunk += ('\n\n' if current_chunk else '') + section.strip()
            else:
                chunks.append(current_chunk)
                current_chunk = section.strip()

        if current_chunk:
            chunks.append(current_chunk)

        print(f"📚 Split message into {len(chunks)} chunk(s)")

        results = []
        for i, chunk in enumerate(chunks, 1):
            chunk_with_header = f"📄 Part {i}/{len(chunks)}:\n\n{chunk}"

            if use_markdown:
                try:
                    print(f"Sending chunk {i} with Markdown: {chunk_with_header[:20]}...")
                    result = self.send_markdown_v2(chat_id, chunk_with_header)
                    results.append(result)
                except Exception as e:
                    print(f"⚠️ Chunk {i} Markdown failed, using plain text: {e}")
                    result = self.send_message(chat_id, chunk_with_header)
                    results.append(result)
            else:
                result = self.send_message(chat_id, chunk_with_header)
                results.append(result)

            time.sleep(0.5)

        return results
    def split_message_safely(text: str, max_length: int = 4000) -> list[str]:
        """Tách message thành các phần <= max_length, không bị rỗng hoặc vỡ định dạng"""
        paragraphs = text.strip().split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_length:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                chunks.append(current_chunk)
                current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
    @staticmethod
    def format_telegram_message(text: str) -> str:
        """
        Tiền xử lý Markdown:
        - Chuyển **** thành ** để làm nổi bật
        - Định dạng giờ
        - Fix lỗi dấu * dư
        """
        text = re.sub(r'\*\*\*\*([^*]+)\*\*\*\*:', r'**\1**:', text)
        text = re.sub(r'(\d{1,2}:\d{2} [AP]M)\s*\n\s*\n', r'*\1*\n\n', text)
        text = re.sub(r'\*\*([^*]+)\*\*(\*+)\s*\n', r'**\1**\n', text)
        text = re.sub(r'(\*\*[^*]+\*\*)\*+$', r'\1', text)
        text = text.replace("**Lưu ý:**", "*Lưu ý:*")
        print(f"🔄 Formatted text: {text[:20]}...")  # Log first 100 chars for debugging
        return text
"""
 Telegram Service
"""
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

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        self.mode = os.getenv("MODE")

    async def run(self):
        if self.mode == "prod":
            await self.run_webhook()
        else:
            await self.run_polling()

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
        logger.info("Running Telegram bot in polling mode")
        try:
            app = ApplicationBuilder().token(self.bot_token).build()
            self.add_handlers(app)
            logger.info("🤖 Bot running in polling mode (dev)")
            await app.initialize() 
            await app.start()
            await app.updater.start_polling()
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
            user_settings = crud.get_users_setting_by_telegram_username(db, telegram_username=user_name)
            if not user_settings or len(user_settings) == 0:
                await self.send_telegram_message(chat_id, "❌ Account not found. Please rent bot first.")
                return {"ok": False}

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
                return await self.handle_start_command(chat_id, user_setting, db)
        except Exception as e:
            logger.error(f"Error handling Telegram message: {e}", exc_info=True)
            await self.send_telegram_message(chat_id, "❌ An error occurred while processing your request. Please try again later.")
            return {"ok": False, "error": str(e)}
    async def handle_start_command(self, chat_id: int, user_setting: models.UserSettings, db: Session):
        await self.send_telegram_message(chat_id, "✅ Welcome! You have successfully started the bot.")
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
import redis
import json
import os
import discord
import asyncio
import logging
from discord.ext import commands
import datetime

from discord.ui import View, Button
from core import crud, models
from core.database import SessionLocal

logger = logging.getLogger(__name__)

class PanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔔 Follow Bot", style=discord.ButtonStyle.success)
    async def follow_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)  # Trả lời ngay, giữ interaction sống
        user_id = str(interaction.user.id)
        username = f"{interaction.user.name}"
        try:
            logger.info(f"🔔 User {username} ({user_id}) clicked Follow Bot button")
            success, message = await self.handle_discord_subscription(user_id, username)

            if success:
                try:
                    await interaction.user.send(message)
                    await interaction.response.send_message("✅ Follow success! Check your DMs!", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Bot cannot send you a DM. Please enable DMs!", ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in follow_button: {e}")
            await interaction.response.send_message("❌ An error occurred. Please try again later.", ephemeral=True)
    async def handle_discord_subscription(self, user_id: str, username: str):
        with SessionLocal() as db:
            user = crud.get_user_setting_by_discord_username(db, username)
            if not user:
                return False, "❌ Account not found. Please rent bot first."
            if user.discord_user_id != user_id:
                user.discord_user_id = user_id
            db.commit()
            db.refresh(user)
            return True, "✅ You are now following the bot!"

class DiscordService:
    def __init__(self, token=None, intents=None, command_prefix="!"):
        self.token = token or os.getenv("DISCORD_BOT_TOKEN")
        self.intents = intents or discord.Intents.default()
        self.intents.message_content = True
        self.intents.guilds = True
        self.intents.members = True
        self.logger = logging.getLogger(__name__)
        self.bot = commands.Bot(command_prefix=command_prefix, intents=self.intents)
        self.add_default_handlers()

    def add_default_handlers(self):
        @self.bot.event
        async def on_ready():
            print(f"✅ Discord bot ready! Logged in as {self.bot.user}")

        @self.bot.command()
        async def start_panel(ctx):
            embed = discord.Embed(
                title="🤖 AI Trading Bot Marketplace",
                description="Welcome! Please **Follow Bot** to receive notifications for bot rentals.",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Bot by AI Team • Marketplace for Rent Bots")
            message = await ctx.send(embed=embed, view=PanelView())
            await message.pin(reason="Pinned start panel for new users")


    async def background_dm_worker(self):
        r = redis.Redis(host=os.getenv('REDIS_HOST', 'active-trading-redis-1'), port=int(os.getenv('REDIS_PORT', 6379)), db=0)
        while True:
            try:
                item = r.blpop('discord_dm_queue', timeout=5)
                if item:
                    _, data = item
                    payload = json.loads(data)
                    user_id = int(payload['user_id'])
                    message = payload['message']
                    await self.send_discord_dm_safe(user_id, message)
            except Exception as e:
                logger.error(f"Error in background_dm_worker: {e}")
            await asyncio.sleep(0.5)

    async def run(self):
        try:
            await asyncio.gather(
                self.bot.start(self.token),
                self.background_dm_worker()
            )
        except asyncio.CancelledError:
            print("🛑 Discord bot task cancelled.")
            await self.bot.close()

    async def close(self):
        await self.bot.close()


    async def send_discord_dm_safe(self, user_id: int, message: str):
        print(f"[{datetime.datetime.now(datetime.timezone.utc)}] ✅ Sending Discord DM")
        try:
            user = await self.bot.fetch_user(user_id)
            chunks = self.split_discord_message(message)

            for i, chunk in enumerate(chunks, 1):
                if len(chunks) > 1:
                    header = f"📄 Part {i}/{len(chunks)}:\n\n"
                    await user.send(header + chunk)
                else:
                    await user.send(chunk)

                await asyncio.sleep(0.5)

            return True
        except Exception as e:
            print(f"❌ Error sending Discord DM: {e}")
            logger.error(f"Failed to send Discord DM: {e}")
            return False

    def split_discord_message(self, text: str, max_length: int = 2000) -> list:
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

    def add_command(self, *args, **kwargs):
        return self.bot.command(*args, **kwargs)

    def add_event(self, func):
        return self.bot.event(func)
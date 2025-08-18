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
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=300)  # 5 minutes timeout instead of None
        self.bot = bot

    @discord.ui.button(label="🔔 Follow Bot", style=discord.ButtonStyle.success)
    async def follow_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        username = f"{interaction.user.name}"
        
        try:
            logger.info(f"🔔 User {username} ({user_id}) clicked Follow Bot button")
            
            # Respond immediately to prevent interaction timeout
            await interaction.response.send_message("⏳ Processing your request...", ephemeral=True)
            
            success, message = await self.handle_discord_subscription(user_id, username)

            if success:
                try:
                    await interaction.user.send(message)
                    await interaction.followup.send("✅ Follow success! Check your DMs!", ephemeral=True)
                except discord.Forbidden:
                    await interaction.followup.send("❌ Bot cannot send you a DM. Please enable DMs!", ephemeral=True)
            else:
                await interaction.followup.send(message, ephemeral=True)
                
        except discord.errors.NotFound:
            # Interaction already expired, try to send DM directly
            try:
                success, message = await self.handle_discord_subscription(user_id, username)
                if success:
                    user = await self.bot.fetch_user(int(user_id))
                    await user.send(message)
                    logger.info(f"Sent followup DM to {username} due to expired interaction")
                else:
                    logger.error(f"Failed to handle subscription for {username}: {message}")
            except Exception as e:
                logger.error(f"Error sending followup DM: {e}")
        except Exception as e:
            logger.error(f"Error in follow_button: {e}")
            try:
                await interaction.followup.send("❌ An error occurred. Please try again later.", ephemeral=True)
            except:
                # If followup also fails, just log the error
                logger.error(f"Could not send error message to user {username}")
    async def handle_discord_subscription(self, user_id: str, username: str):
        try:
            with SessionLocal() as db:
                user = crud.get_user_setting_by_discord_username(db, username)
                if not user:
                    return False, "❌ Account not found. Please rent bot first."
                
                # Update discord_user_id if different
                if user.discord_user_id != user_id:
                    user.discord_user_id = user_id
                    db.commit()
                    db.refresh(user)
                
                return True, "✅ You are now following the bot! You'll receive notifications about bot rentals."
        except Exception as e:
            logger.error(f"Error in handle_discord_subscription: {e}")
            return False, "❌ Database error occurred. Please try again later."

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
            try:
                embed = discord.Embed(
                    title="🤖 AI Trading Bot Marketplace",
                    description="Welcome! Please **Follow Bot** to receive notifications for bot rentals.",
                    color=discord.Color.blue()
                )
                embed.set_footer(text="Bot by AI Team • Marketplace for Rent Bots")
                
                # Create view with timeout
                view = PanelView()
                message = await ctx.send(embed=embed, view=view)
                
                # Try to pin the message
                try:
                    await message.pin(reason="Pinned start panel for new users")
                except discord.Forbidden:
                    logger.warning(f"Cannot pin message in channel {ctx.channel.name} - missing permissions")
                except Exception as e:
                    logger.error(f"Error pinning message: {e}")
                    
            except Exception as e:
                logger.error(f"Error in start_panel command: {e}")
                await ctx.send("❌ An error occurred while creating the panel. Please try again.")


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
            # Create tasks for bot and background worker
            bot_task = asyncio.create_task(self.bot.start(self.token))
            worker_task = asyncio.create_task(self.background_dm_worker())
            
            # Wait for both tasks
            await asyncio.gather(bot_task, worker_task)
        except asyncio.CancelledError:
            print("🛑 Discord bot task cancelled.")
            await self.bot.close()
        except Exception as e:
            print(f"❌ Error in Discord service: {e}")
            await self.bot.close()

    async def stop(self):
        """Stop the Discord bot gracefully"""
        try:
            await self.bot.close()
        except Exception as e:
            self.logger.error(f"Error stopping Discord bot: {e}")

    async def close(self):
        await self.stop()


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
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
from core.tasks import run_bot_signal_logic, run_bot_logic
import discord.errors

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
            await interaction.response.defer(thinking=True, ephemeral=True)
            logger.info(f"🔔 User {username} ({user_id}) clicked Follow Bot button")
            
            # Respond immediately to prevent interaction timeout
            # await interaction.followup.send("⏳ Processing your request...", ephemeral=True)
            
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
                user_settings = crud.get_users_setting_by_discord_username(db, username)
                if not user_settings or len(user_settings) == 0:
                    return False, "❌ Account not found. Please rent bot first."
                
                updated = False
                for user_setting in user_settings:
                    if user_setting.discord_user_id != user_id:
                        user_setting.discord_user_id = user_id
                        updated = True
                        logger.info(f"📱 Updated discord_user_id for user {username}: {user_id}")
                if updated:
                    db.commit()
                    for user_setting in user_settings:
                        db.refresh(user_setting)
                
                return True, "✅ You are now following the bot! You'll receive notifications about bot rentals."
        except Exception as e:
            logger.error(f"Error in handle_discord_subscription: {e}")
            return False, "❌ Database error occurred. Please try again later."

class ManualSignalsPanelView(View):
    @discord.ui.button(label="🔍 View All Bots Passive", style=discord.ButtonStyle.primary)
    async def view_all_bots(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            with SessionLocal() as db:
                user_id = str(interaction.user.id)
                username = f"{interaction.user.name}"

                logger.info(f"ManualSignalsPanelView with user: {username}")

                # Gọi DB để lấy danh sách bot mà user đã thuê
                user_settings = crud.get_users_setting_by_discord_username(db, username)
                if not user_settings or len(user_settings) == 0:
                    await interaction.followup.send("❌ Account not found. Please rent bot first.", ephemeral=True)
                    return

                updated = False
                for user_setting in user_settings:
                    if user_setting.discord_user_id != user_id:
                        user_setting.discord_user_id = user_id
                        updated = True
                        logger.info(f"📱 Updated discord_user_id for user {username}: {user_id}")
                if updated:
                    db.commit()
                    for user_setting in user_settings:
                        db.refresh(user_setting)

                if user_settings:
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
                                    "principal_prefix": principal_prefix,
                                    "bot_mode": bot.bot.bot_mode # passive bot mode
                                })

                if not bots:
                    await interaction.followup.send("❌ You don't have any rented bots.", ephemeral=True)
                    return

                view = BotListView(bots)
                await interaction.followup.send("🤖 List of your rented bots:", view=view, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in view_all_bots: {e}")
            try:
                await interaction.followup.send("❌ An error occurred. Please try again later.", ephemeral=True)
            except:
                # If interaction is completely expired, log the error
                logger.error("Could not send error message to user due to expired interaction")

class ManualActivePanelView(View):
    @discord.ui.button(label="🔍 View All Bots Active", style=discord.ButtonStyle.primary)
    async def view_all_bots(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            with SessionLocal() as db:
                user_id = str(interaction.user.id)
                username = f"{interaction.user.name}"

                logger.info(f"ManualActivePanelView with user: {username}")

                # Query user settings
                user_settings = crud.get_users_setting_by_discord_username(db, username)
                if not user_settings or len(user_settings) == 0:
                    await interaction.followup.send("❌ Account not found. Please rent bot first.", ephemeral=True)
                    return

                updated = False
                for user_setting in user_settings:
                    if user_setting.discord_user_id != user_id:
                        user_setting.discord_user_id = user_id
                        updated = True
                        logger.info(f"📱 Updated discord_user_id for user {username}: {user_id}")
                if updated:
                    db.commit()
                    for user_setting in user_settings:
                        db.refresh(user_setting)

                bots = []
                for user_setting in user_settings:
                    bot_list = crud.get_all_subscription_by_principal_id(db, principal_id=user_setting.principal_id, bot_mode='ACTIVE')
                    for bot in bot_list:
                        rent_date = getattr(bot, "started_at", None)
                        rent_date_str = rent_date.strftime("%d/%m %H:%M") if rent_date else "N/A"
                        principal_prefix = str(user_setting.principal_id)[:5]

                        bots.append({
                            "bot_name": bot.bot.name,
                            "bot_id": bot.bot.id,
                            "sub_id": bot.id,
                            "rent_date": rent_date_str,
                            "principal_prefix": principal_prefix,
                            "bot_mode": bot.bot.bot_mode
                        })

                if not bots:
                    await interaction.followup.send("❌ You don't have any rented bots.", ephemeral=True)
                    return

                view = BotListView(bots)
                await interaction.followup.send("🤖 List of your rented bots:", view=view, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in view_all_bots: {e}")
            try:
                await interaction.followup.send("❌ An error occurred. Please try again later.", ephemeral=True)
            except:
                # If interaction is completely expired, log the error
                logger.error("Could not send error message to user due to expired interaction")

class BotListView(View):
    def __init__(self, bots: list[dict]):
        super().__init__(timeout=300)
        for bot_info in bots:
            self.add_item(RunBotButton(bot_info))

class RunBotButton(Button):
    def __init__(self, bot_info):
        self.bot_id = bot_info["bot_id"]
        self.subs_id = bot_info["sub_id"]
        self.bot_name = bot_info["bot_name"]
        self.rent_date = bot_info["rent_date"]
        self.principal_prefix = bot_info["principal_prefix"]
        self.bot_mode = bot_info["bot_mode"]
        label = f"▶️ {bot_info['bot_name']}-{bot_info['principal_prefix']}-{bot_info['rent_date']}"
        super().__init__(label=label, style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)
            user_id = str(interaction.user.id)
            discord_username = str(interaction.user.name)
            if self.bot_mode == "PASSIVE":
                logger.info(f"trigger celery run_bot_signal_logic for {discord_username}")
                run_bot_signal_logic.delay(self.bot_id, self.subs_id)
            else:
                logger.info(f"trigger celery run_bot_logic for {discord_username}")
                run_bot_logic.delay(self.subs_id)

            await interaction.followup.send(f"🚀 Running bot `{self.bot_name}`...", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in RunBotButton callback: {e}")
            await interaction.followup.send("❌ An error occurred while starting the bot. Please try again later.", ephemeral=True)

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
                general_channel = discord.utils.get(ctx.guild.text_channels, name="general")
                if not general_channel:
                    await ctx.send("❌ Not found # 'general'")
                    return
                embed = discord.Embed(
                    title="🤖 AI Trading Bot Marketplace",
                    description="Welcome! Please **Follow Bot** to receive notifications for bot rentals.",
                    color=discord.Color.blue()
                )
                embed.set_footer(text="Bot by AI Team • Marketplace for Rent Bots")
                
                # Create view with timeout
                # view = PanelView(self.bot)
                message = await general_channel.send(embed=embed, view=PanelView(self.bot))
                
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
        @self.bot.command()
        async def manual_signals_panel(ctx):
            manual_channel = discord.utils.get(ctx.guild.text_channels, name="manual-passive")

            if not manual_channel:
                await ctx.send("❌ Not found # 'manual-passive'")
                return

            embed = discord.Embed(
                title="⚙️ Manual Bot Control",
                description="Click **View All Bots** to see and start the bots you have rented.",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Manual Bot Control • Only you can see your bots")
            await manual_channel.send(embed=embed, view=ManualSignalsPanelView())
        @self.bot.command()
        async def manual_active_panel(ctx):
            manual_channel = discord.utils.get(ctx.guild.text_channels, name="manual-active")

            if not manual_channel:
                await ctx.send("❌ Not found # 'manual-active'")
                return

            embed = discord.Embed(
                title="⚙️ Manual Bot Control",
                description="Click **View All Bots** to see and start the bots you have rented.",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Manual Bot Control • Only you can see your bots")
            await manual_channel.send(embed=embed, view=ManualActivePanelView())


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
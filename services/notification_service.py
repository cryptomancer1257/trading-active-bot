"""
Notification Service - Send trading signals via Telegram/Discord
Reusable service for any trading bot to send notifications
"""

import os
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Supported notification channels"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"  # Future support


class SignalType(Enum):
    """Types of trading signals"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE = "CLOSE"
    ALERT = "ALERT"
    INFO = "INFO"


class NotificationService(ABC):
    """Abstract base class for notification services"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize notification service
        
        Args:
            config: Service configuration
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
    
    @abstractmethod
    async def send_signal(
        self, 
        signal_type: SignalType,
        symbol: str,
        data: Dict[str, Any],
        user_config: Dict[str, Any] = None
    ) -> bool:
        """
        Send trading signal notification
        
        Args:
            signal_type: Type of signal (BUY/SELL/HOLD)
            symbol: Trading pair (e.g., BTCUSDT)
            data: Signal data (price, confidence, reasoning, etc.)
            user_config: User-specific configuration (chat_id, channel_id, etc.)
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    async def send_alert(
        self,
        title: str,
        message: str,
        user_config: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> bool:
        """
        Send general alert/notification
        
        Args:
            title: Alert title
            message: Alert message
            user_config: User-specific configuration
            priority: Priority level (low/normal/high/urgent)
            
        Returns:
            bool: Success status
        """
        pass
    
    def _format_signal_message(
        self,
        signal_type: SignalType,
        symbol: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Format signal data into readable message
        
        Args:
            signal_type: Signal type
            symbol: Trading pair
            data: Signal data
            
        Returns:
            str: Formatted message
        """
        emoji_map = {
            SignalType.BUY: "🟢",
            SignalType.SELL: "🔴",
            SignalType.HOLD: "🟡",
            SignalType.CLOSE: "⚪",
            SignalType.ALERT: "⚠️",
            SignalType.INFO: "ℹ️"
        }
        
        emoji = emoji_map.get(signal_type, "📊")
        
        # Extract data
        exchange = data.get('exchange', 'N/A')
        confidence = data.get('confidence', 0)
        entry_price = data.get('entry_price', 'Market')
        stop_loss = data.get('stop_loss', 'N/A')
        take_profit = data.get('take_profit', 'N/A')
        risk_reward = data.get('risk_reward', 'N/A')
        reasoning = data.get('reasoning', 'No reasoning provided')
        strategy = data.get('strategy', 'N/A')
        timeframe = data.get('timeframe', 'N/A')
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Build message
        message = f"{emoji} **{signal_type.value} SIGNAL - {symbol}**\n\n"
        message += f"**Exchange:** {exchange}\n"
        message += f"**Timeframe:** {timeframe}\n"
        message += f"**Confidence:** {confidence}%\n\n"
        
        if signal_type in [SignalType.BUY, SignalType.SELL]:
            message += f"**Entry Price:** {entry_price}\n"
            message += f"**Stop Loss:** {stop_loss}\n"
            message += f"**Take Profit:** {take_profit}\n"
            message += f"**Risk/Reward:** {risk_reward}\n"
            message += f"**Strategy:** {strategy}\n\n"
        
        message += f"**Analysis:**\n{reasoning}\n\n"
        message += f"⏰ {timestamp}"
        
        return message


class TelegramNotificationService(NotificationService):
    """Telegram notification service implementation"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Telegram service
        
        Args:
            config: Configuration with bot_token
        """
        super().__init__(config)
        self.bot_token = config.get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not self.bot_token:
            logger.warning("⚠️ Telegram bot token not configured")
            self.enabled = False
        else:
            logger.info("✅ Telegram notification service initialized")
    
    async def send_signal(
        self,
        signal_type: SignalType,
        symbol: str,
        data: Dict[str, Any],
        user_config: Dict[str, Any] = None
    ) -> bool:
        """Send trading signal via Telegram"""
        if not self.enabled:
            logger.warning("Telegram service disabled")
            return False
        
        try:
            # Get user's chat_id
            chat_id = None
            if user_config:
                chat_id = user_config.get('telegram_chat_id')
            
            if not chat_id:
                logger.warning("No Telegram chat_id provided")
                return False
            
            # Format message
            message = self._format_signal_message(signal_type, symbol, data)
            
            # Send via Telegram API
            import aiohttp
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"✅ Telegram signal sent: {signal_type.value} {symbol}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Telegram API error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram signal: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def send_alert(
        self,
        title: str,
        message: str,
        user_config: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> bool:
        """Send alert via Telegram"""
        if not self.enabled:
            return False
        
        try:
            chat_id = user_config.get('telegram_chat_id') if user_config else None
            if not chat_id:
                return False
            
            # Priority emoji
            emoji_map = {
                'low': 'ℹ️',
                'normal': '📢',
                'high': '⚠️',
                'urgent': '🚨'
            }
            emoji = emoji_map.get(priority, '📢')
            
            formatted_message = f"{emoji} **{title}**\n\n{message}"
            
            import aiohttp
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                'chat_id': chat_id,
                'text': formatted_message,
                'parse_mode': 'Markdown'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False


class DiscordNotificationService(NotificationService):
    """Discord notification service implementation"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Discord service
        
        Args:
            config: Configuration with webhook_url or bot_token
        """
        super().__init__(config)
        # Discord can use webhooks (easier) or bot API
        self.webhook_url = config.get('webhook_url') or os.getenv('DISCORD_WEBHOOK_URL')
        
        if not self.webhook_url:
            logger.warning("⚠️ Discord webhook URL not configured")
            self.enabled = False
        else:
            logger.info("✅ Discord notification service initialized")
    
    async def send_signal(
        self,
        signal_type: SignalType,
        symbol: str,
        data: Dict[str, Any],
        user_config: Dict[str, Any] = None
    ) -> bool:
        """Send trading signal via Discord webhook"""
        if not self.enabled:
            logger.warning("Discord service disabled")
            return False
        
        try:
            # Get user's webhook URL (can override default)
            webhook_url = self.webhook_url
            if user_config and user_config.get('discord_webhook_url'):
                webhook_url = user_config['discord_webhook_url']
            
            if not webhook_url:
                logger.warning("No Discord webhook URL provided")
                return False
            
            # Format message for Discord
            message = self._format_signal_message(signal_type, symbol, data)
            
            # Convert Markdown to Discord format (similar but ** is bold, __ is underline)
            # Discord uses same markdown style, so we're good
            
            # Color based on signal type
            color_map = {
                SignalType.BUY: 0x00FF00,      # Green
                SignalType.SELL: 0xFF0000,     # Red
                SignalType.HOLD: 0xFFFF00,     # Yellow
                SignalType.CLOSE: 0x808080,    # Gray
                SignalType.ALERT: 0xFFA500,    # Orange
                SignalType.INFO: 0x0099FF      # Blue
            }
            
            color = color_map.get(signal_type, 0x0099FF)
            
            # Discord embed format
            embed = {
                'title': f'{signal_type.value} Signal - {symbol}',
                'description': message,
                'color': color,
                'timestamp': datetime.now().isoformat(),
                'footer': {
                    'text': f'QuantumForge Trading Signals - {data.get("exchange", "N/A")}'
                }
            }
            
            payload = {
                'embeds': [embed]
            }
            
            # Send via Discord webhook
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status in [200, 204]:
                        logger.info(f"✅ Discord signal sent: {signal_type.value} {symbol}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Discord webhook error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Failed to send Discord signal: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def send_alert(
        self,
        title: str,
        message: str,
        user_config: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> bool:
        """Send alert via Discord webhook"""
        if not self.enabled:
            return False
        
        try:
            webhook_url = self.webhook_url
            if user_config and user_config.get('discord_webhook_url'):
                webhook_url = user_config['discord_webhook_url']
            
            if not webhook_url:
                return False
            
            # Color based on priority
            color_map = {
                'low': 0x808080,      # Gray
                'normal': 0x0099FF,   # Blue
                'high': 0xFFA500,     # Orange
                'urgent': 0xFF0000    # Red
            }
            color = color_map.get(priority, 0x0099FF)
            
            embed = {
                'title': title,
                'description': message,
                'color': color,
                'timestamp': datetime.now().isoformat()
            }
            
            payload = {'embeds': [embed]}
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    return response.status in [200, 204]
                    
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False


class NotificationManager:
    """
    Notification manager to handle multiple channels
    Sends notifications to all configured channels
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize notification manager
        
        Args:
            config: Configuration for all channels
                {
                    'telegram': {'bot_token': '...', 'enabled': True},
                    'discord': {'webhook_url': '...', 'enabled': True}
                }
        """
        self.config = config or {}
        self.services: List[NotificationService] = []
        
        # Initialize services based on config
        if self.config.get('telegram', {}).get('enabled', True):
            try:
                telegram_service = TelegramNotificationService(self.config.get('telegram', {}))
                if telegram_service.enabled:
                    self.services.append(telegram_service)
            except Exception as e:
                logger.warning(f"Failed to initialize Telegram service: {e}")
        
        if self.config.get('discord', {}).get('enabled', True):
            try:
                discord_service = DiscordNotificationService(self.config.get('discord', {}))
                if discord_service.enabled:
                    self.services.append(discord_service)
            except Exception as e:
                logger.warning(f"Failed to initialize Discord service: {e}")
        
        logger.info(f"📢 Notification manager initialized with {len(self.services)} service(s)")
    
    async def send_signal(
        self,
        signal_type: SignalType,
        symbol: str,
        data: Dict[str, Any],
        user_config: Dict[str, Any] = None
    ) -> Dict[str, bool]:
        """
        Send signal to all configured channels
        
        Returns:
            Dict with results for each channel
        """
        results = {}
        
        tasks = []
        for service in self.services:
            task = service.send_signal(signal_type, symbol, data, user_config)
            tasks.append((service.__class__.__name__, task))
        
        # Send to all channels concurrently
        for service_name, task in tasks:
            try:
                success = await task
                results[service_name] = success
            except Exception as e:
                logger.error(f"Error sending via {service_name}: {e}")
                results[service_name] = False
        
        return results
    
    async def send_alert(
        self,
        title: str,
        message: str,
        user_config: Dict[str, Any] = None,
        priority: str = "normal"
    ) -> Dict[str, bool]:
        """Send alert to all configured channels"""
        results = {}
        
        tasks = []
        for service in self.services:
            task = service.send_alert(title, message, user_config, priority)
            tasks.append((service.__class__.__name__, task))
        
        for service_name, task in tasks:
            try:
                success = await task
                results[service_name] = success
            except Exception as e:
                logger.error(f"Error sending alert via {service_name}: {e}")
                results[service_name] = False
        
        return results


# Factory function for easy initialization
def create_notification_service(
    channels: List[NotificationChannel],
    config: Dict[str, Any] = None
) -> NotificationManager:
    """
    Create notification manager with specified channels
    
    Args:
        channels: List of channels to enable (TELEGRAM, DISCORD, etc.)
        config: Configuration for each channel
        
    Returns:
        NotificationManager instance
    
    Example:
        ```python
        config = {
            'telegram': {'bot_token': 'xxx'},
            'discord': {'webhook_url': 'yyy'}
        }
        notifier = create_notification_service(
            [NotificationChannel.TELEGRAM, NotificationChannel.DISCORD],
            config
        )
        ```
    """
    if not config:
        config = {}
    
    # Enable only specified channels
    for channel in NotificationChannel:
        if channel not in channels:
            if channel.value in config:
                config[channel.value]['enabled'] = False
    
    return NotificationManager(config)


if __name__ == "__main__":
    # Example usage
    async def test_notifications():
        config = {
            'telegram': {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'enabled': True
            },
            'discord': {
                'webhook_url': os.getenv('DISCORD_WEBHOOK_URL'),
                'enabled': True
            }
        }
        
        manager = NotificationManager(config)
        
        # Test signal
        signal_data = {
            'exchange': 'BINANCE',
            'confidence': 85,
            'entry_price': '50000',
            'stop_loss': '49000',
            'take_profit': '52000',
            'risk_reward': '1:2',
            'reasoning': 'Strong bullish momentum with RSI oversold confirmation',
            'strategy': 'LLM Multi-timeframe Analysis',
            'timeframe': '1h',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        user_config = {
            'telegram_chat_id': '123456789',  # Replace with real chat_id
            'discord_webhook_url': 'https://discord.com/api/webhooks/...'  # Replace
        }
        
        results = await manager.send_signal(
            SignalType.BUY,
            'BTC/USDT',
            signal_data,
            user_config
        )
        
        print("Notification results:", results)
    
    # Run test
    # asyncio.run(test_notifications())
    print("✅ Notification Service Module Loaded")
    print("   - TelegramNotificationService")
    print("   - DiscordNotificationService")
    print("   - NotificationManager")


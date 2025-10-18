"""
Universal Futures Signals Bot - Multi-Exchange Signal Provider
Supports: Binance, Bybit, OKX, Bitget, Huobi/HTX, Kraken

Trading signals bot with:
- LLM AI analysis (OpenAI/Claude/Gemini)
- Multi-timeframe analysis
- Signal generation (BUY/SELL/HOLD)
- Telegram/Discord notifications
- NO actual trading execution (signals only)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
import json
import hashlib
import time
import asyncio
import redis
from datetime import datetime

# Bot SDK imports
from bots.bot_sdk import CustomBot, Action

# Exchange integrations (for data crawling only, no trading)
from services.exchange_integrations import create_futures_exchange

# Services
from services.llm_integration import create_llm_service
from services.notification_service import (
    NotificationManager,
    NotificationChannel,
    SignalType,
    create_notification_service
)

logger = logging.getLogger(__name__)


class UniversalFuturesSignalsBot(CustomBot):
    """Universal Futures Signals Bot - Analysis and Notification Only"""
    
    SUPPORTED_EXCHANGES = ['BINANCE', 'BYBIT', 'OKX', 'BITGET', 'HUOBI', 'HTX', 'KRAKEN']
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str] = None,
                 user_principal_id: str = None, subscription_id: int = None):
        """
        Initialize Universal Futures Signals Bot
        
        Args:
            config: Bot configuration including:
                - exchange: Exchange name (BINANCE, BYBIT, OKX, BITGET, HUOBI, KRAKEN)
                - trading_pair: Trading pair (e.g., 'BTCUSDT')
                - timeframes: List of timeframes for analysis (default: ['30m', '1h', '4h'])
                - use_llm_analysis: Enable LLM analysis (default: True)
                - llm_model: LLM model to use (default: 'openai')
                - notification_channels: List of channels ['telegram', 'discord']
                - telegram_config: Telegram bot configuration
                - discord_config: Discord webhook configuration
            api_keys: LLM API keys (optional)
            user_principal_id: User principal ID
            subscription_id: Subscription ID
        """
        super().__init__(config, api_keys)
        
        # Bot identification
        self.bot_id = config.get('bot_id')
        self.subscription_id = subscription_id
        logger.info(f"🤖 [SIGNALS BOT INIT] bot_id={self.bot_id}, subscription_id={subscription_id}")
        
        # Exchange configuration
        self.exchange_name = (
            config.get('exchange_type') or
            config.get('exchange') or
            'BINANCE'
        ).upper()
        
        if self.exchange_name not in self.SUPPORTED_EXCHANGES:
            raise ValueError(
                f"Unsupported exchange: {self.exchange_name}. "
                f"Supported: {', '.join(self.SUPPORTED_EXCHANGES)}"
            )
        
        logger.info(f"🌐 Signals Bot - Exchange: {self.exchange_name}")
        
        # Trading configuration
        raw_trading_pair = config.get('trading_pair', 'BTCUSDT')
        self.trading_pair = raw_trading_pair.replace('/', '')
        logger.info(f"🎯 Bot initialized with trading_pair: {self.trading_pair} (from config: {config.get('trading_pair', 'NOT_PROVIDED')})")
        
        # Multi-timeframe configuration
        self.timeframes = config.get('timeframes', ['30m', '1h', '4h'])
        self.primary_timeframe = config.get('primary_timeframe', self.timeframes[0])
        
        # Validate timeframes
        supported_timeframes = [
            '1m', '3m', '5m', '15m', '30m',
            '1h', '2h', '4h', '6h', '8h', '12h',
            '1d', '3d', '1w', '1M'
        ]
        
        valid_timeframes = [tf for tf in self.timeframes if tf in supported_timeframes]
        if len(valid_timeframes) != len(self.timeframes):
            invalid_tfs = [tf for tf in self.timeframes if tf not in supported_timeframes]
            logger.warning(f"Unsupported timeframes removed: {invalid_tfs}")
        
        self.timeframes = valid_timeframes if valid_timeframes else ['1h']
        
        if self.primary_timeframe not in self.timeframes:
            self.primary_timeframe = self.timeframes[0]
            logger.warning(f"Primary timeframe adjusted to: {self.primary_timeframe}")
        
        # LLM configuration
        self.llm_model = config.get('llm_model', 'openai')
        self.use_llm_analysis = config.get('use_llm_analysis', True)
        
        # Technical indicators config (fallback)
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        
        # Redis for distributed locking
        self.redis_client = None
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://redis_db:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis_client = None
        
        # Initialize exchange client for data crawling (public API, no credentials needed)
        try:
            # For signals bot, we only need public market data
            # No need for API keys (will use empty strings for public endpoints)
            self.futures_client = create_futures_exchange(
                exchange_name=self.exchange_name,
                api_key="",  # Empty for public data
                api_secret="",
                passphrase="",
                testnet=False  # Always use mainnet for accurate data
            )
            logger.info(f"✅ {self.exchange_name} public client initialized (data only)")
        except Exception as e:
            logger.error(f"Failed to initialize {self.exchange_name} client: {e}")
            raise
        
        # Initialize LLM service
        self.llm_service = None
        if self.use_llm_analysis:
            try:
                developer_id = config.get('developer_id')
                db = config.get('db')
                bot_id = config.get('bot_id')
                
                preferred_provider = config.get('llm_provider')
                llm_model = config.get('llm_model')
                
                if preferred_provider:
                    logger.info(f"🎯 Bot configured to use LLM provider: {preferred_provider}")
                if llm_model:
                    logger.info(f"🎯 Bot configured to use specific model: {llm_model}")
                
                if not llm_model and preferred_provider:
                    llm_model = preferred_provider
                    logger.info(f"ℹ️  No specific model configured, using provider: {preferred_provider}")
                
                llm_config = {
                    'openai_api_key': os.getenv('OPENAI_API_KEY'),
                    'claude_api_key': os.getenv('CLAUDE_API_KEY'),
                    'gemini_api_key': os.getenv('GEMINI_API_KEY'),
                    'openai_model': config.get('openai_model', 'gpt-4o'),
                    'claude_model': config.get('claude_model', 'claude-3-5-sonnet-20241022'),
                    'gemini_model': config.get('gemini_model', 'gemini-2.5-flash')
                }
                
                if llm_model:
                    if preferred_provider == 'openai':
                        llm_config['openai_model'] = llm_model
                    elif preferred_provider in ['anthropic', 'claude']:
                        llm_config['claude_model'] = llm_model
                    elif preferred_provider == 'gemini':
                        llm_config['gemini_model'] = llm_model
                
                self.llm_service = create_llm_service(
                    config=llm_config,
                    developer_id=developer_id,
                    db=db,
                    preferred_provider=preferred_provider,
                    bot_id=bot_id
                )
                
                logger.info(f"✅ LLM service initialized for signals bot")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize LLM service: {e}")
                import traceback
                traceback.print_exc()
                self.use_llm_analysis = False
                logger.warning("⚠️  Falling back to traditional technical analysis")
        
        # Initialize Notification Manager
        notification_config = config.get('notification_config', {})
        
        # Telegram configuration
        telegram_config = notification_config.get('telegram', {})
        if not telegram_config.get('bot_token'):
            telegram_config['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # Discord configuration
        discord_config = notification_config.get('discord', {})
        if not discord_config.get('webhook_url'):
            discord_config['webhook_url'] = os.getenv('DISCORD_WEBHOOK_URL')
        
        # Build notification config
        self.notification_config = {
            'telegram': telegram_config,
            'discord': discord_config
        }
        
        # Get user's notification preferences
        self.user_notification_config = config.get('user_notification_config', {})
        
        # Initialize notification manager
        try:
            self.notification_manager = NotificationManager(self.notification_config)
            logger.info(f"✅ Notification manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize notification manager: {e}")
            self.notification_manager = None
        
        logger.info(f"✅ Universal Futures Signals Bot initialized")
        logger.info(f"   Exchange: {self.exchange_name}")
        logger.info(f"   Trading Pair: {self.trading_pair}")
        logger.info(f"   Timeframes: {self.timeframes}")
        logger.info(f"   LLM Analysis: {'Enabled (' + self.llm_model + ')' if self.use_llm_analysis else 'Disabled'}")
        logger.info(f"   Notification: {'Enabled' if self.notification_manager else 'Disabled'}")
    
    # ==================== MAIN EXECUTION METHOD ====================
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Main execution method - generates signals and sends notifications
        
        Flow:
        1. Crawl multi-timeframe data
        2. Analyze data with LLM/technical indicators
        3. Generate trading signal
        4. Send notification to user
        5. Return action
        
        Args:
            data: Historical price data (not used, we crawl fresh data)
            timeframe: Primary timeframe for analysis
            subscription_config: Additional configuration from subscription
            
        Returns:
            Action: Trading action (BUY/SELL/HOLD)
        """
        try:
            logger.info(f"🚀 [SIGNALS BOT] Starting analysis for {self.trading_pair}")
            logger.info(f"   Exchange: {self.exchange_name}")
            logger.info(f"   Timeframes: {self.timeframes}")
            
            # Step 1: Crawl fresh multi-timeframe data
            multi_timeframe_data = self.crawl_data()
            if not multi_timeframe_data or 'timeframes' not in multi_timeframe_data:
                logger.error("Failed to crawl data")
                return Action.HOLD
            
            # Step 2: Analyze data with LLM or technical indicators
            analysis = self.analyze_data(multi_timeframe_data)
            if not analysis:
                logger.error("Failed to analyze data")
                return Action.HOLD
            
            # Step 3: Generate trading signal
            signal = self.generate_signal(analysis)
            
            # Step 4: Send notification if signal is actionable
            if signal.action in ['BUY', 'SELL'] and self.notification_manager:
                logger.info(f"📢 [SIGNALS BOT] Sending {signal.action} notification...")
                asyncio.create_task(self._send_signal_notification(signal, analysis))
            elif signal.action == 'HOLD':
                logger.info(f"📢 [SIGNALS BOT] HOLD signal - no notification sent")
            elif not self.notification_manager:
                logger.warning(f"📢 [SIGNALS BOT] Notification manager not available")
            
            logger.info(f"✅ [SIGNALS BOT] Completed - Signal: {signal.name}")
            return signal
            
        except Exception as e:
            logger.error(f"❌ [SIGNALS BOT] Error: {e}")
            import traceback
            traceback.print_exc()
            return Action.HOLD
    
    async def setup_position(self, action: Action, confirmation: Any = None, subscription: Any = None) -> Dict[str, Any]:
        """
        Override setup_position to SKIP trade execution for signals-only bot
        This bot only sends signals, does NOT execute trades
        """
        logger.info(f"📡 [SIGNALS BOT] Skipping trade execution - this is a signals-only bot")
        logger.info(f"   Signal: {action.action} @ confidence {action.value * 100:.1f}%")
        logger.info(f"   Reason: {action.reason}")
        
        return {
            'status': 'skipped',
            'reason': 'Signals-only bot - no trade execution',
            'signal': action.action,
            'confidence': action.value
        }
    
    async def _send_signal_notification(self, signal: Action, analysis: Dict[str, Any]):
        """Send signal notification to user via configured channels"""
        try:
            logger.info(f"📢 [SIGNALS BOT] Preparing notification for {signal.action} signal...")
            
            # Map Action to SignalType
            signal_type_map = {
                'BUY': SignalType.BUY,
                'SELL': SignalType.SELL,
                'HOLD': SignalType.HOLD
            }
            
            signal_type = signal_type_map.get(signal.action, SignalType.HOLD)
            
            # Extract recommendation details
            recommendation = signal.recommendation or {}
            
            # Build signal data for notification
            signal_data = {
                'exchange': self.exchange_name,
                'confidence': int(signal.value * 100),
                'entry_price': recommendation.get('entry_price', 'Market'),
                'stop_loss': recommendation.get('stop_loss', 'N/A'),
                'take_profit': recommendation.get('take_profit', 'N/A'),
                'risk_reward': recommendation.get('risk_reward', 'N/A'),
                'market_volatility': recommendation.get('market_volatility', 'MEDIUM'),
                'reasoning': signal.reason,
                'strategy': recommendation.get('strategy', 'Multi-timeframe Analysis'),
                'timeframe': self.primary_timeframe,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"📢 [SIGNALS BOT] Signal data: {signal_data}")
            logger.info(f"📢 [SIGNALS BOT] User config: {self.user_notification_config}")
            
            # Send notification
            results = await self.notification_manager.send_signal(
                signal_type=signal_type,
                symbol=self.trading_pair.replace('/', '/'),  # Format: BTC/USDT
                data=signal_data,
                user_config=self.user_notification_config
            )
            
            logger.info(f"📢 [SIGNALS BOT] Notification sent: {results}")
            
        except Exception as e:
            logger.error(f"❌ [SIGNALS BOT] Failed to send signal notification: {e}")
            import traceback
            traceback.print_exc()
    
    # ==================== LLM CACHING & LOCKING ====================
    
    def _get_llm_cache_key(self, symbol: str, timeframes: List[str]) -> str:
        """Generate cache key for LLM analysis"""
        current_minute = int(time.time() // 60)
        key_data = f"{symbol}:{':'.join(sorted(timeframes))}:{current_minute}"
        return f"llm_analysis:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def _get_llm_lock_key(self, symbol: str) -> str:
        """Generate lock key for LLM analysis"""
        return f"llm_lock:{symbol}"
    
    def _acquire_llm_lock(self, symbol: str, timeout: int = 300) -> bool:
        """Acquire distributed lock for LLM analysis"""
        if not self.redis_client:
            return True
        
        lock_key = self._get_llm_lock_key(symbol)
        worker_id = f"worker_{os.getpid()}_{int(time.time())}"
        
        try:
            acquired = self.redis_client.set(lock_key, worker_id, nx=True, ex=timeout)
            if acquired:
                logger.info(f"🔒 LLM lock acquired by {worker_id}")
                return True
            else:
                current_owner = self.redis_client.get(lock_key)
                logger.info(f"⏳ LLM lock held by {current_owner}, skipping")
                return False
        except Exception as e:
            logger.warning(f"Failed to acquire LLM lock: {e}")
            return True
    
    def _release_llm_lock(self, symbol: str):
        """Release LLM analysis lock"""
        if not self.redis_client:
            return
        
        lock_key = self._get_llm_lock_key(symbol)
        try:
            self.redis_client.delete(lock_key)
            logger.debug(f"🔓 LLM lock released")
        except Exception as e:
            logger.warning(f"Failed to release LLM lock: {e}")
    
    def _get_cached_llm_result(self, symbol: str, timeframes: List[str]) -> Optional[Dict[str, Any]]:
        """Get cached LLM analysis result"""
        if not self.redis_client:
            return None
        
        cache_key = self._get_llm_cache_key(symbol, timeframes)
        try:
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                logger.info(f"📋 Using cached LLM analysis")
                return json.loads(cached_result)
        except Exception as e:
            logger.warning(f"Failed to get cached LLM result: {e}")
        return None
    
    def _cache_llm_result(self, symbol: str, timeframes: List[str], result: Dict[str, Any]):
        """Cache LLM analysis result for 60 seconds"""
        if not self.redis_client:
            return
        
        cache_key = self._get_llm_cache_key(symbol, timeframes)
        try:
            self.redis_client.setex(cache_key, 60, json.dumps(result))
            logger.debug(f"💾 Cached LLM analysis")
        except Exception as e:
            logger.warning(f"Failed to cache LLM result: {e}")
    
    # ==================== DATA CRAWLING ====================
    
    def crawl_data(self, subscription_config: dict = None) -> Dict[str, Any]:
        """
        Crawl historical data for multiple timeframes from exchange
        Returns multi-timeframe OHLCV data
        
        Args:
            subscription_config: Optional subscription configuration containing:
                                - trading_pair: Trading pair to crawl
                                - timeframes: List of timeframes to crawl
                                If not provided, uses self.trading_pair and self.timeframes
        """
        import time
        from datetime import datetime
        import pandas as pd
        
        def _now_ms():
            offset = getattr(self, "_time_offset", 0)
            return int(time.time() * 1000) + int(offset)
        
        def _df_to_records(df: pd.DataFrame) -> list:
            out = []
            for _, row in df.iterrows():
                ts = row["timestamp"]
                if hasattr(ts, "timestamp"):
                    ts_ms = int(ts.timestamp() * 1000)
                elif isinstance(ts, (int, float)):
                    ts_ms = int(ts) if ts > 1e12 else int(ts * 1000)
                else:
                    ts_ms = int(pd.to_datetime(ts).timestamp() * 1000)
                
                out.append({
                    "timestamp": ts_ms,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                })
            return out
        
        timeframe_to_ms = {
            "1m": 60_000, "3m": 3 * 60_000, "5m": 5 * 60_000, "15m": 15 * 60_000,
            "30m": 30 * 60_000, "1h": 60 * 60_000, "2h": 2 * 60 * 60_000, "4h": 4 * 60 * 60_000,
            "6h": 6 * 60 * 60_000, "8h": 8 * 60 * 60_000, "12h": 12 * 60 * 60_000,
            "1d": 24 * 60 * 60_000, "3d": 3 * 24 * 60 * 60_000, "1w": 7 * 24 * 60 * 60_000,
            "1M": 30 * 24 * 60 * 60_000,
        }
        
        timeframe_limits = {
            "30m": 200, "1h": 168, "4h": 42,
            "1m": 1000, "3m": 1000, "5m": 500, "15m": 500,
            "2h": 84, "6h": 28, "8h": 21, "12h": 14,
            "1d": 30, "3d": 30, "1w": 52, "1M": 12
        }
        
        MIN_NEEDED = 20
        INITIAL_LOOKBACK_MULT = 1.5
        MAX_RETRIES = 3
        
        # Extract trading_pair and timeframes from subscription_config
        # This prevents race conditions when multiple workers use the same bot instance
        if subscription_config:
            config_trading_pair = subscription_config.get('trading_pair', self.trading_pair)
            config_timeframes = subscription_config.get('timeframes', self.timeframes)
        else:
            config_trading_pair = self.trading_pair
            config_timeframes = self.timeframes
        
        actual_trading_pair = config_trading_pair.replace('/', '') if config_trading_pair else self.trading_pair.replace('/', '')
        actual_timeframes = config_timeframes if config_timeframes else self.timeframes
        
        logger.info(f"📊 Data crawling using MAINNET public API on {self.exchange_name}")
        logger.info(f"📊 Crawling pair: {actual_trading_pair} (config={subscription_config.get('trading_pair') if subscription_config else None}, self={self.trading_pair})")
        logger.info(f"📊 Crawling timeframes: {actual_timeframes} (config={subscription_config.get('timeframes') if subscription_config else None}, self={self.timeframes})")
        
        timeframes_data = {}
        try:
            logger.info(f"🔄 Crawling data for timeframes: {actual_timeframes}")
            
            for i, timeframe in enumerate(actual_timeframes, 1):
                try:
                    if timeframe not in timeframe_to_ms:
                        raise ValueError(f"Unsupported timeframe: {timeframe}")
                    
                    interval_ms = timeframe_to_ms[timeframe]
                    now_ms = _now_ms()
                    last_closed_open = (now_ms // interval_ms) * interval_ms - interval_ms
                    end_time = last_closed_open + interval_ms - 1
                    
                    base_limit = timeframe_limits.get(timeframe, 100)
                    desired_limit = max(base_limit, MIN_NEEDED)
                    
                    lookback = int(max(desired_limit, int(desired_limit * INITIAL_LOOKBACK_MULT)))
                    start_time = end_time - (lookback - 1) * interval_ms
                    
                    logger.info(f"📊 [{i}/{len(actual_timeframes)}] Fetching {lookback} {timeframe} candles for {actual_trading_pair}")
                    
                    df = self.futures_client.get_klines(
                        symbol=actual_trading_pair,
                        interval=timeframe,
                        start_time=start_time,
                        end_time=end_time,
                        limit=lookback
                    )
                    
                    if df is None or len(df) == 0:
                        raise RuntimeError(f"Empty klines for {timeframe}")
                    
                    # Backfill if needed
                    retries = 0
                    while len(df) < MIN_NEEDED and retries < MAX_RETRIES:
                        retries += 1
                        add_lookback = MIN_NEEDED * 3 * interval_ms
                        new_start = max(0, start_time - add_lookback)
                        new_end = start_time - 1
                        
                        logger.warning(f"⚠️ {timeframe} needs backfill {len(df)}/{MIN_NEEDED}, retry {retries}...")
                        df_more = self.futures_client.get_klines(
                            symbol=actual_trading_pair,
                            interval=timeframe,
                            start_time=new_start,
                            end_time=new_end,
                            limit=MIN_NEEDED * 3
                        )
                        
                        if df_more is not None and len(df_more) > 0:
                            df = pd.concat([df_more, df], axis=0).drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
                        start_time = new_start
                    
                    df = df.sort_values("timestamp")
                    if len(df) < MIN_NEEDED:
                        logger.warning(f"❗ {timeframe} still insufficient: {len(df)}/{MIN_NEEDED}")
                    
                    if len(df) > desired_limit:
                        df = df.iloc[-desired_limit:]
                    
                    records = _df_to_records(df)
                    timeframes_data[timeframe] = records
                    
                    logger.info(f"✅ [{i}/{len(actual_timeframes)}] Got {len(records)} {timeframe} candles")
                    
                except Exception as tf_err:
                    logger.error(f"❌ [{i}/{len(actual_timeframes)}] Failed to fetch {timeframe}: {tf_err}")
                    timeframes_data[timeframe] = []
            
            report = {tf: len(candles) for tf, candles in timeframes_data.items()}
            logger.info(f"🎯 Completed crawling {len(timeframes_data)} TFs. Counts: {report}")
            
            return {
                "timeframes": timeframes_data,
                "crawl_timestamp": datetime.now().isoformat(),
                "total_timeframes": len(timeframes_data),
                "exchange": self.exchange_name
            }
            
        except Exception as e:
            logger.error(f"Error crawling multi-timeframe data: {e}")
            return {
                "timeframes": timeframes_data,
                "crawl_timestamp": datetime.now().isoformat(),
                "total_timeframes": len(timeframes_data),
                "error": str(e),
                "exchange": self.exchange_name
            }
    
    # ==================== ANALYSIS ====================
    
    def _calculate_futures_analysis(self, data: pd.DataFrame, historical_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate technical analysis for futures trading"""
        try:
            # RSI
            def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                return rsi.iloc[-1] if not rsi.empty else 50
            
            # MACD
            def calculate_macd(prices: pd.Series, fast=12, slow=26, signal=9):
                ema_fast = prices.ewm(span=fast).mean()
                ema_slow = prices.ewm(span=slow).mean()
                macd_line = ema_fast - ema_slow
                signal_line = macd_line.ewm(span=signal).mean()
                return macd_line.iloc[-1], signal_line.iloc[-1]
            
            rsi = calculate_rsi(data['close'], self.rsi_period)
            macd, macd_signal = calculate_macd(data['close'])
            
            sma_20 = data['close'].rolling(window=20).mean().iloc[-1]
            sma_50 = data['close'].rolling(window=50).mean().iloc[-1]
            
            # ATR for volatility
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=14).mean().iloc[-1]
            
            analysis = {
                'current_price': float(data['close'].iloc[-1]),
                'rsi': float(rsi),
                'rsi_oversold': bool(rsi < self.rsi_oversold),
                'rsi_overbought': bool(rsi > self.rsi_overbought),
                'macd': float(macd),
                'macd_signal': float(macd_signal),
                'macd_bullish': bool(macd > macd_signal),
                'sma_20': float(sma_20),
                'sma_50': float(sma_50),
                'trend_bullish': bool(sma_20 > sma_50),
                'atr': float(atr),
                'volatility': float(atr / data['close'].iloc[-1] * 100),
                'volume_ratio': float(data['volume'].iloc[-1] / data['volume'].rolling(20).mean().iloc[-1])
            }
            
            if historical_data:
                analysis['historical_data'] = historical_data
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error calculating futures analysis: {e}")
            return {'error': str(e), 'historical_data': historical_data}
    
    def analyze_data(self, multi_timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze multi-timeframe historical data"""
        try:
            timeframes_data = multi_timeframe_data.get("timeframes", {})
            if not timeframes_data:
                return {'error': 'No timeframes data provided'}
            
            multi_analysis = {}
            
            for timeframe, historical_data in timeframes_data.items():
                if not historical_data:
                    continue
                
                try:
                    df = pd.DataFrame(historical_data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df = df.set_index('timestamp')
                    
                    timeframe_analysis = self._calculate_futures_analysis(df, historical_data)
                    multi_analysis[timeframe] = timeframe_analysis
                    
                    logger.info(f"Analyzed {timeframe}: Price {timeframe_analysis.get('current_price', 0):.2f}")
                    
                except Exception as e:
                    logger.error(f"Error analyzing {timeframe}: {e}")
                    multi_analysis[timeframe] = {'error': f'Analysis error: {e}'}
            
            primary_analysis = multi_analysis.get(self.primary_timeframe, {})
            
            combined_analysis = {
                'multi_timeframe': multi_analysis,
                'primary_timeframe': self.primary_timeframe,
                'primary_analysis': primary_analysis,
                'timeframes_data': timeframes_data,
                'exchange': self.exchange_name
            }
            
            if 'current_price' in primary_analysis:
                combined_analysis['current_price'] = primary_analysis['current_price']
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing multi-timeframe data: {e}")
            return {'error': f'Multi-timeframe analysis error: {e}'}
    
    # ==================== SIGNAL GENERATION ====================
    
    def _generate_technical_signal(self, analysis: Dict[str, Any], data: pd.DataFrame) -> Action:
        """Generate signal using traditional technical analysis"""
        try:
            logger.info("Generating signal using technical analysis...")
            if 'error' in analysis:
                return Action(action="HOLD", value=0.0, reason=f"Analysis error: {analysis['error']}")
            
            signals = []
            signal_strength = 0
            reasons = []
            
            # RSI signals
            if analysis.get('rsi_oversold', False):
                signals.append('RSI_OVERSOLD')
                signal_strength += 3
                reasons.append(f"RSI oversold ({analysis.get('rsi', 0):.1f})")
            elif analysis.get('rsi_overbought', False):
                signals.append('RSI_OVERBOUGHT')
                signal_strength -= 3
                reasons.append(f"RSI overbought ({analysis.get('rsi', 0):.1f})")
            
            # MACD signals
            macd_value = analysis.get('macd', 0)
            macd_signal_value = analysis.get('macd_signal', 0)
            if abs(macd_value - macd_signal_value) > 50:
                if analysis.get('macd_bullish', False):
                    signals.append('MACD_BULLISH')
                    signal_strength += 2
                    reasons.append("MACD bullish crossover")
                elif analysis.get('macd_bullish') == False:
                    signals.append('MACD_BEARISH')
                    signal_strength -= 2
                    reasons.append("MACD bearish crossover")
            
            # Trend signals
            sma_20 = analysis.get('sma_20', 0)
            sma_50 = analysis.get('sma_50', 0)
            if sma_20 > 0 and sma_50 > 0:
                trend_strength = abs(sma_20 - sma_50) / sma_50
                if trend_strength > 0.01:
                    if analysis.get('trend_bullish', False):
                        signals.append('TREND_BULLISH')
                        signal_strength += 1
                        reasons.append(f"Bullish trend ({trend_strength*100:.1f}%)")
                    else:
                        signals.append('TREND_BEARISH')
                        signal_strength -= 1
                        reasons.append(f"Bearish trend ({trend_strength*100:.1f}%)")
            
            # Volatility consideration
            volatility = analysis.get('volatility', 0)
            if volatility > 3:
                signal_strength *= 0.8
                reasons.append(f"High volatility ({volatility:.1f}%)")
            
            confidence = min(abs(signal_strength) * 12, 100)
            reason_text = ", ".join(reasons)
            
            if signal_strength >= 4:
                return Action(action="BUY", value=confidence/100, reason=reason_text)
            elif signal_strength <= -4:
                return Action(action="SELL", value=confidence/100, reason=reason_text)
            else:
                return Action(action="HOLD", value=confidence/100, reason=reason_text)
                
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Signal error: {e}")
    
    async def _generate_llm_signal_from_multi_timeframes(self, timeframes_data: Dict[str, List[Dict]]) -> Action:
        """Generate signal using LLM with multi-timeframe data"""
        try:
            if not self.llm_service:
                return Action(action="HOLD", value=0.0, reason="LLM service unavailable")
            
            # Clean data for LLM
            cleaned_timeframes_data = {}
            data_limits = {
                '1m': 60, '3m': 60, '5m': 60, '15m': 48, '30m': 48,
                '1h': 24, '2h': 24, '4h': 12, '6h': 12, '8h': 12, '12h': 12,
                '1d': 7, '3d': 7, '1w': 4, '1M': 4
            }
            
            for timeframe, data in timeframes_data.items():
                if data:
                    limit = data_limits.get(timeframe, 24)
                    cleaned_data = []
                    for item in data[-limit:]:
                        cleaned_item = {}
                        for key, value in item.items():
                            if hasattr(value, 'timestamp'):
                                cleaned_item[key] = int(value.timestamp() * 1000)
                            elif hasattr(value, 'isoformat'):
                                cleaned_item[key] = value.isoformat()
                            else:
                                cleaned_item[key] = float(value) if isinstance(value, (int, float)) else value
                        cleaned_data.append(cleaned_item)
                    
                    cleaned_timeframes_data[timeframe] = cleaned_data
            
            # Get LLM analysis
            self.trading_pair = self.trading_pair.replace('/', '')
            llm_analysis = await self.llm_service.analyze_market(
                symbol=self.trading_pair,
                timeframes_data=cleaned_timeframes_data,
                model=self.llm_model,
                bot_id=self.bot_id
            )
            
            if "error" in llm_analysis:
                logger.error(f"LLM analysis failed: {llm_analysis['error']}")
                return Action(action="HOLD", value=0.0, reason=f"LLM error: {llm_analysis['error']}")
            
            # Debug: Log raw LLM response
            logger.info(f"🔍 Raw LLM analysis keys: {list(llm_analysis.keys())}")
            logger.info(f"🔍 parsed={llm_analysis.get('parsed')}, has_recommendation={'recommendation' in llm_analysis}")
            if not llm_analysis.get("parsed", False) or "recommendation" not in llm_analysis:
                logger.warning(f"⚠️ LLM response structure: {llm_analysis}")
            
            # Parse recommendation
            if llm_analysis.get("parsed", False) and "recommendation" in llm_analysis:
                recommendation = llm_analysis["recommendation"]
                
                action = recommendation.get("action", "HOLD").upper()
                
                # Parse confidence
                confidence_raw = recommendation.get("confidence", 0)
                try:
                    if isinstance(confidence_raw, str):
                        confidence_str = confidence_raw.replace("%", "").strip()
                        confidence = float(confidence_str) / 100.0
                    else:
                        confidence = float(confidence_raw) / 100.0
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse confidence: {e}")
                    confidence = 0.0
                
                reasoning = recommendation.get("reasoning", "LLM analysis")
                
                # Extract recommendation details (SIGNALS_FUTURES includes SL/TP from LLM)
                entry_price = recommendation.get("entry_price", "Market")
                take_profit = recommendation.get("take_profit", "N/A")
                stop_loss = recommendation.get("stop_loss", "N/A")
                strategy = recommendation.get("strategy", "Multi-timeframe")
                risk_reward = recommendation.get("risk_reward", "N/A")
                market_volatility = recommendation.get("market_volatility", "MEDIUM")
                
                if action == "CLOSE":
                    action = "SELL"
                
                if action not in ["BUY", "SELL", "HOLD"]:
                    action = "HOLD"
                    confidence = 0.0
                    reasoning = f"Invalid LLM action: {action}"
                
                logger.info(f"🤖 LLM: {action} ({confidence*100:.1f}%) - {reasoning[:80]}...")
                logger.info(f"   Entry: {entry_price} | SL: {stop_loss} | TP: {take_profit} | R:R: {risk_reward}")
                logger.info(f"   Market Volatility: {market_volatility}")
                
                full_recommendation = {
                    "action": action,
                    "confidence": f"{confidence*100:.1f}%",
                    "entry_price": entry_price,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                    "strategy": strategy,
                    "risk_reward": risk_reward,
                    "market_volatility": market_volatility,
                    "reasoning": reasoning
                }
                
                return Action(
                    action=action,
                    value=confidence,
                    reason=f"[LLM-{self.exchange_name}] {reasoning}",
                    recommendation=full_recommendation
                )
            else:
                logger.warning("LLM response could not be parsed")
                return Action(action="HOLD", value=0.0, reason="Unparseable LLM response")
                
        except Exception as e:
            logger.error(f"Error in LLM signal generation: {e}")
            return Action(action="HOLD", value=0.0, reason=f"LLM signal error: {e}")
    
    def generate_signal(self, analysis: Dict[str, Any]) -> Action:
        """Generate trading signal based on multi-timeframe analysis"""
        self.trading_pair = self.trading_pair.replace('/', '')
        try:
            if 'error' in analysis:
                return Action(action="HOLD", value=0.0, reason=f"Analysis error: {analysis['error']}")
            
            # Try LLM analysis if enabled
            if (self.use_llm_analysis and self.llm_service and
                'timeframes_data' in analysis and analysis['timeframes_data']):
                
                # Check cache first
                cached_result = self._get_cached_llm_result(self.trading_pair, self.timeframes)
                if cached_result:
                    return Action(
                        action=cached_result.get('action', 'HOLD'),
                        value=cached_result.get('confidence', 0.0),
                        reason=f"[CACHED-{self.exchange_name}] {cached_result.get('reasoning', 'Cached LLM analysis')}"
                    )
                
                # Try to acquire lock
                if not self._acquire_llm_lock(self.trading_pair):
                    time.sleep(3)
                    cached_result = self._get_cached_llm_result(self.trading_pair, self.timeframes)
                    if cached_result:
                        return Action(
                            action=cached_result.get('action', 'HOLD'),
                            value=cached_result.get('confidence', 0.0),
                            reason=f"[WAITED-{self.exchange_name}] {cached_result.get('reasoning', 'LLM from other worker')}"
                        )
                    else:
                        logger.warning("⚠️ No cached result, falling back to technical")
                else:
                    logger.info(f"🤖 Generating LLM signal for {self.exchange_name}...")
                    
                    try:
                        import concurrent.futures
                        
                        def run_llm_signal():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(
                                    self._generate_llm_signal_from_multi_timeframes(analysis['timeframes_data'])
                                )
                            except Exception as e:
                                logger.error(f"LLM signal error: {e}")
                                return None
                            finally:
                                new_loop.close()
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_llm_signal)
                            try:
                                llm_action = future.result(timeout=60)
                                if llm_action:
                                    cache_data = {
                                        'action': llm_action.action,
                                        'confidence': llm_action.value,
                                        'reasoning': llm_action.reason
                                    }
                                    self._cache_llm_result(self.trading_pair, self.timeframes, cache_data)
                                    self._release_llm_lock(self.trading_pair)
                                    return llm_action
                            except concurrent.futures.TimeoutError:
                                logger.warning("LLM signal timed out")
                                self._release_llm_lock(self.trading_pair)
                            except Exception as e:
                                logger.warning(f"LLM signal failed: {e}")
                                self._release_llm_lock(self.trading_pair)
                                
                    except Exception as e:
                        logger.warning(f"Failed to setup LLM: {e}")
                        self._release_llm_lock(self.trading_pair)
                
                logger.info("Falling back to technical analysis...")
            
            # Fallback to technical analysis
            logger.info(f"Generating signal using technical analysis for {self.exchange_name}...")
            
            multi_analysis = analysis.get('multi_timeframe', {})
            primary_analysis = analysis.get('primary_analysis', {})
            
            if not primary_analysis or 'error' in primary_analysis:
                return Action(action="HOLD", value=0.0, reason="No valid primary analysis")
            
            primary_df = pd.DataFrame({'close': [primary_analysis.get('current_price', 50000)], 'volume': [100]})
            primary_signal = self._generate_technical_signal(primary_analysis, primary_df)
            
            # Multi-timeframe confirmation
            confirmations = 0
            total_timeframes = 0
            
            for tf, tf_analysis in multi_analysis.items():
                if tf == self.primary_timeframe or 'error' in tf_analysis:
                    continue
                
                total_timeframes += 1
                tf_df = pd.DataFrame({'close': [tf_analysis.get('current_price', 50000)], 'volume': [100]})
                tf_signal = self._generate_technical_signal(tf_analysis, tf_df)
                
                if tf_signal.action == primary_signal.action:
                    confirmations += 1
            
            confirmation_ratio = confirmations / total_timeframes if total_timeframes > 0 else 1.0
            adjusted_confidence = primary_signal.value * (0.5 + 0.5 * confirmation_ratio)
            
            reason = f"[MULTI-TF-{self.exchange_name}] {primary_signal.reason}"
            if total_timeframes > 0:
                reason += f" | Confirmation: {confirmations}/{total_timeframes}"
            
            # Create technical recommendation
            current_price = primary_analysis.get('current_price', 50000)
            if primary_signal.action == "BUY":
                entry_price = f"{current_price:.2f}"
                take_profit = f"{current_price * 1.04:.2f}"
                stop_loss = f"{current_price * 0.98:.2f}"
            elif primary_signal.action == "SELL":
                entry_price = f"{current_price:.2f}"
                take_profit = f"{current_price * 0.96:.2f}"
                stop_loss = f"{current_price * 1.02:.2f}"
            else:
                entry_price = "N/A"
                take_profit = "N/A"
                stop_loss = "N/A"
            
            technical_recommendation = {
                "action": primary_signal.action,
                "confidence": f"{adjusted_confidence*100:.1f}%",
                "entry_price": entry_price,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "strategy": f"Multi-timeframe technical ({self.exchange_name})",
                "risk_reward": "1:2" if primary_signal.action != "HOLD" else "N/A",
                "reasoning": reason
            }
            
            return Action(
                action=primary_signal.action,
                value=adjusted_confidence,
                reason=reason,
                recommendation=technical_recommendation
            )
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Signal error: {e}")


# ==================== FACTORY FUNCTION ====================

def create_universal_futures_signals_bot(
    exchange: str,
    user_principal_id: str,
    config: Dict[str, Any] = None,
    subscription_id: int = None
) -> UniversalFuturesSignalsBot:
    """
    Factory function to create Universal Futures Signals Bot
    
    Args:
        exchange: Exchange name (BINANCE, BYBIT, OKX, BITGET, HUOBI, KRAKEN)
        user_principal_id: ICP Principal ID
        config: Bot configuration (optional)
        subscription_id: Subscription ID (optional)
    
    Returns:
        Configured UniversalFuturesSignalsBot instance
    """
    default_config = {
        'exchange': exchange.upper(),
        'trading_pair': 'BTCUSDT',
        'timeframes': ['30m', '1h', '4h'],
        'primary_timeframe': '1h',
        'use_llm_analysis': True,
        'llm_model': 'openai',
        'notification_config': {
            'telegram': {'enabled': True},
            'discord': {'enabled': True}
        }
    }
    
    if config:
        default_config.update(config)
    
    return UniversalFuturesSignalsBot(
        config=default_config,
        user_principal_id=user_principal_id,
        subscription_id=subscription_id
    )


if __name__ == "__main__":
    print("Universal Futures Signals Bot - Analysis & Notification Only")
    print("Supported exchanges:", ', '.join(UniversalFuturesSignalsBot.SUPPORTED_EXCHANGES))
    print("Notification channels: Telegram, Discord")
    print("\nUse create_universal_futures_signals_bot() factory function to create bot instances")


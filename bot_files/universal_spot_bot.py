"""
Universal Spot Trading Bot Template - Multi-Exchange Support
Supports: Binance, Bybit, OKX, Bitget, Huobi/HTX, Kraken

Advanced spot trading bot with:
- Multi-exchange support via unified interface
- LLM AI analysis (OpenAI/Claude/Gemini)
- Multi-timeframe analysis
- Capital management system
- Stop loss & take profit (via OCO orders)
- DCA (Dollar Cost Averaging) support
- Position monitoring
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
from dataclasses import dataclass

# Bot SDK imports
from bots.bot_sdk import CustomBot, Action

# Exchange integrations
from services.exchange_integrations import (
    BaseSpotExchange,
    SpotOrderInfo,
    create_spot_exchange
)

# Services
from services.llm_integration import create_llm_service
from bot_files.capital_management import CapitalManagement, RiskMetrics, PositionSizeRecommendation
from core.api_key_manager import get_bot_api_keys

logger = logging.getLogger(__name__)

class UniversalSpotBot(CustomBot):
    """Universal Spot Trading Bot with Multi-Exchange Support"""
    
    SUPPORTED_EXCHANGES = ['BINANCE', 'BYBIT', 'OKX', 'BITGET', 'HUOBI', 'HTX', 'KRAKEN']
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str] = None, 
                 user_principal_id: str = None, subscription_id: int = None):
        """
        Initialize Universal Spot Bot
        
        Args:
            config: Bot configuration including:
                - exchange: Exchange name (BINANCE, BYBIT, OKX, BITGET, HUOBI, KRAKEN)
                - trading_pair: Trading pair (e.g., 'BTC/USDT')
                - base_asset: Base asset (e.g., 'BTC')
                - quote_asset: Quote asset (e.g., 'USDT')
                - stop_loss_pct: Stop loss percentage (default: 0.02)
                - take_profit_pct: Take profit percentage (default: 0.04)
                - position_size_pct: Position size percentage (default: 0.1)
                - testnet: Use testnet (default: True)
                - timeframes: List of timeframes for analysis (default: ['30m', '1h', '4h'])
                - use_llm_analysis: Enable LLM analysis (default: True)
                - llm_model: LLM model to use (default: 'openai')
                - use_oco_orders: Use OCO (One-Cancels-Other) orders (default: True)
                - trailing_stop: Enable trailing stop loss (default: False)
            api_keys: LLM API keys (optional)
            user_principal_id: User principal ID for database lookup
            subscription_id: Subscription ID for bot management
        """
        super().__init__(config, api_keys)
        
        # Bot identification
        self.bot_id = config.get('bot_id')
        self.subscription_id = subscription_id
        logger.info(f"🤖 [SPOT BOT INIT] bot_id={self.bot_id}, subscription_id={subscription_id}")
        
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
        
        logger.info(f"🌐 Using exchange: {self.exchange_name} (SPOT)")
        
        # Trading configuration
        raw_trading_pair = config.get('trading_pair', 'BTC/USDT')
        
        # Parse trading pair
        if '/' in raw_trading_pair:
            parts = raw_trading_pair.split('/')
            self.base_asset = parts[0]
            self.quote_asset = parts[1]
            self.trading_pair = f"{self.base_asset}{self.quote_asset}"
        else:
            self.trading_pair = raw_trading_pair
            # Try to extract base/quote (assuming USDT as common quote)
            if raw_trading_pair.endswith('USDT'):
                self.base_asset = raw_trading_pair[:-4]
                self.quote_asset = 'USDT'
            elif raw_trading_pair.endswith('BUSD'):
                self.base_asset = raw_trading_pair[:-4]
                self.quote_asset = 'BUSD'
            elif raw_trading_pair.endswith('BTC'):
                self.base_asset = raw_trading_pair[:-3]
                self.quote_asset = 'BTC'
            else:
                self.base_asset = config.get('base_asset', 'BTC')
                self.quote_asset = config.get('quote_asset', 'USDT')
        
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)
        self.take_profit_pct = config.get('take_profit_pct', 0.04)
        self.position_size_pct = config.get('position_size_pct', 0.1)
        self.testnet = config.get('testnet', True)
        
        # Spot-specific features
        self.use_oco_orders = config.get('use_oco_orders', True)  # OCO for SL/TP
        self.trailing_stop = config.get('trailing_stop', False)
        self.trailing_stop_pct = config.get('trailing_stop_pct', 0.01)
        self.min_notional = config.get('min_notional', 10.0)  # Minimum order value
        
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
        
        # Initialize exchange client
        if not user_principal_id:
            raise ValueError("user_principal_id is required for database API key lookup")
        
        self.user_principal_id = user_principal_id
        logger.info(f"Bot initialized for principal ID: {self.user_principal_id}")
        
        # Get API keys from database
        logger.info(f"Loading {self.exchange_name} API keys for principal ID: {user_principal_id}")
        db_credentials = get_bot_api_keys(
            user_principal_id=user_principal_id,
            exchange=self.exchange_name,
            is_testnet=self.testnet,
            subscription_id=subscription_id
        )
        
        if not db_credentials:
            raise ValueError(
                f"No {self.exchange_name} API credentials found in database for principal ID: {user_principal_id}"
            )
        
        # Create spot exchange client using factory
        try:
            self.spot_client = create_spot_exchange(
                exchange_name=self.exchange_name,
                api_key=db_credentials['api_key'],
                api_secret=db_credentials['api_secret'],
                passphrase=db_credentials.get('passphrase', ''),
                testnet=db_credentials['testnet']
            )
            logger.info(f"✅ {self.exchange_name} SPOT client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize {self.exchange_name} spot client: {e}")
            raise
        
        # Always use public mainnet client for data crawling (no auth needed for market data)
        try:
            logger.info("📡 Creating public mainnet client for market data crawling...")
            self.spot_client_mainnet = create_spot_exchange(
                exchange_name=self.exchange_name,
                api_key="",
                api_secret="",
                passphrase="",
                testnet=False
            )
            logger.info("✅ Public mainnet client created for accurate market data (no auth required)")
        except Exception as e:
            logger.warning(f"Could not initialize mainnet client: {e}")
            self.spot_client_mainnet = None
        
        # Initialize LLM service
        self.llm_service = None
        if self.use_llm_analysis:
            try:
                # Get developer_id and db from config
                developer_id = config.get('developer_id')
                db = config.get('db')
                bot_id = config.get('bot_id')
                
                # Get bot's preferred LLM provider and model from config (set in UI)
                preferred_provider = config.get('llm_provider')  # "openai", "claude", "gemini"
                llm_model = config.get('llm_model')  # Specific model selected in UI (e.g., "gemini-2.5-pro")
                
                if preferred_provider:
                    logger.info(f"🎯 Bot configured to use LLM provider: {preferred_provider}")
                if llm_model:
                    logger.info(f"🎯 Bot configured to use specific model: {llm_model}")
                
                # If no specific model, use provider name as model identifier
                if not llm_model and preferred_provider:
                    llm_model = preferred_provider
                    logger.info(f"ℹ️  No specific model configured, using provider: {preferred_provider}")
                
                # Build LLM config with defaults
                llm_config = {
                    'openai_api_key': os.getenv('OPENAI_API_KEY'),
                    'claude_api_key': os.getenv('CLAUDE_API_KEY'),
                    'gemini_api_key': os.getenv('GEMINI_API_KEY'),
                    'openai_model': config.get('openai_model', 'gpt-4o'),
                    'claude_model': config.get('claude_model', 'claude-3-5-sonnet-20241022'),
                    'gemini_model': config.get('gemini_model', 'gemini-2.5-flash')
                }
                
                # Override with specific model if provided
                if llm_model:
                    if preferred_provider == 'openai':
                        llm_config['openai_model'] = llm_model
                        logger.info(f"✅ Using OpenAI model: {llm_model}")
                    elif preferred_provider in ['anthropic', 'claude']:
                        llm_config['claude_model'] = llm_model
                        logger.info(f"✅ Using Claude model: {llm_model}")
                    elif preferred_provider == 'gemini':
                        llm_config['gemini_model'] = llm_model
                        logger.info(f"✅ Using Gemini model: {llm_model}")
                    elif preferred_provider == 'groq':
                        llm_config['groq_model'] = llm_model
                        logger.info(f"✅ Using Groq model: {llm_model}")
                    elif preferred_provider == 'cohere':
                        llm_config['cohere_model'] = llm_model
                        logger.info(f"✅ Using Cohere model: {llm_model}")
                
                # Create LLM service with developer's API keys (BYOK - Priority!)
                self.llm_service = create_llm_service(
                    config=llm_config,
                    developer_id=developer_id,
                    db=db,
                    preferred_provider=preferred_provider,  # ✅ Pass bot's preference!
                    bot_id=bot_id
                )
                
                # Update self.llm_model to use the actual model that will be used
                if llm_model:
                    self.llm_model = llm_model
                elif preferred_provider:
                    self.llm_model = preferred_provider
                
                if developer_id:
                    logger.info(f"✅ LLM service initialized for developer {developer_id} (using their API keys - FREE)")
                else:
                    logger.info(f"ℹ️  LLM service initialized with environment variables")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize LLM service: {e}")
                import traceback
                traceback.print_exc()
                self.use_llm_analysis = False
                logger.warning("⚠️  Falling back to traditional technical analysis")
        
        # Initialize Capital Management System (adjusted for spot trading)
        capital_config = {
            'base_position_size_pct': config.get('base_position_size_pct', 0.05),  # Lower for spot
            'max_position_size_pct': config.get('max_position_size_pct', 0.20),    # Lower for spot
            'max_portfolio_exposure': config.get('max_portfolio_exposure', 0.50),  # Higher for spot
            'max_drawdown_threshold': config.get('max_drawdown_threshold', 0.15),
            'volatility_threshold_low': config.get('volatility_threshold_low', 0.02),
            'volatility_threshold_high': config.get('volatility_threshold_high', 0.08),
            'kelly_multiplier': config.get('kelly_multiplier', 0.20),  # More conservative for spot
            'min_win_rate': config.get('min_win_rate', 0.40),
            'use_llm_capital_management': config.get('use_llm_capital_management', True),
            'llm_capital_weight': config.get('llm_capital_weight', 0.40),
            'sizing_method': config.get('sizing_method', 'llm_hybrid')
        }
        
        self.capital_manager = CapitalManagement(capital_config)
        
        logger.info(f"✅ Universal Spot Bot initialized")
        logger.info(f"   Exchange: {self.exchange_name} (SPOT)")
        logger.info(f"   Trading Pair: {self.base_asset}/{self.quote_asset}")
        logger.info(f"   Timeframes: {self.timeframes}")
        logger.info(f"   LLM Analysis: {'Enabled (' + self.llm_model + ')' if self.use_llm_analysis else 'Disabled'}")
        logger.info(f"   OCO Orders: {'Enabled' if self.use_oco_orders else 'Disabled'}")
        logger.info(f"   Testnet: {self.testnet}")
    
    # ==================== MAIN EXECUTION METHOD ====================
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Main execution method - required by CustomBot
        
        This method implements the complete trading cycle:
        1. Crawl multi-timeframe data
        2. Analyze data with LLM/technical indicators
        3. Generate trading signal
        4. Return action
        
        Args:
            data: Historical price data (not used, we crawl fresh data)
            timeframe: Primary timeframe for analysis
            subscription_config: Additional configuration from subscription
            
        Returns:
            Action: Trading action (BUY/SELL/HOLD)
        """
        try:
            logger.info(f"🚀 [EXECUTE ALGORITHM] Starting SPOT trading cycle for {self.trading_pair}")
            logger.info(f"   Exchange: {self.exchange_name}")
            logger.info(f"   Timeframes: {self.timeframes}")
            
            # Step 0: Check account status and balance
            logger.info("💰 Step 0: Checking account status...")
            account_status = self.check_account_status()
            if not account_status:
                logger.error("❌ Failed to check account status")
                return Action.HOLD
            
            # Validate sufficient balance
            quote_balance = account_status.get('quote_balance', 0)
            if quote_balance <= 0:
                logger.error(f"❌ Insufficient {self.quote_asset} balance: ${quote_balance:.2f}")
                return Action(action="HOLD", value=0.0, reason=f"Insufficient balance: ${quote_balance:.2f} {self.quote_asset}")
            
            logger.info(f"✅ Account check passed - {self.quote_asset} balance: ${quote_balance:.2f}")
            
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
            
            logger.info(f"✅ [EXECUTE ALGORITHM] Completed - Signal: {signal.action}")
            return signal
            
        except Exception as e:
            logger.error(f"❌ [EXECUTE ALGORITHM] Error: {e}")
            import traceback
            traceback.print_exc()
            return Action.HOLD
    
    def check_account_status(self) -> Optional[Dict[str, Any]]:
        """
        Check spot account status and balances
        
        Returns:
            Dict with account info:
            - base_balance: Base asset balance (e.g., BTC)
            - quote_balance: Quote asset balance (e.g., USDT)
            - total_value_usdt: Total portfolio value in USDT
        """
        try:
            logger.info(f"\n💼 CHECKING {self.exchange_name} SPOT ACCOUNT STATUS...")
            logger.info("=" * 50)
            
            # Get account balances
            account_info = self.spot_client.get_account_info()
            
            base_balance = 0.0
            quote_balance = 0.0
            
            # Extract balances
            balances = account_info.get('balances', [])
            for balance in balances:
                asset = balance.get('asset', '')
                free = float(balance.get('free', 0))
                
                if asset == self.base_asset:
                    base_balance = free
                elif asset == self.quote_asset:
                    quote_balance = free
            
            # Get current price for portfolio value calculation
            current_price = self.spot_client.get_current_price(self.trading_pair)
            total_value_usdt = (base_balance * current_price) + quote_balance
            
            mode = "🧪 TESTNET" if self.testnet else "🔴 LIVE"
            logger.info(f"{mode} Account Balance:")
            logger.info(f"   💰 {self.base_asset}: {base_balance:.6f}")
            logger.info(f"   💵 {self.quote_asset}: {quote_balance:.2f}")
            logger.info(f"   💎 Total Value: ${total_value_usdt:.2f} USDT")
            logger.info(f"   📊 Current {self.base_asset} Price: ${current_price:.2f}")
            
            return {
                'base_balance': base_balance,
                'quote_balance': quote_balance,
                'total_value_usdt': total_value_usdt,
                'current_price': current_price,
                'base_asset': self.base_asset,
                'quote_asset': self.quote_asset
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to check {self.exchange_name} account: {e}")
            import traceback
            traceback.print_exc()
            return None
    
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
    
    def crawl_data(self) -> Dict[str, Any]:
        """
        Crawl historical spot data for multiple timeframes from exchange
        Returns multi-timeframe OHLCV data
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
        
        # Use mainnet for data, fallback to testnet
        CLIENT = self.spot_client_mainnet if self.spot_client_mainnet else self.spot_client
        if not CLIENT:
            logger.error("❌ No spot client available")
            return {'timeframes': {}, 'error': 'No spot client initialized'}
        
        client_type = "MAINNET" if self.spot_client_mainnet else "TESTNET (fallback)"
        logger.info(f"📊 Data crawling using {client_type} client on {self.exchange_name} SPOT")
        
        timeframes_data = {}
        try:
            logger.info(f"🔄 Crawling SPOT data for timeframes: {self.timeframes}")
            
            for i, timeframe in enumerate(self.timeframes, 1):
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
                    
                    logger.info(f"📊 [{i}/{len(self.timeframes)}] Fetching {lookback} {timeframe} candles for {self.trading_pair}")
                    
                    df = CLIENT.get_klines(
                        symbol=self.trading_pair,
                        timeframe=timeframe,
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
                        df_more = CLIENT.get_klines(
                            symbol=self.trading_pair,
                            timeframe=timeframe,
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
                    
                    logger.info(f"✅ [{i}/{len(self.timeframes)}] Got {len(records)} {timeframe} candles")
                    
                except Exception as tf_err:
                    logger.error(f"❌ [{i}/{len(self.timeframes)}] Failed to fetch {timeframe}: {tf_err}")
                    timeframes_data[timeframe] = []
            
            report = {tf: len(candles) for tf, candles in timeframes_data.items()}
            logger.info(f"🎯 Completed crawling {len(timeframes_data)} TFs. Counts: {report}")
            
            return {
                "timeframes": timeframes_data,
                "crawl_timestamp": datetime.now().isoformat(),
                "total_timeframes": len(timeframes_data),
                "exchange": self.exchange_name,
                "market_type": "SPOT"
            }
            
        except Exception as e:
            logger.error(f"Error crawling multi-timeframe data: {e}")
            return {
                "timeframes": timeframes_data,
                "crawl_timestamp": datetime.now().isoformat(),
                "total_timeframes": len(timeframes_data),
                "error": str(e),
                "exchange": self.exchange_name,
                "market_type": "SPOT"
            }
    
    # ==================== ANALYSIS ====================
    
    def _calculate_spot_analysis(self, data: pd.DataFrame, historical_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate technical analysis for spot trading"""
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
                'volume_ratio': float(data['volume'].iloc[-1] / data['volume'].rolling(20).mean().iloc[-1]),
                'market_type': 'SPOT'
            }
            
            if historical_data:
                analysis['historical_data'] = historical_data
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error calculating spot analysis: {e}")
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
                    
                    timeframe_analysis = self._calculate_spot_analysis(df, historical_data)
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
                'exchange': self.exchange_name,
                'market_type': 'SPOT'
            }
            
            if 'current_price' in primary_analysis:
                combined_analysis['current_price'] = primary_analysis['current_price']
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing multi-timeframe data: {e}")
            return {'error': f'Multi-timeframe analysis error: {e}'}
    
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
            llm_analysis = await self.llm_service.analyze_market(
                symbol=self.trading_pair,
                timeframes_data=cleaned_timeframes_data,
                model=self.llm_model,
                bot_id=self.bot_id
            )
            
            if "error" in llm_analysis:
                logger.error(f"LLM analysis failed: {llm_analysis['error']}")
                return Action(action="HOLD", value=0.0, reason=f"LLM error: {llm_analysis['error']}")
            
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
                
                # Extract recommendation details
                entry_price = recommendation.get("entry_price", "Market")
                take_profit = recommendation.get("take_profit", "N/A")
                stop_loss = recommendation.get("stop_loss", "N/A")
                strategy = recommendation.get("strategy", "Multi-timeframe SPOT")
                risk_reward = recommendation.get("risk_reward", "N/A")
                
                if action == "CLOSE":
                    action = "SELL"
                
                if action not in ["BUY", "SELL", "HOLD"]:
                    action = "HOLD"
                    confidence = 0.0
                    reasoning = f"Invalid LLM action: {action}"
                
                logger.info(f"🤖 LLM: {action} ({confidence*100:.1f}%) - {reasoning[:50]}...")
                
                full_recommendation = {
                    "action": action,
                    "confidence": f"{confidence*100:.1f}%",
                    "entry_price": entry_price,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                    "strategy": strategy,
                    "risk_reward": risk_reward,
                    "reasoning": reasoning
                }
                
                return Action(
                    action=action,
                    value=confidence,
                    reason=f"[LLM-SPOT-{self.exchange_name}] {reasoning}",
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
                        reason=f"[CACHED-SPOT-{self.exchange_name}] {cached_result.get('reasoning', 'Cached LLM analysis')}"
                    )
                
                # Try to acquire lock
                logger.info(f"🔐 Attempting to acquire LLM lock for {self.trading_pair}...")
                if not self._acquire_llm_lock(self.trading_pair):
                    logger.info(f"⏸️  Lock not acquired, waiting 3s for cache...")
                    time.sleep(3)
                    cached_result = self._get_cached_llm_result(self.trading_pair, self.timeframes)
                    if cached_result:
                        logger.info(f"✅ Found cached result after wait")
                        return Action(
                            action=cached_result.get('action', 'HOLD'),
                            value=cached_result.get('confidence', 0.0),
                            reason=f"[WAITED-SPOT-{self.exchange_name}] {cached_result.get('reasoning', 'LLM from other worker')}"
                        )
                    else:
                        logger.warning("⚠️ No cached result after wait, falling back to technical")
                else:
                    logger.info(f"🤖 Generating LLM signal for SPOT {self.exchange_name}...")
                    
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
                                    logger.info(f"✅ LLM signal generated successfully: {llm_action.action}")
                                    cache_data = {
                                        'action': llm_action.action,
                                        'confidence': llm_action.value,
                                        'reasoning': llm_action.reason
                                    }
                                    self._cache_llm_result(self.trading_pair, self.timeframes, cache_data)
                                    self._release_llm_lock(self.trading_pair)
                                    return llm_action
                                else:
                                    logger.warning("⚠️ LLM signal returned None, falling back to technical")
                                    self._release_llm_lock(self.trading_pair)
                            except concurrent.futures.TimeoutError:
                                logger.warning("⏱️ LLM signal timed out after 60s")
                                self._release_llm_lock(self.trading_pair)
                            except Exception as e:
                                logger.warning(f"❌ LLM signal failed with exception: {e}")
                                self._release_llm_lock(self.trading_pair)
                                
                    except Exception as e:
                        logger.warning(f"Failed to setup LLM: {e}")
                        self._release_llm_lock(self.trading_pair)
                
                logger.info("Falling back to technical analysis...")
            
            # Fallback to technical analysis
            logger.info(f"Generating signal using technical analysis for SPOT {self.exchange_name}...")
            
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
            
            reason = f"[MULTI-TF-SPOT-{self.exchange_name}] {primary_signal.reason}"
            if total_timeframes > 0:
                reason += f" | Confirmation: {confirmations}/{total_timeframes}"
            
            # Create technical recommendation
            current_price = primary_analysis.get('current_price', 50000)
            if primary_signal.action == "BUY":
                entry_price = f"{current_price:.2f}"
                take_profit = f"{current_price * (1 + self.take_profit_pct):.2f}"
                stop_loss = f"{current_price * (1 - self.stop_loss_pct):.2f}"
            elif primary_signal.action == "SELL":
                entry_price = f"{current_price:.2f}"
                take_profit = f"{current_price * (1 - self.take_profit_pct):.2f}"
                stop_loss = f"{current_price * (1 + self.stop_loss_pct):.2f}"
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
                "strategy": f"Multi-timeframe SPOT ({self.exchange_name})",
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
    
    # ==================== POSITION SETUP (SPOT) ====================
    
    async def setup_position(self, action: Action, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Setup spot position with intelligent capital management
        
        SPOT-specific features:
        - No leverage (1x only)
        - Uses OCO orders for SL/TP (if supported)
        - Buys base asset with quote asset
        - Can use trailing stop loss
        """
        try:
            if action.action == "HOLD":
                return {
                    'status': 'success',
                    'action': 'HOLD',
                    'reason': action.reason,
                    'exchange': self.exchange_name,
                    'market_type': 'SPOT'
                }
            
            symbol = self.trading_pair
            
            # Get account balances
            account_info = self.spot_client.get_account_info()
            
            # Find quote balance (USDT, BUSD, etc.)
            quote_balance = 0.0
            balances = account_info.get('balances', [])
            for balance in balances:
                if balance.get('asset') == self.quote_asset:
                    quote_balance = float(balance.get('free', 0))
                    break
            
            if quote_balance <= self.min_notional:
                return {
                    'status': 'error',
                    'message': f'Insufficient {self.quote_asset} balance: ${quote_balance:.2f}',
                    'exchange': self.exchange_name,
                    'market_type': 'SPOT'
                }
            
            # Calculate risk metrics for capital management
            risk_metrics = self.capital_manager.calculate_risk_metrics({
                'availableBalance': quote_balance,
                'totalWalletBalance': quote_balance
            })
            
            # Prepare market data
            market_data = {
                'current_price': analysis.get('current_price', 0),
                'atr': analysis.get('primary_analysis', {}).get('atr', 0),
                'volatility': risk_metrics.volatility
            }
            
            # Get optimal position size
            logger.info("🧠 Calculating optimal SPOT position size...")
            position_recommendation = self.capital_manager.calculate_position_size(
                signal_confidence=action.value,
                risk_metrics=risk_metrics,
                market_data=market_data,
                llm_service=self.llm_service
            )
            
            logger.info(f"💰 Capital Management (SPOT):")
            logger.info(f"   Recommended Size: {position_recommendation.recommended_size_pct*100:.2f}%")
            logger.info(f"   Risk Level: {position_recommendation.risk_level}")
            logger.info(f"   Method: {position_recommendation.sizing_method}")
            
            optimal_position_size_pct = position_recommendation.recommended_size_pct
            logger.info(f"📊 Position sizing: {optimal_position_size_pct*100:.4f}% of balance (${quote_balance * optimal_position_size_pct:.2f})")
            
            if optimal_position_size_pct <= 0:
                return {
                    'status': 'info',
                    'action': 'HOLD',
                    'reason': f'Capital management recommends no position: {position_recommendation.reasoning}',
                    'exchange': self.exchange_name,
                    'market_type': 'SPOT'
                }
            
            # Get prices from recommendation
            entry_price = None
            take_profit_target = None
            stop_loss_target = None
            
            if action.recommendation:
                rec = action.recommendation
                try:
                    entry_str = str(rec.get('entry_price', '')).replace(',', '').strip()
                    if entry_str and entry_str not in ['Market', 'N/A', '']:
                        entry_price = float(entry_str)
                    
                    tp_str = str(rec.get('take_profit', '')).replace(',', '').strip()
                    if tp_str and tp_str != 'N/A':
                        import re
                        numbers = re.findall(r'\d+\.\d+', tp_str)
                        if numbers:
                            take_profit_target = float(numbers[0])
                    
                    sl_str = str(rec.get('stop_loss', '')).replace(',', '').strip()
                    if sl_str and sl_str != 'N/A':
                        import re
                        numbers = re.findall(r'\d+\.\d+', sl_str)
                        if numbers:
                            stop_loss_target = float(numbers[0])
                            
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse recommendation prices: {e}")
            
            # Get realtime price
            if not entry_price:
                try:
                    current_price = self.spot_client.get_current_price(symbol)
                    entry_price = current_price
                except Exception as e:
                    logger.error(f"Failed to get current price: {e}")
                    return {
                        'status': 'error',
                        'message': f'Failed to get market price: {e}',
                        'exchange': self.exchange_name,
                        'market_type': 'SPOT'
                    }
            
            # Calculate position value and quantity
            position_value = quote_balance * optimal_position_size_pct  # No leverage in spot
            quantity = position_value / entry_price
            logger.info(f"💵 Initial calculation: position_value=${position_value:.2f}, quantity={quantity:.8f}")
            
            # Round quantity to proper precision (exchange-specific)
            quantity = round(quantity, 6)  # Most exchanges support 6 decimals
            logger.info(f"🔢 After rounding: quantity={quantity:.6f}")
            
            # Check and adjust for minimum notional
            notional = quantity * entry_price
            logger.info(f"💰 Notional value: ${notional:.2f} (min required: ${self.min_notional})")
            if notional < self.min_notional:
                # Auto-adjust quantity to meet minimum notional
                logger.warning(f"⚠️ Order value ${notional:.2f} below minimum ${self.min_notional}, adjusting...")
                quantity = (self.min_notional * 1.1) / entry_price  # Add 10% buffer
                quantity = round(quantity, 6)
                notional = quantity * entry_price
                logger.info(f"✅ Adjusted quantity to {quantity:.6f} (notional: ${notional:.2f})")
                
                # Check if we have enough balance
                if notional > quote_balance:
                    return {
                        'status': 'error',
                        'message': f'Insufficient balance: ${quote_balance:.2f} < minimum order ${notional:.2f}',
                        'exchange': self.exchange_name,
                        'market_type': 'SPOT'
                    }
            
            logger.info(f"🚀 Opening SPOT {action.action} position on {self.exchange_name}:")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Quantity: {quantity:.6f} {self.base_asset}")
            logger.info(f"   Entry: ${entry_price:.2f}")
            logger.info(f"   Value: ${notional:.2f} {self.quote_asset}")
            
            # Place market order (BUY for spot)
            if action.action == "BUY":
                try:
                    order = self.spot_client.create_market_order(
                        symbol=symbol,
                        side="BUY",
                        quantity=f"{quantity:.6f}"
                    )
                except Exception as e:
                    logger.error(f"Failed to create market order: {e}")
                    return {
                        'status': 'error',
                        'message': f'Order failed: {e}',
                        'exchange': self.exchange_name,
                        'market_type': 'SPOT'
                    }
                
                # Binance Spot can return: FILLED, NEW, PARTIALLY_FILLED, CLOSED (for filled market orders)
                if not hasattr(order, 'status') or order.status not in ['FILLED', 'NEW', 'PARTIALLY_FILLED', 'CLOSED']:
                    return {
                        'status': 'error',
                        'message': f'Order failed with status: {getattr(order, "status", "UNKNOWN")}',
                        'exchange': self.exchange_name,
                        'market_type': 'SPOT'
                    }
                
                logger.info(f"✅ SPOT BUY order placed: {order.status}")
                
                # Calculate SL/TP prices for OCO order
                actual_entry = float(getattr(order, 'price', entry_price) or entry_price)
                stop_loss_price = stop_loss_target or (actual_entry * (1 - self.stop_loss_pct))
                take_profit_price = take_profit_target or (actual_entry * (1 + self.take_profit_pct))
                
                # Place OCO order (if supported)
                oco_order = None
                if self.use_oco_orders:
                    try:
                        logger.info(f"📊 Placing OCO order for SL/TP...")
                        oco_order = self.spot_client.create_oco_order(
                            symbol=symbol,
                            side="SELL",
                            quantity=f"{quantity:.6f}",
                            price=f"{take_profit_price:.2f}",  # Take profit limit price
                            stop_price=f"{stop_loss_price:.2f}",  # Stop loss trigger
                            stop_limit_price=f"{stop_loss_price * 0.995:.2f}"  # Stop limit (slightly below)
                        )
                        logger.info(f"✅ OCO order placed successfully")
                    except Exception as e:
                        logger.warning(f"Failed to place OCO order: {e}")
                        # Continue without OCO, will need manual SL/TP
                
                result = {
                    'status': 'success',
                    'action': 'BUY',
                    'market_type': 'SPOT',
                    'exchange': self.exchange_name,
                    'symbol': symbol,
                    'base_asset': self.base_asset,
                    'quote_asset': self.quote_asset,
                    'quantity': f"{quantity:.6f}",
                    'entry_price': actual_entry,
                    'position_value': notional,
                    'main_order_id': getattr(order, 'order_id', 'N/A'),
                    'stop_loss': {
                        'price': stop_loss_price,
                        'oco_order_id': getattr(oco_order, 'order_list_id', None) if oco_order else None,
                        'source': 'recommendation' if stop_loss_target else 'percentage'
                    },
                    'take_profit': {
                        'price': take_profit_price,
                        'oco_order_id': getattr(oco_order, 'order_list_id', None) if oco_order else None,
                        'source': 'recommendation' if take_profit_target else 'percentage'
                    },
                    'confidence': action.value,
                    'reason': action.reason,
                    'timestamp': datetime.now().isoformat(),
                    'capital_management': {
                        'recommended_size_pct': position_recommendation.recommended_size_pct * 100,
                        'risk_level': position_recommendation.risk_level,
                        'sizing_method': position_recommendation.sizing_method,
                        'reasoning': position_recommendation.reasoning
                    }
                }
                
                return result
            
            elif action.action == "SELL":
                # For SPOT, SELL means selling existing base asset
                # Check if we have enough base asset
                base_balance = 0.0
                for balance in balances:
                    if balance.get('asset') == self.base_asset:
                        base_balance = float(balance.get('free', 0))
                        break
                
                if base_balance < quantity:
                    return {
                        'status': 'error',
                        'message': f'Insufficient {self.base_asset} balance: {base_balance:.6f}',
                        'exchange': self.exchange_name,
                        'market_type': 'SPOT'
                    }
                
                try:
                    order = self.spot_client.create_market_order(
                        symbol=symbol,
                        side="SELL",
                        quantity=f"{quantity:.6f}"
                    )
                except Exception as e:
                    logger.error(f"Failed to create SELL order: {e}")
                    return {
                        'status': 'error',
                        'message': f'Order failed: {e}',
                        'exchange': self.exchange_name,
                        'market_type': 'SPOT'
                    }
                
                logger.info(f"✅ SPOT SELL order placed: {order.status}")
                
                result = {
                    'status': 'success',
                    'action': 'SELL',
                    'market_type': 'SPOT',
                    'exchange': self.exchange_name,
                    'symbol': symbol,
                    'quantity': f"{quantity:.6f}",
                    'entry_price': float(getattr(order, 'price', entry_price) or entry_price),
                    'main_order_id': getattr(order, 'order_id', 'N/A'),
                    'confidence': action.value,
                    'reason': action.reason,
                    'timestamp': datetime.now().isoformat()
                }
                
                return result
            
        except Exception as e:
            logger.error(f"Error setting up SPOT position: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'Position setup error: {e}',
                'exchange': self.exchange_name,
                'market_type': 'SPOT'
            }
    
    def save_transaction_to_db(self, trade_result: Dict[str, Any]):
        """
        Save SPOT trade transaction to MySQL database
        
        Args:
            trade_result: Dict containing trade execution details
        """
        try:
            from core.database import get_db
            from core import models
            from datetime import datetime
            from decimal import Decimal
            
            # Get database session
            db = next(get_db())
            
            # Determine action
            action = trade_result.get('action', '').upper()
            
            # Helper function to safely extract float
            def safe_float(value, default=0):
                if value is None:
                    return None
                if isinstance(value, dict):
                    value = value.get('price') or value.get('stopPrice') or value.get('triggerPrice') or default
                try:
                    return float(value) if value else default
                except (ValueError, TypeError):
                    return default
            
            entry_price = safe_float(trade_result.get('entry_price'), 0) or 0
            stop_loss_value = trade_result.get('stop_loss')
            stop_loss = safe_float(stop_loss_value) if stop_loss_value else None
            take_profit_value = trade_result.get('take_profit')
            take_profit = safe_float(take_profit_value) if take_profit_value else None
            
            # Calculate risk-reward ratio
            risk_reward_ratio = None
            if stop_loss and take_profit and entry_price > 0:
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                if risk > 0:
                    risk_reward_ratio = Decimal(str(round(reward / risk, 4)))
            
            # Create transaction record
            transaction = models.Transaction(
                # Identity & Ownership
                user_id=trade_result.get('user_id'),
                user_principal_id=trade_result.get('user_principal_id'),
                bot_id=trade_result.get('bot_id', self.bot_id),
                subscription_id=trade_result.get('subscription_id', self.subscription_id),
                prompt_id=trade_result.get('prompt_id'),
                
                # Trade Details (SPOT)
                action=action,
                position_side='LONG' if action == 'BUY' else 'SHORT',  # SPOT: BUY=LONG, SELL=SHORT
                symbol=trade_result.get('symbol', self.trading_pair),
                quantity=Decimal(str(trade_result.get('quantity', 0))),
                entry_price=Decimal(str(entry_price)),
                entry_time=datetime.now(),
                leverage=1,  # Always 1 for spot
                
                # Risk Management
                stop_loss=Decimal(str(stop_loss)) if stop_loss else None,
                take_profit=Decimal(str(take_profit)) if take_profit else None,
                risk_reward_ratio=risk_reward_ratio,
                
                # Order Info
                order_id=trade_result.get('main_order_id'),
                
                # LLM Strategy
                strategy_used=trade_result.get('strategy_name'),
                confidence=Decimal(str(trade_result.get('confidence', 0))) if trade_result.get('confidence') else None,
                reason=trade_result.get('reason'),
                
                # Status
                status='OPEN',
                
                # Timestamps
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Add to database
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            
            logger.info(f"✅ SPOT transaction saved to database with ID: {transaction.id}")
            logger.info(f"   Type: SPOT {action}, Entry: ${entry_price:.2f}, RR: {risk_reward_ratio or 'N/A'}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save SPOT transaction to database: {e}")
            import traceback
            traceback.print_exc()
    
    # ==================== TRADE EXECUTION ====================
    
    def execute_trade(self, signal: Action, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the SPOT trading signal"""
        try:
            if signal.action == "HOLD":
                return {
                    'status': 'success',
                    'action': 'HOLD',
                    'reason': signal.reason,
                    'exchange': self.exchange_name,
                    'market_type': 'SPOT',
                    'timestamp': datetime.now().isoformat()
                }
            
            current_price = analysis.get('current_price', 0)
            
            result = {
                'status': 'success',
                'action': signal.action,
                'market_type': 'SPOT',
                'exchange': self.exchange_name,
                'confidence': signal.value,
                'reason': signal.reason,
                'entry_price': current_price,
                'primary_timeframe': analysis.get('primary_timeframe', self.primary_timeframe),
                'timeframes_analyzed': list(analysis.get('multi_timeframe', {}).keys()),
                'timestamp': datetime.now().isoformat()
            }
            
            if signal.recommendation:
                result['strategy'] = signal.recommendation.get('strategy', 'N/A')
                result['risk_reward'] = signal.recommendation.get('risk_reward', 'N/A')
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing SPOT trade: {e}")
            return {
                'status': 'error',
                'message': f'Trade execution error: {e}',
                'exchange': self.exchange_name,
                'market_type': 'SPOT'
            }

# ==================== FACTORY FUNCTION ====================

def create_universal_spot_bot(
    exchange: str,
    user_principal_id: str,
    config: Dict[str, Any] = None,
    subscription_id: int = None
) -> UniversalSpotBot:
    """
    Factory function to create Universal Spot Bot
    
    Args:
        exchange: Exchange name (BINANCE, BYBIT, OKX, BITGET, HUOBI, KRAKEN)
        user_principal_id: ICP Principal ID
        config: Bot configuration (optional)
        subscription_id: Subscription ID (optional)
    
    Returns:
        Configured UniversalSpotBot instance
    """
    default_config = {
        'exchange': exchange.upper(),
        'trading_pair': 'BTC/USDT',
        'testnet': True,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.04,
        'position_size_pct': 0.10,
        'timeframes': ['30m', '1h', '4h'],
        'primary_timeframe': '1h',
        'use_llm_analysis': True,
        'llm_model': 'openai',
        'use_oco_orders': True,
        'trailing_stop': False
    }
    
    if config:
        default_config.update(config)
    
    return UniversalSpotBot(
        config=default_config,
        user_principal_id=user_principal_id,
        subscription_id=subscription_id
    )

if __name__ == "__main__":
    print("Universal Spot Bot Template - Multi-Exchange Support")
    print("Supported exchanges:", ', '.join(UniversalSpotBot.SUPPORTED_EXCHANGES))
    print("\nUse create_universal_spot_bot() factory function to create bot instances")


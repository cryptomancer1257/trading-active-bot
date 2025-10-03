"""
Universal Futures Trading Bot Template - Multi-Exchange Support
Supports: Binance, Bybit, OKX, Bitget, Huobi/HTX, Kraken

Advanced futures trading bot with:
- Multi-exchange support via unified interface
- LLM AI analysis (OpenAI/Claude/Gemini)
- Multi-timeframe analysis
- Capital management system
- Stop loss & take profit
- Leverage trading
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
    BaseFuturesExchange,
    FuturesOrderInfo,
    FuturesPosition,
    create_futures_exchange
)

# Services
from services.llm_integration import create_llm_service
from bot_files.capital_management import CapitalManagement, RiskMetrics, PositionSizeRecommendation
from core.api_key_manager import get_bot_api_keys

logger = logging.getLogger(__name__)

class UniversalFuturesBot(CustomBot):
    """Universal Futures Trading Bot with Multi-Exchange Support"""
    
    SUPPORTED_EXCHANGES = ['BINANCE', 'BYBIT', 'OKX', 'BITGET', 'HUOBI', 'HTX', 'KRAKEN']
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str] = None, 
                 user_principal_id: str = None, subscription_id: int = None):
        """
        Initialize Universal Futures Bot
        
        Args:
            config: Bot configuration including:
                - exchange: Exchange name (BINANCE, BYBIT, OKX, BITGET, HUOBI, KRAKEN)
                - trading_pair: Trading pair (e.g., 'BTCUSDT')
                - leverage: Leverage multiplier (default: 5)
                - stop_loss_pct: Stop loss percentage (default: 0.02)
                - take_profit_pct: Take profit percentage (default: 0.04)
                - position_size_pct: Position size percentage (default: 0.1)
                - testnet: Use testnet (default: True)
                - timeframes: List of timeframes for analysis (default: ['30m', '1h', '4h'])
                - use_llm_analysis: Enable LLM analysis (default: True)
                - llm_model: LLM model to use (default: 'openai')
            api_keys: LLM API keys (optional)
            user_principal_id: User principal ID for database lookup
            subscription_id: Subscription ID for bot management
        """
        super().__init__(config, api_keys)
        
        # Bot identification
        self.bot_id = config.get('bot_id')
        self.subscription_id = subscription_id
        logger.info(f"🤖 [BOT INIT] bot_id={self.bot_id}, subscription_id={subscription_id}")
        
        # Exchange configuration - support both 'exchange_type' and 'exchange' keys
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
        
        logger.info(f"🌐 Using exchange: {self.exchange_name}")
        
        # Trading configuration
        raw_trading_pair = config.get('trading_pair', 'BTCUSDT')
        self.trading_pair = raw_trading_pair.replace('/', '')
        
        self.leverage = config.get('leverage', 5)
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)
        self.take_profit_pct = config.get('take_profit_pct', 0.04)
        self.position_size_pct = config.get('position_size_pct', 0.1)
        self.testnet = config.get('testnet', True)
        
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
        
        # Create exchange client using factory
        try:
            self.futures_client = create_futures_exchange(
                exchange_name=self.exchange_name,
                api_key=db_credentials['api_key'],
                api_secret=db_credentials['api_secret'],
                passphrase=db_credentials.get('passphrase', ''),
                testnet=db_credentials['testnet']
            )
            logger.info(f"✅ {self.exchange_name} client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize {self.exchange_name} client: {e}")
            raise
        
        # Try to get mainnet client for data crawling
        try:
            db_credentials_mainnet = get_bot_api_keys(
                user_principal_id=user_principal_id,
                exchange=self.exchange_name,
                is_testnet=False,
                subscription_id=subscription_id
            )
            
            if db_credentials_mainnet:
                self.futures_client_mainnet = create_futures_exchange(
                    exchange_name=self.exchange_name,
                    api_key=db_credentials_mainnet['api_key'],
                    api_secret=db_credentials_mainnet['api_secret'],
                    passphrase=db_credentials_mainnet.get('passphrase', ''),
                    testnet=False
                )
                logger.info("✅ Mainnet client initialized for data crawling")
            else:
                # Create public mainnet client for data
                logger.warning("⚠️ No mainnet credentials, creating public client for data")
                self.futures_client_mainnet = create_futures_exchange(
                    exchange_name=self.exchange_name,
                    api_key="",
                    api_secret="",
                    testnet=False
                )
                logger.info("✅ Public mainnet client created for accurate market data")
        except Exception as e:
            logger.warning(f"Could not initialize mainnet client: {e}")
            self.futures_client_mainnet = None
        
        # Initialize LLM service
        self.llm_service = None
        if self.use_llm_analysis:
            try:
                llm_config = {
                    'openai_api_key': os.getenv('OPENAI_API_KEY'),
                    'claude_api_key': os.getenv('CLAUDE_API_KEY'),
                    'gemini_api_key': os.getenv('GEMINI_API_KEY'),
                    'openai_model': config.get('openai_model', 'gpt-4o'),
                    'claude_model': config.get('claude_model', 'claude-3-5-sonnet-20241022'),
                    'gemini_model': config.get('gemini_model', 'gemini-1.5-pro')
                }
                self.llm_service = create_llm_service(llm_config)
                logger.info(f"LLM service initialized with model: {self.llm_model}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
                self.use_llm_analysis = False
                logger.warning("Falling back to traditional technical analysis")
        
        # Initialize Capital Management System
        capital_config = {
            'base_position_size_pct': config.get('base_position_size_pct', 0.02),
            'max_position_size_pct': config.get('max_position_size_pct', 0.10),
            'max_portfolio_exposure': config.get('max_portfolio_exposure', 0.30),
            'max_drawdown_threshold': config.get('max_drawdown_threshold', 0.20),
            'volatility_threshold_low': config.get('volatility_threshold_low', 0.02),
            'volatility_threshold_high': config.get('volatility_threshold_high', 0.08),
            'kelly_multiplier': config.get('kelly_multiplier', 0.25),
            'min_win_rate': config.get('min_win_rate', 0.35),
            'use_llm_capital_management': config.get('use_llm_capital_management', True),
            'llm_capital_weight': config.get('llm_capital_weight', 0.40),
            'sizing_method': config.get('sizing_method', 'llm_hybrid')
        }
        
        self.capital_manager = CapitalManagement(capital_config)
        
        logger.info(f"✅ Universal Futures Bot initialized")
        logger.info(f"   Exchange: {self.exchange_name}")
        logger.info(f"   Trading Pair: {self.trading_pair}")
        logger.info(f"   Leverage: {self.leverage}x")
        logger.info(f"   Timeframes: {self.timeframes}")
        logger.info(f"   LLM Analysis: {'Enabled (' + self.llm_model + ')' if self.use_llm_analysis else 'Disabled'}")
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
            logger.info(f"🚀 [EXECUTE ALGORITHM] Starting trading cycle for {self.trading_pair}")
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
            
            logger.info(f"✅ [EXECUTE ALGORITHM] Completed - Signal: {signal.name}")
            return signal
            
        except Exception as e:
            logger.error(f"❌ [EXECUTE ALGORITHM] Error: {e}")
            import traceback
            traceback.print_exc()
            return Action.HOLD
    
    def check_account_status(self) -> Optional[Dict[str, Any]]:
        """
        Check account status and positions across any exchange
        
        Returns:
            Dict with account info:
            - available_balance: Available balance
            - total_balance: Total wallet balance
            - active_positions: Number of active positions
            - positions: List of position objects
        """
        try:
            logger.info(f"\n💼 CHECKING {self.exchange_name} ACCOUNT STATUS...")
            logger.info("=" * 50)
            
            # Get account info from exchange
            account_info = self.futures_client.get_account_info()
            available_balance = float(account_info.get('availableBalance', 0))
            total_wallet_balance = float(account_info.get('totalWalletBalance', 0))
            
            mode = "🧪 TESTNET" if self.testnet else "🔴 LIVE"
            logger.info(f"{mode} Account Balance:")
            logger.info(f"   💰 Available: ${available_balance:,.2f} USDT")
            logger.info(f"   💎 Total Wallet: ${total_wallet_balance:,.2f} USDT")
            
            # Get positions
            positions = self.futures_client.get_positions()
            active_positions = len([p for p in positions if float(getattr(p, "size", 0)) != 0])
            
            logger.info(f"   📊 Active Positions: {active_positions}")
            
            return {
                'available_balance': available_balance,
                'total_balance': total_wallet_balance,
                'active_positions': active_positions,
                'positions': positions
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
        Crawl historical data for multiple timeframes from exchange
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
        
        self.trading_pair = self.trading_pair.replace('/', '')
        
        # Use mainnet for data, fallback to testnet
        CLIENT = self.futures_client_mainnet if self.futures_client_mainnet else self.futures_client
        if not CLIENT:
            logger.error("❌ No futures client available")
            return {'timeframes': {}, 'error': 'No futures client initialized'}
        
        client_type = "MAINNET" if self.futures_client_mainnet else "TESTNET (fallback)"
        logger.info(f"📊 Data crawling using {client_type} client on {self.exchange_name}")
        
        timeframes_data = {}
        try:
            logger.info(f"🔄 Crawling data for timeframes: {self.timeframes}")
            
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
                        df_more = CLIENT.get_klines(
                            symbol=self.trading_pair,
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
                strategy = recommendation.get("strategy", "Multi-timeframe")
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
    
    # ==================== POSITION SETUP ====================
    
    async def setup_position(self, action: Action, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Setup futures position with capital management"""
        try:
            if action.action == "HOLD":
                return {
                    'status': 'success',
                    'action': 'HOLD',
                    'reason': action.reason,
                    'exchange': self.exchange_name
                }
            
            self.trading_pair = self.trading_pair.replace('/', '')
            
            # Get account info
            account_info = self.futures_client.get_account_info()
            available_balance = float(account_info.get('availableBalance', 0))
            
            if available_balance <= 0:
                return {'status': 'error', 'message': 'No available balance', 'exchange': self.exchange_name}
            
            # Calculate risk metrics
            risk_metrics = self.capital_manager.calculate_risk_metrics(account_info)
            
            market_data = {
                'current_price': analysis.get('current_price', 0),
                'atr': analysis.get('primary_analysis', {}).get('atr', 0),
                'volatility': risk_metrics.volatility
            }
            
            # Get optimal position size
            logger.info("🧠 Calculating optimal position size...")
            position_recommendation = self.capital_manager.calculate_position_size(
                signal_confidence=action.value,
                risk_metrics=risk_metrics,
                market_data=market_data,
                llm_service=self.llm_service
            )
            
            logger.info(f"💰 Capital Management:")
            logger.info(f"   Recommended Size: {position_recommendation.recommended_size_pct*100:.2f}%")
            logger.info(f"   Risk Level: {position_recommendation.risk_level}")
            logger.info(f"   Method: {position_recommendation.sizing_method}")
            
            optimal_position_size_pct = position_recommendation.recommended_size_pct
            
            if optimal_position_size_pct <= 0:
                return {
                    'status': 'info',
                    'action': 'HOLD',
                    'reason': f'Capital management recommends no position',
                    'exchange': self.exchange_name
                }
            
            # Get entry/TP/SL prices
            entry_price = None
            take_profit_target = None
            stop_loss_target = None
            
            if action.recommendation:
                rec = action.recommendation
                try:
                    entry_str = rec.get('entry_price', '').replace(',', '').strip()
                    if entry_str and entry_str != 'Market' and entry_str != 'N/A':
                        entry_price = float(entry_str)
                    
                    tp_str = rec.get('take_profit', '').replace(',', '').strip()
                    if tp_str and tp_str != 'N/A':
                        import re
                        numbers = re.findall(r'\d+\.\d+', tp_str)
                        if numbers:
                            take_profit_target = float(numbers[0])
                    
                    sl_str = rec.get('stop_loss', '').replace(',', '').strip()
                    if sl_str and sl_str != 'N/A':
                        import re
                        numbers = re.findall(r'\d+\.\d+', sl_str)
                        if numbers:
                            stop_loss_target = float(numbers[0])
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse prices: {e}")
            
            if not entry_price:
                current_price = analysis.get('current_price', 0)
                if current_price <= 0:
                    return {'status': 'error', 'message': 'Invalid current price', 'exchange': self.exchange_name}
                entry_price = current_price
            
            # Set leverage
            symbol = self.trading_pair
            if not self.futures_client.set_leverage(symbol, self.leverage):
                logger.warning(f"Failed to set leverage on {self.exchange_name}")
            
            # Calculate position size
            position_value = available_balance * optimal_position_size_pct * self.leverage
            quantity = position_value / entry_price
            
            quantity = round(quantity, 3)
            quantity_str = f"{quantity:.3f}"
            
            logger.info(f"🚀 Opening {action.action} position on {self.exchange_name}:")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Quantity: {quantity_str}")
            logger.info(f"   Entry: ${entry_price:.2f}")
            logger.info(f"   Leverage: {self.leverage}x")
            
            # Place market order
            order = self.futures_client.create_market_order(symbol, action.action, quantity_str)
            
            if order.status not in ['FILLED', 'NEW', 'PENDING']:
                return {
                    'status': 'error',
                    'message': f'Order failed: {order.status}',
                    'exchange': self.exchange_name
                }
            
            logger.info(f"✅ Market order placed on {self.exchange_name}: {order.status}")
            
            # Calculate SL/TP prices
            if action.action == "BUY":
                stop_loss_price = stop_loss_target if stop_loss_target else entry_price * (1 - self.stop_loss_pct)
                take_profit_price = take_profit_target if take_profit_target else entry_price * (1 + self.take_profit_pct)
                sl_side = "SELL"
                tp_side = "SELL"
            else:  # SELL
                stop_loss_price = stop_loss_target if stop_loss_target else entry_price * (1 + self.stop_loss_pct)
                take_profit_price = take_profit_target if take_profit_target else entry_price * (1 - self.take_profit_pct)
                sl_side = "BUY"
                tp_side = "BUY"
            
            # Place managed orders (SL + TP)
            try:
                current_ticker = self.futures_client.get_ticker(symbol)
                current_market_price = float(current_ticker['price'])
                
                # Validate and adjust prices
                min_distance = current_market_price * 0.001
                adjusted_stop_price = stop_loss_price
                adjusted_tp_price = take_profit_price
                
                if action.action == "BUY":
                    if stop_loss_price >= current_market_price:
                        adjusted_stop_price = current_market_price * (1 - max(self.stop_loss_pct, 0.005))
                        logger.warning(f"⚠️ SL adjusted: {stop_loss_price:.2f} → {adjusted_stop_price:.2f}")
                    
                    if current_market_price - adjusted_stop_price < min_distance:
                        adjusted_stop_price = current_market_price - min_distance
                    
                    if take_profit_price <= current_market_price:
                        adjusted_tp_price = current_market_price * (1 + max(self.take_profit_pct, 0.01))
                        logger.warning(f"⚠️ TP adjusted: {take_profit_price:.2f} → {adjusted_tp_price:.2f}")
                else:  # SELL
                    if stop_loss_price <= current_market_price:
                        adjusted_stop_price = current_market_price * (1 + max(self.stop_loss_pct, 0.005))
                        logger.warning(f"⚠️ SL adjusted: {stop_loss_price:.2f} → {adjusted_stop_price:.2f}")
                    
                    if take_profit_price >= current_market_price:
                        adjusted_tp_price = current_market_price * (1 - max(self.take_profit_pct, 0.01))
                        logger.warning(f"⚠️ TP adjusted: {take_profit_price:.2f} → {adjusted_tp_price:.2f}")
                
                managed_orders = self.futures_client.create_managed_orders(
                    symbol=symbol,
                    side=sl_side,
                    quantity=quantity_str,
                    stop_price=f"{adjusted_stop_price:.2f}",
                    take_profit_price=f"{adjusted_tp_price:.2f}",
                    reduce_only=True
                )
                
                sl_order = managed_orders['stop_loss_order']
                tp_orders = managed_orders['take_profit_orders']
                
                logger.info(f"✅ Managed orders placed on {self.exchange_name}")
                
            except Exception as e:
                logger.error(f"Failed to place managed orders: {e}")
                sl_order = None
                tp_orders = None
            
            result = {
                'status': 'success',
                'action': action.action,
                'exchange': self.exchange_name,
                'symbol': symbol,
                'quantity': quantity_str,
                'entry_price': entry_price,
                'leverage': self.leverage,
                'position_value': position_value,
                'main_order_id': order.order_id,
                'stop_loss': {
                    'price': stop_loss_price,
                    'order_id': sl_order.get('order_id') if sl_order else None,
                    'source': 'recommendation' if stop_loss_target else 'percentage'
                },
                'take_profit': {
                    'price': take_profit_price,
                    'order_ids': [tp.get('order_id') for tp in tp_orders] if tp_orders else [None],
                    'source': 'recommendation' if take_profit_target else 'percentage'
                },
                'confidence': action.value,
                'reason': action.reason,
                'timestamp': datetime.now().isoformat(),
                'capital_management': {
                    'recommended_size_pct': position_recommendation.recommended_size_pct * 100,
                    'risk_level': position_recommendation.risk_level,
                    'method': position_recommendation.sizing_method
                }
            }
            
            if action.recommendation:
                result['recommendation_used'] = True
                result['strategy'] = action.recommendation.get('strategy', 'N/A')
            
            return result
            
        except Exception as e:
            logger.error(f"Error setting up position: {e}")
            return {
                'status': 'error',
                'message': f'Position setup error: {e}',
                'exchange': self.exchange_name
            }
    
    # ==================== TRADE EXECUTION ====================
    
    def execute_trade(self, signal: Action, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the trading signal"""
        try:
            if signal.action == "HOLD":
                return {
                    'status': 'success',
                    'action': 'HOLD',
                    'reason': signal.reason,
                    'exchange': self.exchange_name,
                    'timestamp': datetime.now().isoformat()
                }
            
            # For real trading would call setup_position
            # For testing return signal info
            current_price = analysis.get('current_price', 0)
            
            result = {
                'status': 'success',
                'action': signal.action,
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
            logger.error(f"Error executing trade: {e}")
            return {
                'status': 'error',
                'message': f'Trade execution error: {e}',
                'exchange': self.exchange_name
            }

# ==================== FACTORY FUNCTION ====================

def create_universal_futures_bot(
    exchange: str,
    user_principal_id: str,
    config: Dict[str, Any] = None,
    subscription_id: int = None
) -> UniversalFuturesBot:
    """
    Factory function to create Universal Futures Bot
    
    Args:
        exchange: Exchange name (BINANCE, BYBIT, OKX, BITGET, HUOBI, KRAKEN)
        user_principal_id: ICP Principal ID
        config: Bot configuration (optional)
        subscription_id: Subscription ID (optional)
    
    Returns:
        Configured UniversalFuturesBot instance
    """
    default_config = {
        'exchange': exchange.upper(),
        'trading_pair': 'BTCUSDT',
        'testnet': True,
        'leverage': 5,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.04,
        'position_size_pct': 0.05,
        'timeframes': ['30m', '1h', '4h'],
        'primary_timeframe': '1h',
        'use_llm_analysis': True,
        'llm_model': 'openai'
    }
    
    if config:
        default_config.update(config)
    
    return UniversalFuturesBot(
        config=default_config,
        user_principal_id=user_principal_id,
        subscription_id=subscription_id
    )

if __name__ == "__main__":
    print("Universal Futures Bot Template - Multi-Exchange Support")
    print("Supported exchanges:", ', '.join(UniversalFuturesBot.SUPPORTED_EXCHANGES))
    print("\nUse create_universal_futures_bot() factory function to create bot instances")


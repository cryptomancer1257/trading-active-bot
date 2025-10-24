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
        exchange_raw = config.get('exchange_type') or config.get('exchange') or 'BINANCE'
        # Handle enum or string
        if hasattr(exchange_raw, 'value'):
            self.exchange_name = str(exchange_raw.value).upper()
        else:
            self.exchange_name = str(exchange_raw).upper()
        
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
                # Get developer_id and db from config (passed by tasks.py)
                developer_id = config.get('developer_id')
                db = config.get('db')
                bot_id = config.get('bot_id')
                
                # Get bot's preferred LLM provider from config (set in UI)
                preferred_provider = config.get('llm_provider')  # "openai", "claude", "gemini"
                
                if preferred_provider:
                    logger.info(f"🎯 Bot configured to use LLM provider: {preferred_provider}")
                
                # Note: Platform now manages LLM models automatically
                # No need to override model - platform will select the best model for the provider
                
                # Create LLM service (platform-managed)
                self.llm_service = create_llm_service(
                    config={},  # Empty config - platform provides everything
                    developer_id=developer_id,
                    db=db,
                    preferred_provider=preferred_provider,  # ✅ Pass bot's preference!
                    bot_id=bot_id,
                    subscription_id=subscription_id  # ✅ Pass subscription_id for usage tracking
                )
                
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
    
    async def setup_position(self, action: Action, analysis: Dict[str, Any], subscription = None) -> Dict[str, Any]:
        """
        Setup futures position with intelligent capital management and stop loss/take profit
        Works across all supported exchanges (Binance, Bybit, OKX, Bitget, Huobi, Kraken)
        
        Args:
            action: Trading action (BUY/SELL/HOLD) from signal generation
            analysis: Market analysis data
            subscription: Subscription object (needed for risk_config)
        """
        try:
            if action.action == "HOLD":
                return {
                    'status': 'success',
                    'action': 'HOLD',
                    'reason': action.reason,
                    'exchange': self.exchange_name
                }
            
            # Ensure trading pair format (no slash)
            symbol = self.trading_pair.replace('/', '')
            
            # Get account information for capital management
            account_info = self.futures_client.get_account_info()
            available_balance = float(account_info.get('availableBalance', 0))
            
            if available_balance <= 0:
                return {
                    'status': 'error',
                    'message': 'No available balance for trading',
                    'exchange': self.exchange_name
                }
            
            # Calculate risk metrics for position sizing
            risk_metrics = self.capital_manager.calculate_risk_metrics(account_info)
            
            # Prepare market data for capital management
            market_data = {
                'current_price': analysis.get('current_price', 0),
                'atr': analysis.get('primary_analysis', {}).get('atr', 0),
                'volatility': risk_metrics.volatility
            }
            
            # Get optimal position size using capital management system
            logger.info("🧠 Calculating optimal position size using capital management...")
            position_recommendation = self.capital_manager.calculate_position_size(
                signal_confidence=action.value,
                risk_metrics=risk_metrics,
                market_data=market_data,
                llm_service=self.llm_service
            )
            
            logger.info(f"💰 Capital Management Recommendation:")
            logger.info(f"   Recommended Size: {position_recommendation.recommended_size_pct*100:.2f}%")
            logger.info(f"   Risk Level: {position_recommendation.risk_level}")
            logger.info(f"   Method: {position_recommendation.sizing_method}")
            
            # Use recommended position size
            optimal_position_size_pct = position_recommendation.recommended_size_pct
            
            # Apply Risk Config limits to Capital Management recommendation
            if subscription and hasattr(subscription, 'bot') and hasattr(subscription.bot, 'risk_config'):
                risk_config_dict = subscription.bot.risk_config
                if risk_config_dict:
                    try:
                        from core import schemas
                        risk_config = schemas.RiskConfig(**risk_config_dict)
                        
                        # Enforce max_position_size limit
                        if risk_config.max_position_size:
                            max_size_decimal = risk_config.max_position_size / 100  # Convert % to decimal
                            if optimal_position_size_pct > max_size_decimal:
                                logger.warning(f"⚠️ Position size capped by Risk Config:")
                                logger.warning(f"   Capital Mgmt Recommended: {optimal_position_size_pct*100:.2f}%")
                                logger.warning(f"   Risk Config Max: {risk_config.max_position_size}%")
                                logger.warning(f"   Using: {risk_config.max_position_size}%")
                                optimal_position_size_pct = max_size_decimal
                        
                        logger.info(f"✅ Final Position Size: {optimal_position_size_pct*100:.2f}% (after risk config limits)")
                    except Exception as e:
                        logger.warning(f"Failed to apply risk config limits: {e}")
            
            if optimal_position_size_pct <= 0:
                return {
                    'status': 'info',
                    'action': 'HOLD',
                    'reason': f'Capital management recommends no position: {position_recommendation.reasoning}',
                    'exchange': self.exchange_name
                }
            
            # Get entry price from LLM recommendation (if provided)
            entry_price = None
            
            if action.recommendation:
                rec = action.recommendation
                try:
                    # Parse entry price only (TP/SL will be calculated from risk config)
                    entry_str = str(rec.get('entry_price', '')).replace(',', '').strip()
                    if entry_str and entry_str not in ['Market', 'N/A', '']:
                        entry_price = float(entry_str)
                            
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse recommendation entry price: {e}")
            
            # Fallback to current market price
            if not entry_price:
                current_price = analysis.get('current_price', 0)
                if current_price <= 0:
                    return {
                        'status': 'error',
                        'message': 'Invalid current price',
                        'exchange': self.exchange_name
                    }
                entry_price = current_price
            
            # Determine leverage (use risk_config max_leverage if available)
            leverage_to_use = self.leverage  # Default
            
            if subscription and hasattr(subscription, 'bot') and hasattr(subscription.bot, 'risk_config'):
                risk_config_dict = subscription.bot.risk_config
                if risk_config_dict:
                    try:
                        from core import schemas
                        risk_config = schemas.RiskConfig(**risk_config_dict)
                        if risk_config.max_leverage:
                            # Use the LOWER of bot default and risk config max
                            leverage_to_use = min(self.leverage, risk_config.max_leverage)
                            if leverage_to_use < self.leverage:
                                logger.warning(f"⚠️ Leverage capped by Risk Config:")
                                logger.warning(f"   Bot Default: {self.leverage}x")
                                logger.warning(f"   Risk Config Max: {risk_config.max_leverage}x")
                                logger.warning(f"   Using: {leverage_to_use}x")
                            else:
                                logger.info(f"✅ Using Risk Config Max Leverage: {leverage_to_use}x")
                    except Exception as e:
                        logger.warning(f"Failed to read risk config leverage: {e}")
            
            # Setup leverage - ignore if already set (common with Bybit)
            try:
                self.futures_client.set_leverage(symbol, leverage_to_use)
                logger.info(f"✅ Set leverage to {leverage_to_use}x on {self.exchange_name}")
            except Exception as e:
                error_msg = str(e).lower()
                # Bybit returns "leverage not modified" if already set - this is OK
                if 'leverage not modified' in error_msg or 'leverage is already set' in error_msg:
                    logger.info(f"✅ Leverage already at {self.leverage}x on {self.exchange_name}")
                else:
                    # Log but continue - leverage might already be correct
                    logger.warning(f"⚠️ Leverage setup warning on {self.exchange_name}: {e} (continuing anyway)")
            
            # Get REALTIME market price right before placing order (prevent stale price errors)
            try:
                realtime_ticker = self.futures_client.get_ticker(symbol)
                realtime_price = float(realtime_ticker['price'])
                logger.info(f"📊 Realtime market price: ${realtime_price:.2f} (analysis price was ${entry_price:.2f})")
                
                # Use realtime price for quantity calculation to ensure accuracy
                actual_entry_price = realtime_price
            except Exception as e:
                logger.warning(f"Failed to get realtime price, using analysis price: {e}")
                actual_entry_price = entry_price
            
            # Get exchange minimums for this symbol
            precision_info = self.futures_client.get_symbol_precision(symbol)
            min_qty = precision_info.get('minQty', 0.001)
            step_size = float(precision_info.get('stepSize', '0.001'))
            min_notional = precision_info.get('minNotional', 5)
            
            # Calculate position size with realtime price (use leverage_to_use from risk config)
            position_value = available_balance * optimal_position_size_pct * leverage_to_use
            quantity = position_value / actual_entry_price
            
            # Round to proper precision based on step size
            quantity = round(quantity / step_size) * step_size
            
            # Check if quantity meets exchange minimum
            notional_value = quantity * actual_entry_price
            if quantity < min_qty or notional_value < min_notional:
                logger.warning(f"⚠️ Calculated quantity {quantity} below minimum requirements:")
                logger.warning(f"   Min Quantity: {min_qty}, Min Notional: ${min_notional}")
                
                # Use exchange minimum instead
                quantity = max(min_qty, min_notional / actual_entry_price)
                quantity = round(quantity / step_size) * step_size
                notional_value = quantity * actual_entry_price
                
                # Check if account has enough balance for minimum order
                required_balance = notional_value / leverage_to_use
                if required_balance > available_balance:
                    # Extract base asset from trading pair (e.g., BTCUSDT -> BTC)
                    base_asset = self.trading_pair.replace('USDT', '').replace('/', '')
                    return {
                        'status': 'error',
                        'message': f'Insufficient balance: ${available_balance:.2f} USDT. ' +
                                 f'Minimum order requires ${required_balance:.2f} USDT ' +
                                 f'({min_qty} {base_asset} @ ${actual_entry_price:.2f} with {leverage_to_use}x leverage)',
                        'exchange': self.exchange_name,
                        'min_balance_required': required_balance,
                        'current_balance': available_balance
                    }
                
                logger.info(f"✅ Adjusted to exchange minimum: {quantity} (notional: ${notional_value:.2f})")
            
            # Format quantity string with proper precision
            decimals = precision_info.get('quantityPrecision', 3)
            quantity_str = f"{quantity:.{decimals}f}"
            
            logger.info(f"🚀 Opening {action.action} position on {self.exchange_name}:")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Quantity: {quantity_str}")
            logger.info(f"   Entry (Realtime): ${actual_entry_price:.2f}")
            logger.info(f"   Notional Value: ${notional_value:.2f}")
            logger.info(f"   Leverage: {leverage_to_use}x")
            
            # Place market order (NO PRICE for market orders!)
            try:
                order = self.futures_client.create_market_order(symbol, action.action, quantity_str)
            except Exception as e:
                logger.error(f"Failed to create market order: {e}")
                return {
                    'status': 'error',
                    'message': f'Position setup error: {e}',
                    'exchange': self.exchange_name
                }
            
            # Check order status (PENDING is valid for Bybit market orders)
            if not hasattr(order, 'status') or order.status not in ['FILLED', 'NEW', 'PENDING']:
                return {
                    'status': 'error',
                    'message': f'Order failed with status: {getattr(order, "status", "UNKNOWN")}',
                    'exchange': self.exchange_name
                }
            
            logger.info(f"✅ Market order placed successfully: {order.status}")
            logger.info(f"📋 Order details: ID={order.order_id}, Symbol={order.symbol}, Qty={order.quantity}")
            
            # Validate order_id
            if not order.order_id or order.order_id == '':
                logger.error(f"❌ CRITICAL: Order created but NO order_id returned from {self.exchange_name}!")
                logger.error(f"   Order object: {order}")
            
            # Wait for position to be settled on exchange before placing SL/TP
            import time
            time.sleep(1)  # 1 second delay to ensure position is registered
            logger.info("⏳ Position settled, now placing SL/TP orders...")
            
            # Calculate stop loss and take profit prices from Risk Config
            # Get risk config from bot (developer-configured risk parameters)
            from core import schemas
            
            # Default percentages (fallback if risk config not set)
            stop_loss_pct = self.stop_loss_pct  # Default from bot config
            take_profit_pct = self.take_profit_pct  # Default from bot config
            
            # Try to get risk config from subscription
            risk_config_dict = None
            if subscription and hasattr(subscription, 'bot') and hasattr(subscription.bot, 'risk_config'):
                risk_config_dict = subscription.bot.risk_config
            
            # Override with risk config if available
            if risk_config_dict:
                try:
                    risk_config = schemas.RiskConfig(**risk_config_dict)
                    if risk_config.stop_loss_percent:
                        stop_loss_pct = risk_config.stop_loss_percent / 100  # Convert to decimal
                        logger.info(f"📊 Using Risk Config SL: {risk_config.stop_loss_percent}%")
                    if risk_config.take_profit_percent:
                        take_profit_pct = risk_config.take_profit_percent / 100  # Convert to decimal
                        logger.info(f"📊 Using Risk Config TP: {risk_config.take_profit_percent}%")
                except Exception as e:
                    logger.warning(f"Failed to parse risk config, using defaults: {e}")
            else:
                logger.info(f"📊 Using default TP/SL from bot config (no risk_config found)")
            
            # Calculate TP/SL based on entry price and risk config percentages
            if action.action == "BUY":
                stop_loss_price = actual_entry_price * (1 - stop_loss_pct)
                take_profit_price = actual_entry_price * (1 + take_profit_pct)
                sl_side = "SELL"
                tp_side = "SELL"
            else:  # SELL
                stop_loss_price = actual_entry_price * (1 + stop_loss_pct)
                take_profit_price = actual_entry_price * (1 - take_profit_pct)
                sl_side = "BUY"
                tp_side = "BUY"
            
            logger.info(f"💰 Calculated from Risk Config:")
            logger.info(f"   Entry: ${actual_entry_price:.2f}")
            logger.info(f"   Stop Loss: ${stop_loss_price:.2f} ({stop_loss_pct*100:.1f}%)")
            logger.info(f"   Take Profit: ${take_profit_price:.2f} ({take_profit_pct*100:.1f}%)")
            
            # Cancel all existing STOP/TP orders for this symbol BEFORE placing new ones
            logger.info(f"🧹 Cancelling all existing SL/TP orders for {symbol}...")
            try:
                existing_orders = self.futures_client.get_open_orders(symbol)
                cancelled_count = 0
                for order in existing_orders:
                    order_type = order.get('type', '')
                    if order_type in ['STOP_MARKET', 'TAKE_PROFIT_MARKET', 'STOP', 'TAKE_PROFIT']:
                        order_id = str(order.get('orderId', order.get('order_id', order.get('orderId', ''))))
                        try:
                            self.futures_client.cancel_order(symbol, order_id)
                            cancelled_count += 1
                            logger.info(f"   ✅ Cancelled {order_type} order: {order_id}")
                        except Exception as cancel_err:
                            logger.warning(f"   ⚠️ Failed to cancel order {order_id}: {cancel_err}")
                
                if cancelled_count > 0:
                    logger.info(f"✅ Cancelled {cancelled_count} existing SL/TP orders")
                    # Wait briefly for cancellations to settle
                    import time
                    time.sleep(0.5)
                else:
                    logger.info(f"✅ No existing SL/TP orders to cancel")
            except Exception as cancel_all_err:
                logger.warning(f"⚠️ Failed to check/cancel existing orders: {cancel_all_err}")
            
            # Place managed orders (stop loss + take profit)
            sl_order = None
            tp_orders = None
            try:
                # Get current market price for validation
                current_ticker = self.futures_client.get_ticker(symbol)
                current_market_price = float(current_ticker['price'])
                
                # Validate and adjust prices with minimum distance requirement
                min_distance_pct = 0.005  # 0.5% minimum distance (Bybit requirement)
                adjusted_stop_price = stop_loss_price
                adjusted_tp_price = take_profit_price
                
                if action.action == "BUY":  # Long position
                    # Stop loss should be BELOW market price with minimum distance
                    if stop_loss_price >= current_market_price:
                        adjusted_stop_price = current_market_price * (1 - max(self.stop_loss_pct, min_distance_pct))
                        logger.warning(f"⚠️ SL too high, adjusted: ${stop_loss_price:.2f} → ${adjusted_stop_price:.2f}")
                    elif (current_market_price - stop_loss_price) / current_market_price < min_distance_pct:
                        adjusted_stop_price = current_market_price * (1 - min_distance_pct)
                        logger.warning(f"⚠️ SL too close ({(current_market_price - stop_loss_price) / current_market_price * 100:.2f}%), adjusted: ${stop_loss_price:.2f} → ${adjusted_stop_price:.2f}")
                    
                    # Take profit should be ABOVE market price with minimum distance
                    if take_profit_price <= current_market_price:
                        adjusted_tp_price = current_market_price * (1 + max(self.take_profit_pct, 0.01))
                        logger.warning(f"⚠️ TP too low, adjusted: ${take_profit_price:.2f} → ${adjusted_tp_price:.2f}")
                    elif (take_profit_price - current_market_price) / current_market_price < min_distance_pct:
                        adjusted_tp_price = current_market_price * (1 + max(self.take_profit_pct, min_distance_pct))
                        logger.warning(f"⚠️ TP too close, adjusted: ${take_profit_price:.2f} → ${adjusted_tp_price:.2f}")
                else:  # SELL - Short position
                    # Stop loss should be ABOVE market price with minimum distance
                    if stop_loss_price <= current_market_price:
                        adjusted_stop_price = current_market_price * (1 + max(self.stop_loss_pct, min_distance_pct))
                        logger.warning(f"⚠️ SL too low, adjusted: ${stop_loss_price:.2f} → ${adjusted_stop_price:.2f}")
                    elif (stop_loss_price - current_market_price) / current_market_price < min_distance_pct:
                        adjusted_stop_price = current_market_price * (1 + min_distance_pct)
                        logger.warning(f"⚠️ SL too close ({(stop_loss_price - current_market_price) / current_market_price * 100:.2f}%), adjusted: ${stop_loss_price:.2f} → ${adjusted_stop_price:.2f}")
                    
                    # Take profit should be BELOW market price with minimum distance
                    if take_profit_price >= current_market_price:
                        adjusted_tp_price = current_market_price * (1 - max(self.take_profit_pct, min_distance_pct))
                        logger.warning(f"⚠️ TP too high, adjusted: ${take_profit_price:.2f} → ${adjusted_tp_price:.2f}")
                    elif (current_market_price - take_profit_price) / current_market_price < min_distance_pct:
                        adjusted_tp_price = current_market_price * (1 - max(self.take_profit_pct, min_distance_pct))
                        logger.warning(f"⚠️ TP too close, adjusted: ${take_profit_price:.2f} → ${adjusted_tp_price:.2f}")
                
                # Create managed orders with reduceOnly=True
                # This ensures that if position closes (SL or TP), remaining orders will be REJECTED by exchange
                # preventing unwanted reverse positions
                logger.info(f"🛡️ Creating managed orders with reduceOnly=True (prevents reverse positions)")
                managed_orders = self.futures_client.create_managed_orders(
                    symbol=symbol,
                    side=sl_side,
                    quantity=quantity_str,
                    stop_price=f"{adjusted_stop_price:.2f}",
                    take_profit_price=f"{adjusted_tp_price:.2f}",
                    reduce_only=True  # ✅ Critical: Prevents opening reverse positions when position is already closed
                )
                
                sl_order = managed_orders.get('stop_loss_order')
                tp_orders = managed_orders.get('take_profit_orders', [])
                
                logger.info(f"✅ Managed Orders placed on {self.exchange_name}")
                if sl_order:
                    logger.info(f"🛡️ Stop Loss: ${adjusted_stop_price:.2f}")
                if tp_orders:
                    logger.info(f"🎯 Take Profit: ${adjusted_tp_price:.2f}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to place managed orders on {self.exchange_name}: {e}")
                logger.error(f"   Stop Price: ${adjusted_stop_price:.2f}, TP Price: ${adjusted_tp_price:.2f}")
                logger.error(f"   Side: {sl_side}, Quantity: {quantity_str}, Symbol: {symbol}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                sl_order = None
                tp_orders = None
            
            # Return trade result
            main_order_id = getattr(order, 'order_id', 'N/A')
            
            # Final validation before returning
            if not main_order_id or main_order_id == 'N/A' or main_order_id == '':
                logger.error(f"❌ CRITICAL: About to save transaction WITHOUT valid order_id!")
                logger.error(f"   Order object: {order}")
                logger.error(f"   main_order_id value: '{main_order_id}'")
            else:
                logger.info(f"✅ Transaction will be saved with order_id: {main_order_id}")
            
            result = {
                'status': 'success',
                'action': action.action,
                'exchange': self.exchange_name,
                'symbol': symbol,
                'quantity': quantity_str,
                'entry_price': actual_entry_price,  # Use actual realtime entry price
                'leverage': self.leverage,
                'position_value': position_value,
                'main_order_id': main_order_id,
                'stop_loss': {
                    'price': stop_loss_price,
                    'order_id': sl_order.get('order_id') if sl_order else None,
                    'source': 'risk_config',
                    'percent': stop_loss_pct * 100
                },
                'take_profit': {
                    'price': take_profit_price,
                    'order_ids': [tp.get('order_id') for tp in tp_orders] if tp_orders else [None],
                    'source': 'risk_config',
                    'percent': take_profit_pct * 100
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
            
        except Exception as e:
            logger.error(f"Error setting up position on {self.exchange_name}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'Position setup error: {e}',
                'exchange': self.exchange_name
            }
    
    def save_transaction_to_db(self, trade_result: Dict[str, Any]):
        """
        Save trade transaction to MySQL database with enhanced tracking
        
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
            
            # Determine position side
            action = trade_result.get('action', '').upper()
            position_side = 'LONG' if action == 'BUY' else 'SHORT' if action == 'SELL' else None
            
            # Calculate planned risk-reward ratio
            # Helper function to safely extract float from dict or value
            def safe_float(value, default=0):
                if value is None:
                    return None
                if isinstance(value, dict):
                    # If it's a dict, try to get 'price' or other common keys
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
            
            risk_reward_ratio = None
            if stop_loss and take_profit and entry_price > 0:
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                if risk > 0:
                    risk_reward_ratio = Decimal(str(round(reward / risk, 4)))
            
            # Create transaction record with enhanced fields
            transaction = models.Transaction(
                # Identity & Ownership
                user_id=trade_result.get('user_id'),
                user_principal_id=trade_result.get('user_principal_id'),
                bot_id=trade_result.get('bot_id', self.bot_id),
                subscription_id=trade_result.get('subscription_id', self.subscription_id),
                prompt_id=trade_result.get('prompt_id'),
                
                # Trade Details
                action=action,
                position_side=position_side,
                symbol=trade_result.get('symbol', self.trading_pair),
                quantity=Decimal(str(trade_result.get('quantity', 0))),
                entry_price=Decimal(str(entry_price)),
                entry_time=datetime.now(),
                leverage=int(trade_result.get('leverage', self.leverage)),
                
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
            
            # Extract and save SL/TP order IDs
            sl_order_ids = []
            tp_order_ids = []
            
            # Get SL order ID
            if trade_result.get('stop_loss') and trade_result['stop_loss'].get('order_id'):
                sl_order_id = trade_result['stop_loss']['order_id']
                if sl_order_id and sl_order_id != 'N/A' and sl_order_id != '':
                    sl_order_ids.append(str(sl_order_id))
            
            # Get TP order IDs
            if trade_result.get('take_profit') and trade_result['take_profit'].get('order_ids'):
                tp_ids = trade_result['take_profit']['order_ids']
                if isinstance(tp_ids, list):
                    for tp_id in tp_ids:
                        if tp_id and tp_id != 'N/A' and tp_id != '' and tp_id is not None:
                            tp_order_ids.append(str(tp_id))
                elif tp_ids and tp_ids != 'N/A' and tp_ids != '':
                    tp_order_ids.append(str(tp_ids))
            
            # Save order IDs to transaction
            transaction.sl_order_ids = sl_order_ids if sl_order_ids else None
            transaction.tp_order_ids = tp_order_ids if tp_order_ids else None
            
            # Log what we're about to save
            logger.info(f"💾 Saving transaction to database:")
            logger.info(f"   order_id from trade_result: '{trade_result.get('main_order_id')}'")
            logger.info(f"   order_id in transaction object: '{transaction.order_id}'")
            logger.info(f"   SL order IDs: {sl_order_ids}")
            logger.info(f"   TP order IDs: {tp_order_ids}")
            
            # Add to database
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            
            logger.info(f"✅ Transaction saved to database with ID: {transaction.id} (Status: OPEN)")
            logger.info(f"   Position: {position_side}, Entry: ${entry_price:.2f}, RR: {risk_reward_ratio or 'N/A'}")
            logger.info(f"   Order ID in DB: '{transaction.order_id}'")
            logger.info(f"   SL/TP Orders tracked: {len(sl_order_ids)} SL, {len(tp_order_ids)} TP")
            
        except Exception as e:
            logger.error(f"❌ Failed to save transaction to database: {e}")
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
            subscription_config: Optional config dict containing:
                - trading_pair: Trading pair to crawl (e.g., 'ETH/USDT' or 'ETHUSDT')
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
            "30m": 200, "1h": 250, "4h": 120,
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
        
        # Use mainnet for data, fallback to testnet
        CLIENT = self.futures_client_mainnet if self.futures_client_mainnet else self.futures_client
        if not CLIENT:
            logger.error("❌ No futures client available")
            return {'timeframes': {}, 'error': 'No futures client initialized'}
        
        client_type = "MAINNET" if self.futures_client_mainnet else "TESTNET (fallback)"
        logger.info(f"📊 Data crawling using {client_type} client on {self.exchange_name}")
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
                    
                    df = CLIENT.get_klines(
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
                        df_more = CLIENT.get_klines(
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
    # Note: Main setup_position method is defined earlier (line ~401) with subscription parameter
    
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


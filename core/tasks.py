import logging
import traceback
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import importlib.util
import logging
import traceback
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import importlib.util
import inspect
import os
import tempfile
import sys
import redis
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.celery_app import app
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_notification_message(
    bot_name,
    balance_info=None,
    action=None,
    reason=None,
    current_price=None,
    available=None,
    total_wallet=None,
    entry_price=None,
    quantity=None,
    stop_loss=None,
    take_profit=None,
):
    """
    Format notification message for all channels (Telegram, Discord, Email)
    """

    available_str = available if available is not None else "N/A"
    total_wallet_str = total_wallet if total_wallet is not None else "N/A"
    msg = (
        f"{bot_name}\n"
        f"TESTNET Account Balance:\n"
        f" 💰 Available: ${available_str:,.2f} USDT\n"
        f" 💎 Total Wallet: ${total_wallet_str:,.2f} USDT\n"
        f"Action: {action}"
    )

    if action and action.upper() != "HOLD":
        if entry_price is not None:
            msg += f"\nEntry Price: ${entry_price:,.2f}"
        if quantity is not None:
            msg += f"\nQuantity: {quantity}"
        if stop_loss is not None:
            msg += f"\nStop Loss: ${stop_loss:,.2f}"
        if take_profit is not None:
            msg += f"\nTake Profit: ${take_profit:,.2f}"
    msg += f"\nReason: {reason}"
    return msg

def format_trade_log_details(trade_result, signal, trading_pair):
    """
    Format comprehensive trade execution log details for UI display
    Returns formatted string with all trade information
    """
    try:
        # Extract trade details
        quantity = trade_result.get('quantity', 0)
        entry_price = trade_result.get('entry_price', 0)
        leverage = trade_result.get('leverage', 1)
        stop_loss_data = trade_result.get('stop_loss', {})
        take_profit_data = trade_result.get('take_profit', {})
        confidence = signal.value * 100 if hasattr(signal, 'value') else 0
        action = signal.action if hasattr(signal, 'action') else trade_result.get('action', 'UNKNOWN')
        
        # Extract SL/TP prices
        if isinstance(stop_loss_data, dict):
            stop_loss_price = stop_loss_data.get('price', 0)
        else:
            stop_loss_price = stop_loss_data if stop_loss_data else 0
            
        if isinstance(take_profit_data, dict):
            take_profit_price = take_profit_data.get('price', 0)
        else:
            take_profit_price = take_profit_data if take_profit_data else 0
        
        # Format message with emoji
        action_emoji = "💰" if action == "BUY" else "🔴" if action == "SELL" else "⏸️"
        
        # Build comprehensive message
        details = (
            f"{action_emoji} {action} {quantity} {trading_pair} at ${entry_price:,.2f} ({leverage}x) "
            f"(Confidence: {confidence:.1f}%)"
        )
        
        # Add SL/TP to signal_data for display
        if stop_loss_price > 0 or take_profit_price > 0:
            sl_tp_info = []
            if stop_loss_price > 0:
                sl_tp_info.append(f"SL: ${stop_loss_price:,.2f}")
            if take_profit_price > 0:
                sl_tp_info.append(f"TP: ${take_profit_price:,.2f}")
            if sl_tp_info:
                details += f" | {' | '.join(sl_tp_info)}"
        
        return details
        
    except Exception as e:
        logger.error(f"Error formatting trade log details: {e}")
        return f"{trade_result.get('action', 'TRADE')} executed"

# Helper to push DM to Redis queue
def queue_discord_dm(user_id, message):
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis_db'), port=int(os.getenv('REDIS_PORT', 6379)), db=0)
    payload = {'user_id': user_id, 'message': message}
    r.rpush('discord_dm_queue', json.dumps(payload))

def initialize_bot_from_local_file(subscription, local_file_path, db):
    """📂 Load bot from local file system (for template bots)"""
    try:
        import importlib.util
        
        bot_id = subscription.bot.id
        
        # Handle bot_type - can be enum or string
        bot_type = subscription.bot.bot_type
        if hasattr(bot_type, 'value'):
            bot_type = bot_type.value
        
        # Handle exchange_type - can be enum or string
        exchange_type = subscription.bot.exchange_type
        if hasattr(exchange_type, 'value'):
            exchange_type = exchange_type.value
        elif not exchange_type:
            exchange_type = 'BINANCE'
        
        logger.info(f"📂 Loading bot from local file: {local_file_path}")
        
        # Load module from file
        module_name = f"bot_module_{bot_id}_{int(time.time())}"  # Unique name to avoid cache
        spec = importlib.util.spec_from_file_location(module_name, local_file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find bot class by looking for classes with execute_algorithm method
        bot_class = None
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Look for custom bot class (has execute_algorithm and not a base class)
            if (hasattr(obj, 'execute_algorithm') and 
                name not in ['CustomBot', 'Action', 'BaseBot'] and
                not name.startswith('_')):
                bot_class = obj
                logger.info(f"🔧 [DEV MODE] Found bot class: {name}")
                break
        
        if not bot_class:
            raise Exception(f"No bot class found in local file: {local_path}")
        
        # Prepare config
        execution_config = subscription.execution_config or {}
        
        bot_config = {
            'bot_id': bot_id,
            'subscription_id': subscription.id,
            'trading_pair': subscription.trading_pair or execution_config.get('trading_pair', 'BTC/USDT'),
            'leverage': execution_config.get('leverage', 5),
            'testnet': subscription.is_testnet if subscription.is_testnet is not None else False,
            'exchange_type': exchange_type,
            'timeframes': execution_config.get('timeframes', ['1h']),
            'bot_type': bot_type,
            'developer_id': subscription.bot.developer_id if subscription.bot else None,  # For LLM provider selection
            'db': db  # For LLM provider selection
        }
        
        # Merge bot's strategy_config (includes llm_provider preference)
        if subscription.bot and subscription.bot.strategy_config:
            logger.info(f"🎯 [LOCAL] Merging bot's strategy config: {subscription.bot.strategy_config}")
            bot_config.update(subscription.bot.strategy_config)
            if bot_config.get('llm_provider'):
                logger.info(f"🤖 [LOCAL] Bot LLM Provider: {bot_config['llm_provider']}")
        
        # Get API keys
        from core.api_key_manager import get_bot_api_keys
        api_keys = get_bot_api_keys(subscription.user_principal_id, exchange_type)
        
        # Initialize bot (try 4-arg constructor first)
        try:
            bot_instance = bot_class(bot_config, api_keys, subscription.user_principal_id, subscription.id)
            logger.info(f"🔧 [LOCAL] Bot initialized with 4 args (developer_id={bot_config.get('developer_id')})")
        except TypeError as e:
            try:
                bot_instance = bot_class(bot_config, api_keys)
                logger.info(f"🔧 [LOCAL] Bot initialized with 2 args")
            except Exception as e2:
                raise Exception(f"Failed to initialize bot: {e}, {e2}")
        
        return bot_instance
        
    except Exception as e:
        logger.error(f"📂 Failed to load bot from local file: {e}")
        import traceback
        traceback.print_exc()
        raise

def initialize_bot(subscription):
    """Initialize bot from subscription - Load from local file if exists, else S3"""
    try:
        # Import here to avoid circular imports
        from core import models
        from core import schemas
        from core.database import SessionLocal
        from services.s3_manager import S3Manager
        from core.bot_base_classes import get_base_classes
        
        # Get bot information
        bot_id = subscription.bot.id
        code_path = subscription.bot.code_path
        
        # Create database session for LLM provider loading
        db = SessionLocal()
        
        # 🎯 STRATEGY: Try local file first (for templates), fallback to S3 (for uploaded bots)
        
        # Check if code_path points to a local file
        if code_path and not code_path.startswith('bots/'):
            # This is a template bot (e.g., "bot_files/universal_futures_bot.py")
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_file_path = os.path.join(project_root, code_path)
            
            if os.path.exists(local_file_path):
                logger.info(f"📂 [LOCAL FILE] Loading bot {bot_id} from: {code_path}")
                return initialize_bot_from_local_file(subscription, local_file_path, db)
            else:
                logger.warning(f"⚠️ Local file not found: {local_file_path}, falling back to S3")
        
        # Fallback to S3 for marketplace/uploaded bots
        # Initialize S3 manager
        s3_manager = S3Manager()
        logger.info(f"☁️ [S3] Loading bot {bot_id} from S3...")
        
        # Get latest version from S3
        try:
            latest_version = s3_manager.get_latest_version(bot_id, "code")
            logger.info(f"Using latest version: {latest_version}")
        except Exception as e:
            logger.error(f"Could not get latest version for bot {bot_id}: {e}")
            return None
        
        # Download bot code from S3
        try:
            code_content = s3_manager.download_bot_code(bot_id, latest_version)
            logger.info(f"Downloaded bot code from S3: {len(code_content)} characters")
        except Exception as e:
            logger.error(f"Failed to download bot code from S3: {e}")
            return None
        
        # Create temporary file to execute the code
        # (tempfile and os already imported globally)
        
        # Load base classes from bot_sdk folder
        base_classes = get_base_classes()
        
        # Combine base classes with downloaded bot code
        full_code = base_classes + "\n" + code_content
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file_path = f.name
        
        try:
            # Load bot module from temporary file
            spec = importlib.util.spec_from_file_location("bot_module", temp_file_path)
            if not spec or not spec.loader:
                logger.error("Could not create module spec")
                return None
            
            bot_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bot_module)
            
            # Find bot class in the module
            bot_class = None
            for attr_name in dir(bot_module):
                attr = getattr(bot_module, attr_name)
                if (inspect.isclass(attr) and 
                    hasattr(attr, 'execute_algorithm') and 
                    attr_name != 'CustomBot'):
                    bot_class = attr
                    break
            
            if not bot_class:
                logger.error("No valid bot class found in module")
                return None
            
            # Prepare bot configuration - Rich config for Futures bots
            if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type and subscription.bot.bot_type.upper() == 'FUTURES':
                # Rich configuration for Futures bots (like main_execution)
                if subscription.trading_pair:
                    trading_pair = subscription.trading_pair
                else:
                    trading_pair = subscription.bot.trading_pair.replace("/", "")
                
                # Get exchange type from bot
                exchange_type = subscription.bot.exchange_type.value if subscription.bot.exchange_type else 'BINANCE'
                
                bot_config = {
                    'bot_id': subscription.bot.id,  # ✅ CRITICAL: Pass bot_id for custom prompt loading
                    'subscription_id': subscription.id,  # ✅ Pass subscription_id for tracking
                    'trading_pair': trading_pair,
                    'exchange_type': exchange_type,  # ✅ CRITICAL: Pass exchange type for multi-exchange support
                    'testnet': subscription.is_testnet if subscription.is_testnet else True,
                    'leverage': 5,
                    'stop_loss_pct': 0.02,  # 2%
                    'take_profit_pct': 0.04,  # 4%
                    'position_size_pct': 0.1,  # 10% of balance
                    
                    # 🎯 Optimized 3 timeframes for better performance
                    'timeframes': subscription.bot.timeframes,
                    'primary_timeframe': subscription.bot.timeframe,  # Primary timeframe for final decision
                    
                    'use_llm_analysis': True,  # Enable LLM analysis with full system
                    'llm_model': 'openai',  # Primary LLM model to use
                    
                    # Technical indicators (fallback when LLM fails)
                    'rsi_period': 14,
                    'rsi_oversold': 30,     # Buy signal threshold
                    'rsi_overbought': 70,   # Sell signal threshold
                    
                    # Capital management (CRITICAL for risk control)
                    'base_position_size_pct': 0.02,    # 2% minimum position
                    'max_position_size_pct': 0.10,     # 10% maximum position  
                    'max_portfolio_exposure': 0.30,    # 30% total exposure limit
                    'max_drawdown_threshold': 0.15,    # 15% stop-loss threshold
                    
                    # LLM Provider Selection (BYOK)
                    'developer_id': subscription.bot.developer_id if subscription.bot else None,  # For LLM provider selection
                    'db': db,  # For LLM provider selection
                    
                    # Celery execution
                    'require_confirmation': False,  # No confirmation for Celery
                    'auto_confirm': True  # Auto-confirm trades (for Celery/automated execution)
                }
                # Merge bot's strategy_config (includes llm_provider preference)
                if subscription.bot.strategy_config:
                    logger.info(f"🎯 Merging bot's strategy config: {subscription.bot.strategy_config}")
                    bot_config.update(subscription.bot.strategy_config)
                
                logger.info(f"🎯 Config with bot_id={subscription.bot.id}, subscription_id={subscription.id}, exchange={exchange_type}")
                logger.info(f"🚀 Applied RICH FUTURES CONFIG: {len(bot_config['timeframes'])} timeframes, {bot_config['leverage']}x leverage, exchange={exchange_type}")
                if bot_config.get('llm_provider'):
                    logger.info(f"🤖 Bot LLM Provider: {bot_config['llm_provider']}")
            else:
                # Standard configuration for other bots
                bot_config = {
                    'short_window': 50,
                    'long_window': 200,
                    'position_size': 0.3,
                    'min_volume_threshold': 1000000,
                    'volatility_threshold': 0.05,
                    # LLM Provider Selection (BYOK)
                    'developer_id': subscription.bot.developer_id if subscription.bot else None,
                    'db': db
                }
                logger.info("📊 Applied STANDARD CONFIG for non-futures bot")
            
            # Override with subscription strategy_config if available (from database)
            if subscription.bot.strategy_config:
                logger.info(f"🎯 Merging DATABASE STRATEGY CONFIG: {subscription.bot.strategy_config}")
                bot_config.update(subscription.bot.strategy_config)
            
            # Set trading pair in bot config
            if subscription.trading_pair:
                trading_pair = subscription.trading_pair
            else:
                trading_pair = subscription.bot.trading_pair.replace("/", "")
            
            # Add trading pair to bot config (without slash for Binance API)
            bot_config['trading_pair'] = trading_pair
            # Prepare subscription context for bot (includes principal ID)
            subscription_context = {
                'subscription_id': subscription.id,
                'user_principal_id': subscription.user_principal_id,
                'exchange': subscription.bot.exchange_type.value if subscription.bot.exchange_type else 'binance',
                'trading_pair': trading_pair,
                'timeframe': subscription.bot.timeframe,
                'is_testnet': subscription.is_testnet if subscription.is_testnet else True,
                'is_marketplace_subscription': getattr(subscription, 'is_marketplace_subscription', False)
            }
            
            # Try multiple initialization approaches for compatibility
            bot_instance = None
            init_success = False
            
            # Create api_keys dict for backward compatibility
            api_keys = {
                'exchange': subscription_context['exchange'],
                'testnet': subscription_context['is_testnet']
            }
            
            # ✅ ALWAYS use bot code downloaded from S3 (supports multi-exchange)
            # Try different initialization signatures for compatibility
            logger.info(f"Initializing bot from S3 code: {bot_class.__name__}")
            
            # Method 1: Try with 4 arguments (config, api_keys, user_principal_id, subscription_id) - for Universal Bot
            if not init_success:
                try:
                    bot_instance = bot_class(bot_config, api_keys, subscription.user_principal_id, subscription.id)
                    init_success = True
                    logger.info(f"✅ Downloaded bot initialized with 4 args (Universal Futures Bot): {bot_class.__name__}")
                except TypeError as e:
                    logger.warning(f"4-arg constructor failed: {e}")
            
            # Method 2: Try with 3 arguments (config, api_keys, user_principal_id)
            if not init_success:
                try:
                    bot_instance = bot_class(bot_config, api_keys, subscription.user_principal_id)
                    init_success = True
                    logger.info(f"✅ Downloaded bot initialized with 3 args: {bot_class.__name__}")
                except TypeError as e:
                    logger.warning(f"3-arg constructor failed: {e}")
            
            # Method 3: Try downloaded bot with 2 arguments (config, api_keys)
            if not init_success:
                try:
                    bot_instance = bot_class(bot_config, api_keys)
                    init_success = True
                    logger.info(f"✅ Downloaded bot initialized with 2 args: {bot_class.__name__}")
                except TypeError as e:
                    logger.warning(f"2-arg constructor failed: {e}")
            
            # Method 4: Try downloaded bot with 1 argument (config)
            if not init_success:
                try:
                    bot_instance = bot_class(bot_config)
                    init_success = True
                    logger.info(f"✅ Downloaded bot initialized with 1 arg: {bot_class.__name__}")
                except TypeError as e:
                    logger.warning(f"1-arg constructor failed: {e}")
            
            # Method 5: Try downloaded bot with no arguments
            if not init_success:
                try:
                    bot_instance = bot_class()
                    init_success = True
                    logger.info(f"✅ Downloaded bot initialized with no args: {bot_class.__name__}")
                except Exception as e:
                    logger.error(f"No-arg constructor failed: {e}")
            
            # If initialization succeeded, manually inject context for non-futures bots
            if init_success and bot_instance:
                # Manually inject subscription context for downloaded bots
                if hasattr(bot_instance, 'user_principal_id'):
                    bot_instance.user_principal_id = subscription_context['user_principal_id']
                if hasattr(bot_instance, 'subscription_id'):
                    bot_instance.subscription_id = subscription_context['subscription_id']
                if hasattr(bot_instance, 'trading_pair'):
                    bot_instance.trading_pair = subscription_context['trading_pair']
                if hasattr(bot_instance, 'timeframe'):
                    bot_instance.timeframe = subscription_context['timeframe']
                if hasattr(bot_instance, 'is_testnet'):
                    bot_instance.is_testnet = subscription_context['is_testnet']
                
                # Set config manually if the bot has attributes for it
                if hasattr(bot_instance, 'short_window'):
                    bot_instance.short_window = bot_config.get('short_window', 50)
                if hasattr(bot_instance, 'long_window'):
                    bot_instance.long_window = bot_config.get('long_window', 200)
                if hasattr(bot_instance, 'position_size'):
                    bot_instance.position_size = bot_config.get('position_size', 0.3)
                
                logger.info(f"Context injected - Principal ID: {subscription_context['user_principal_id']}")
            else:
                logger.error(f"All bot initialization methods failed")
                return None
            
            return bot_instance
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        logger.error(traceback.format_exc())
        return None
    
def initialize_bot_rpa_v1(subscription):
    """Initialize bot from subscription - Load from S3"""
    try:
        # Import here to avoid circular imports
        from core import models
        from core import schemas
        from core.database import SessionLocal
        from services.s3_manager import S3Manager
        from core.bot_base_classes import get_base_classes
        from core.consts.index import MAIN_INDICATORS, SUB_INDICATORS, TIMEFRAME_ROBOT_MAP
        # Initialize S3 manager
        s3_manager = S3Manager()
        
        # Get bot information
        bot_id = subscription.bot.id
        logger.info(f"Initializing bot {bot_id} from S3...")
        
        # Get latest version from S3
        try:
            latest_version = s3_manager.get_latest_version(bot_id, "code")
            latest_version_rpa = s3_manager.get_latest_version(bot_id, "rpa")
            logger.info(f"Using latest version: {latest_version}, RPA version: {latest_version_rpa}")
        except Exception as e:
            logger.error(f"Could not get latest version for bot {bot_id}: {e}")
            return None
        
        # Download bot code from S3
        try:
            code_content = s3_manager.download_bot_code(bot_id, latest_version, file_type="code")
            rpa_code_content = s3_manager.download_bot_code(bot_id, latest_version_rpa, file_type="rpa")
            logger.info(f"Downloaded bot code from S3: {len(code_content)} characters")
        except Exception as e:
            logger.error(f"Failed to download bot code from S3: {e}")
            return None
        
        # Create temporary file to execute the code
        # (tempfile and os already imported globally)
        
        # Load base classes from bot_sdk folder
        base_classes = get_base_classes()
        
        # Combine base classes with downloaded bot code
        full_code = base_classes + "\n" + code_content
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.robot', delete=False) as rf:
            rf.write(rpa_code_content)
            robot_file_path = rf.name
        
        try:
            # Load bot module from temporary file
            spec = importlib.util.spec_from_file_location("bot_module", temp_file_path)
            if not spec or not spec.loader:
                logger.error("Could not create module spec")
                return None
            
            bot_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bot_module)
            
            # Find bot class in the module
            bot_class = None
            for attr_name in dir(bot_module):
                attr = getattr(bot_module, attr_name)
                if (inspect.isclass(attr) and 
                    hasattr(attr, 'execute_algorithm') and 
                    attr_name != 'CustomBot'):
                    bot_class = attr
                    break
            
            if not bot_class:
                logger.error("No valid bot class found in module")
                return None
            
            # Prepare bot configuration - Rich config for Futures bots
            if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type and subscription.bot.bot_type.upper() == 'FUTURES_RPA':
                # Rich configuration for Futures bots (like main_execution)
                all_strategies = subscription.bot.strategy_config
                main_selected = [s for s in all_strategies if s in MAIN_INDICATORS]
                sub_selected = [s for s in all_strategies if s in SUB_INDICATORS]

                trading_pair = subscription.bot.trading_pair.replace('/', '_') or 'BTC_USDT'

                timeframes_binance = [
                    TIMEFRAME_ROBOT_MAP.get(tf.lower(), tf)
                    for tf in subscription.bot.timeframes
                ]

                primary_timeframe = subscription.bot.timeframe
                primary_tf_mapped = TIMEFRAME_ROBOT_MAP.get(primary_timeframe.lower(), primary_timeframe)
                if primary_tf_mapped not in timeframes_binance:
                    timeframes_binance.append(primary_tf_mapped)
                logger.info(f"🔍 DEBUG: timeframes for robot: {timeframes_binance} and primary: {primary_tf_mapped}")

                logger.info(f"RPA Bot Config - Trading Pair: {trading_pair}, Timeframes: {timeframes_binance} (Primary: {primary_tf_mapped}), Main Indicators: {main_selected}, Sub Indicators: {sub_selected}")
                bot_config = {
                    'trading_pair': trading_pair,
                    'testnet': subscription.is_testnet if subscription.is_testnet else True,
                    'leverage': 5,
                    'stop_loss_pct': 0.02,  # 2%
                    'take_profit_pct': 0.04,  # 4%
                    'position_size_pct': 0.1,  # 10% of balance
                    
                    # 🎯 Optimized 3 timeframes for better performance
                    'timeframes': timeframes_binance,
                    'primary_timeframe': primary_tf_mapped,  # Primary timeframe for final decision
                    'main_indicators': main_selected,
                    'sub_indicators': sub_selected,
                    'use_llm_analysis': True,  # Enable LLM analysis with full system
                    'llm_model': 'openai',  # Primary LLM model to use
                    
                    # Technical indicators (fallback when LLM fails)
                    'rsi_period': 14,
                    'rsi_oversold': 30,     # Buy signal threshold
                    'rsi_overbought': 70,   # Sell signal threshold
                    
                    # Capital management (CRITICAL for risk control)
                    'base_position_size_pct': 0.02,    # 2% minimum position
                    'max_position_size_pct': 0.10,     # 10% maximum position  
                    'max_portfolio_exposure': 0.30,    # 30% total exposure limit
                    'max_drawdown_threshold': 0.15,    # 15% stop-loss threshold
                    
                    # Celery execution
                    'require_confirmation': False,  # No confirmation for Celery
                    'auto_confirm': True,  # Auto-confirm trades (for Celery/automated execution)

                    # robot file
                    'robot_file': robot_file_path or 'binance.robot'
                }
                logger.info(f"🚀 Applied RICH FUTURES CONFIG: {len(bot_config['timeframes'])} timeframes, {bot_config['leverage']}x leverage")
            else:
                # Standard configuration for other bots
                bot_config = {
                    'short_window': 50,
                    'long_window': 200,
                    'position_size': 0.3,
                    'min_volume_threshold': 1000000,
                    'volatility_threshold': 0.05
                }
                logger.info("📊 Applied STANDARD CONFIG for non-futures bot")
            
            # Override with subscription strategy_config if available (from database)
            # Prepare subscription context for bot (includes principal ID)
            subscription_context = {
                'subscription_id': subscription.id,
                'user_principal_id': subscription.user_principal_id,
                'exchange': subscription.bot.exchange_type.value if subscription.bot.exchange_type else 'binance',
                'trading_pair': trading_pair,
                'timeframe': subscription.bot.timeframe,
                'is_testnet': subscription.is_testnet if subscription.is_testnet else True,
                'is_marketplace_subscription': getattr(subscription, 'is_marketplace_subscription', False)
            }
            
            # Try multiple initialization approaches for compatibility
            bot_instance = None
            init_success = False
            
            # Create api_keys dict for backward compatibility
            api_keys = {
                'exchange': subscription_context['exchange'],
                'testnet': subscription_context['is_testnet']
            }
            
            # Method 1: Try BinanceFuturesBot direct initialization (for Futures bots)
            if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type and subscription.bot.bot_type.upper() == 'FUTURES_RPA':
                try:
                    logger.info(f"Attempting FUTURES_RPA BOT direct initialization...")
                    # Import FuturesRPABot directly for futures RPA bots
                    import sys
                    import os
                    bot_files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_files')
                    if bot_files_path not in sys.path:
                        sys.path.insert(0, bot_files_path)
                    
                    from binance_futures_rpa_bot import BinanceFuturesRPABot
                    bot_instance = BinanceFuturesRPABot(bot_config, api_keys, subscription.user_principal_id, subscription.id)
                    init_success = True
                    logger.info(f"✅ FUTURES_RPA BOT initialized successfully with principal ID")
                except Exception as e:
                    logger.warning(f"FUTURES_RPA BOT direct init failed: {e}")
            # Method 2: Try downloaded bot with 4 arguments (config, api_keys, principal_id, subscription_id)
            if not init_success:
                try:
                    bot_instance = bot_class(bot_config, api_keys, subscription.user_principal_id, subscription.id)
                    init_success = True
                    logger.info(f"✅ Downloaded bot initialized with 4 args: {bot_class.__name__}")
                except TypeError as e:
                    logger.warning(f"4-arg constructor failed: {e}")
            
            # Method 3: Try downloaded bot with 3 arguments (config, api_keys, principal_id) - fallback
            if not init_success:
                try:
                    bot_instance = bot_class(bot_config, api_keys, subscription.user_principal_id)
                    init_success = True
                    logger.info(f"✅ Downloaded bot initialized with 3 args: {bot_class.__name__}")
                except TypeError as e:
                    logger.warning(f"3-arg constructor failed: {e}")
            
            # Method 3: Try downloaded bot with 2 arguments (config, api_keys)
            if not init_success:
                try:
                    bot_instance = bot_class(bot_config, api_keys)
                    init_success = True
                    logger.info(f"✅ Downloaded bot initialized with 2 args: {bot_class.__name__}")
                except TypeError as e:
                    logger.warning(f"2-arg constructor failed: {e}")
            
            # Method 4: Try downloaded bot with 1 argument (config)
            if not init_success:
                try:
                    bot_instance = bot_class(bot_config)
                    init_success = True
                    logger.info(f"✅ Downloaded bot initialized with 1 arg: {bot_class.__name__}")
                except TypeError as e:
                    logger.warning(f"1-arg constructor failed: {e}")
            
            # Method 5: Try downloaded bot with no arguments
            if not init_success:
                try:
                    bot_instance = bot_class()
                    init_success = True
                    logger.info(f"✅ Downloaded bot initialized with no args: {bot_class.__name__}")
                except Exception as e:
                    logger.error(f"No-arg constructor failed: {e}")
            
            # If initialization succeeded, manually inject context for non-futures bots
            if init_success and bot_instance:
                # Manually inject subscription context for downloaded bots
                if hasattr(bot_instance, 'user_principal_id'):
                    bot_instance.user_principal_id = subscription_context['user_principal_id']
                if hasattr(bot_instance, 'subscription_id'):
                    bot_instance.subscription_id = subscription_context['subscription_id']
                if hasattr(bot_instance, 'trading_pair'):
                    bot_instance.trading_pair = subscription_context['trading_pair']
                if hasattr(bot_instance, 'is_testnet'):
                    bot_instance.is_testnet = subscription_context['is_testnet']
                
                # Set config manually if the bot has attributes for it
                if hasattr(bot_instance, 'short_window'):
                    bot_instance.short_window = bot_config.get('short_window', 50)
                if hasattr(bot_instance, 'long_window'):
                    bot_instance.long_window = bot_config.get('long_window', 200)
                if hasattr(bot_instance, 'position_size'):
                    bot_instance.position_size = bot_config.get('position_size', 0.3)
                
                logger.info(f"Context injected - Principal ID: {subscription_context['user_principal_id']}")
            else:
                logger.error(f"All bot initialization methods failed")
                return None
            
            return bot_instance
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error initializing bot: {e}")
        logger.error(traceback.format_exc())
        return None

def execute_trade_action(db, subscription, exchange, action, current_price):
    """Execute trade action"""
    try:
        from core import crud
        
        # Get trading pair
        trading_pair = subscription.bot.trading_pair or 'BTC/USDT'
        exchange_symbol = trading_pair.replace('/', '')
        
        # Get balance info
        try:
            base_asset = trading_pair.split('/')[0]  # BTC from BTC/USDT
            quote_asset = trading_pair.split('/')[1]  # USDT from BTC/USDT
        
            base_balance = exchange.get_balance(base_asset)
            quote_balance = exchange.get_balance(quote_asset)
        
            base_total = float(base_balance.free) + float(base_balance.locked)
            quote_total = float(quote_balance.free) + float(quote_balance.locked)
            
            # Calculate portfolio value in USDT
            portfolio_value = quote_total + (base_total * current_price)
            
            logger.info(f"Balance - {base_asset}: {base_total}, {quote_asset}: {quote_total}, Portfolio: ${portfolio_value:.2f}")
            
        except Exception as e:
            logger.warning(f"Could not get balance info: {e}")
            base_asset = trading_pair.split('/')[0] if '/' in trading_pair else 'BTC'
            quote_asset = trading_pair.split('/')[1] if '/' in trading_pair else 'USDT'
            base_total = 0
            quote_total = 0
            portfolio_value = 0
        
        # Execute trade based on action
        if action.action == "BUY":
            # Calculate buy amount
            if action.type == "PERCENTAGE":
                # Use percentage of quote balance
                buy_amount_usdt = quote_total * (action.value / 100)
                # Use exchange's calculate_quantity method for proper precision
                quantity_str, quantity_info = exchange.calculate_quantity(
                    symbol=exchange_symbol,
                    side="BUY",
                    amount=buy_amount_usdt,
                    price=current_price
                )
                buy_quantity = float(quantity_str)
            else:
                # Fixed amount in base currency
                quantity_str, quantity_info = exchange.calculate_quantity(
                    symbol=exchange_symbol,
                    side="BUY",
                    amount=action.value,
                    price=current_price
                )
                buy_quantity = float(quantity_str)
            
            # Check if we have enough quote currency
            if buy_quantity * current_price > quote_total:
                logger.warning(f"Insufficient {quote_asset} balance for buy order")
                return {
                    'success': False,
                    'error': f"Insufficient {quote_asset} balance"
                }
            
            # Place buy order
            try:
                order = exchange.create_market_order(
                    symbol=exchange_symbol,
                    side="BUY",
                    quantity=quantity_str
                )
                logger.info(f"Buy order executed: {order}")
                
                # Log trade to database
                crud.log_bot_action(
                    db, subscription.id, "BUY_EXECUTED",
                    f"Bought {buy_quantity} {base_asset} at ${current_price:.2f}. Order: {order.order_id}"
                )
                
                return {
                    'success': True,
                    'order_id': order.order_id,
                    'quantity': quantity_str,
                    'current_price': current_price,
                    'usdt_value': buy_quantity * current_price,
                    'percentage_used': action.value,
                    'base_asset': base_asset
                }
                
            except Exception as e:
                logger.error(f"Buy order failed: {e}")
                crud.log_bot_action(
                    db, subscription.id, "BUY_FAILED",
                    f"Failed to buy {buy_quantity} {base_asset}: {str(e)}"
                )
                return {
                    'success': False,
                    'error': str(e)
                }
                
        elif action.action == "SELL":
            # Calculate sell amount
            if action.type == "PERCENTAGE":
                # Use percentage of base balance
                sell_amount = base_total * (action.value / 100)
                # Use exchange's calculate_quantity method for proper precision
                quantity_str, quantity_info = exchange.calculate_quantity(
                    symbol=exchange_symbol,
                    side="SELL",
                    amount=sell_amount,
                    price=current_price
                )
                sell_quantity = float(quantity_str)
            else:
                # Fixed amount in base currency
                quantity_str, quantity_info = exchange.calculate_quantity(
                    symbol=exchange_symbol,
                    side="SELL",
                    amount=action.value,
                    price=current_price
                )
                sell_quantity = float(quantity_str)
            
            # 🎯 FUTURES vs SPOT: Different balance requirements
            is_futures = hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type and subscription.bot.bot_type.upper() == 'FUTURES'
            
            if is_futures:
                # FUTURES: For SELL (SHORT), only need USDT margin, not base currency
                required_margin = sell_quantity * current_price * 0.1  # Assume 10x leverage
                if required_margin > quote_total:
                    logger.warning(f"Insufficient {quote_asset} margin for futures SELL order (need ${required_margin:.2f}, have ${quote_total:.2f})")
                    return {
                        'success': False,
                        'error': f"Insufficient {quote_asset} margin for futures SELL"
                    }
                logger.info(f"✅ Futures SELL: Using ${required_margin:.2f} USDT margin to SHORT {sell_quantity} {base_asset}")
            else:
                # SPOT: Need actual base currency to sell
                if sell_quantity > base_total:
                    logger.warning(f"Insufficient {base_asset} balance for spot sell order")
                    return {
                        'success': False,
                        'error': f"Insufficient {base_asset} balance"
                    }
            
            # Place sell order
            try:
                order = exchange.create_market_order(
                    symbol=exchange_symbol,
                    side="SELL",
                    quantity=quantity_str
                )
                logger.info(f"Sell order executed: {order}")
                
                # Log trade to database
                crud.log_bot_action(
                    db, subscription.id, "SELL_EXECUTED",
                    f"Sold {sell_quantity} {base_asset} at ${current_price:.2f}. Order: {order.order_id}"
                )
                
                return {
                    'success': True,
                    'order_id': order.order_id,
                    'quantity': quantity_str,
                    'current_price': current_price,
                    'usdt_value': sell_quantity * current_price,
                    'percentage_used': action.value,
                    'base_asset': base_asset
                }
                
            except Exception as e:
                logger.error(f"Sell order failed: {e}")
                crud.log_bot_action(
                    db, subscription.id, "SELL_FAILED",
                    f"Failed to sell {sell_quantity} {base_asset}: {str(e)}"
                )
                return {
                    'success': False,
                    'error': str(e)
                }
        
        return {
            'success': False,
            'error': 'Invalid action type'
        }
        
    except Exception as e:
        logger.error(f"Error executing trade action: {e}")
        logger.error(traceback.format_exc())
        return False

def _calculate_next_run(timeframe: str) -> 'datetime':
    """Helper function to calculate next run time based on timeframe"""
    from datetime import datetime, timedelta
    
    if timeframe == "1m":
        return datetime.utcnow() + timedelta(minutes=1)
    elif timeframe == "5m":
        return datetime.utcnow() + timedelta(minutes=5)
    elif timeframe == "15m":
        return datetime.utcnow() + timedelta(minutes=15)
    elif timeframe == "1h":
        return datetime.utcnow() + timedelta(hours=1)
    elif timeframe == "4h":
        return datetime.utcnow() + timedelta(hours=4)
    elif timeframe == "1d":
        return datetime.utcnow() + timedelta(days=1)
    else:
        return datetime.utcnow() + timedelta(hours=1)  # Default to 1 hour


@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def run_bot_logic(self, subscription_id: int):
    """
    Main task to run bot logic with duplicate execution prevention
    """
    # 🔒 LOCK: Prevent duplicate execution by multiple workers
    lock_key = f"bot_execution_lock_{subscription_id}"
    redis_client = None
    
    try:
        # Try to acquire Redis lock
        from redis import Redis
        redis_client = Redis(host='redis', port=6379, db=0, decode_responses=True)
        
        # Set lock with 5-minute expiration (longer than typical bot execution)
        lock_acquired = redis_client.set(lock_key, "locked", nx=True, ex=300)
        
        if not lock_acquired:
            logger.info(f"🔒 Bot execution for subscription {subscription_id} already in progress by another worker, skipping")
            return {"status": "skipped", "reason": "duplicate_execution_prevented"}
            
        logger.info(f"🔓 Acquired execution lock for subscription {subscription_id}")
        
    except Exception as e:
        logger.warning(f"Failed to acquire Redis lock, proceeding without lock: {e}")
        redis_client = None  # Disable lock cleanup if Redis unavailable
    
    try:
        # Import here to avoid circular imports
        from core import models
        from core import schemas
        from core import crud
        from core.database import SessionLocal
        from services.exchange_factory import ExchangeFactory
        
        db = SessionLocal()
        
        try:
            logger.info(f"Running bot logic for subscription {subscription_id}")
            # Get subscription
            subscription = crud.get_subscription_by_id(db, subscription_id)
            if not subscription:
                logger.error(f"Subscription {subscription_id} not found")
                return

            # Skip if subscription is not active
            if subscription.status != models.SubscriptionStatus.ACTIVE:
                logger.info(f"Subscription {subscription_id} is not active (status: {subscription.status}), skipping")
                return

            # Skip if subscription has expired
            from datetime import datetime
            now = datetime.utcnow()
            if subscription.expires_at and subscription.expires_at < now:
                logger.info(f"Subscription {subscription_id} has expired (ended at {subscription.expires_at}), skipping")
                return
            
            # Skip if subscription hasn't started yet
            if subscription.started_at and subscription.started_at > now:
                logger.info(f"Subscription {subscription_id} hasn't started yet (starts at {subscription.started_at}), skipping")
                return
            
            # ⏰ UPDATE NEXT_RUN_AT IMMEDIATELY: Prevent duplicate scheduling
            try:
                bot_timeframe = subscription.bot.timeframe
                next_run = _calculate_next_run(bot_timeframe)
                crud.update_subscription_next_run(db, subscription_id, next_run)
                logger.info(f"⏰ Next run scheduled at {next_run} (preventing duplicate execution)")
            except Exception as e:
                logger.error(f"Failed to update next_run_at at start: {e}")

            # Initialize bot
            bot = initialize_bot(subscription)
            if not bot:
                logger.error(f"Failed to initialize bot for subscription {subscription_id}")
                crud.update_subscription_status(db, subscription_id, schemas.SubscriptionStatus.ERROR)
                return

            # Get exchange credentials - prioritize exchange_credentials table
            exchange_type = subscription.bot.exchange_type or schemas.ExchangeType.BINANCE
            use_testnet = getattr(subscription, 'is_testnet', True)
            if getattr(subscription, 'is_trial', False):
                use_testnet = True
            
            api_key = None
            api_secret = None
            
            if subscription.user_principal_id:
    # Marketplace user - use principal_id (PRIORITY)
                logger.info(f"Looking for exchange credentials for marketplace user (principal: {subscription.user_principal_id})")
                from core.api_key_manager import get_bot_api_keys
                
                # Use get_bot_api_keys which handles TRIAL payment method
                creds = get_bot_api_keys(
                    user_principal_id=subscription.user_principal_id,
                    exchange=exchange_type.value,
                    is_testnet=use_testnet,
                    subscription_id=subscription_id  # Pass subscription_id for TRIAL check
                )
                if creds:
                    api_key = creds.get('api_key')
                    api_secret = creds.get('api_secret')
                    logger.info(f"Found exchange credentials for marketplace user (testnet={use_testnet})")
                else:
                    logger.error(f"No exchange credentials found for marketplace user {subscription.user_principal_id}")
            elif subscription.user_id:
                # Studio user - use user_id (FALLBACK)
                logger.info(f"Looking for exchange credentials for studio user {subscription.user.email}")
                from core.api_key_manager import APIKeyManager
                api_key_manager = APIKeyManager()
                creds = api_key_manager.get_user_exchange_credentials(
                    db=db, 
                    user_id=subscription.user.id, 
                    exchange=exchange_type.value,
                    is_testnet=use_testnet
                )
                if creds:
                    api_key = creds['api_key']
                    api_secret = creds['api_secret']
                    logger.info(f"Found exchange credentials for {exchange_type.value} (testnet={use_testnet})")
                else:
                    # Fallback to user's direct API credentials
                    logger.info(f"No exchange credentials found, checking user direct credentials")
                    api_key = subscription.user.api_key
                    api_secret = subscription.user.api_secret
                    if api_key and api_secret:
                        logger.info(f"Using user direct API credentials")
            else:
                logger.error(f"No user_id or user_principal_id found for subscription {subscription_id}")
            if not api_key or not api_secret:
                logger.error(f"No valid API credentials for subscription {subscription_id}")
                crud.log_bot_action(
                    db, subscription_id, "ERROR", 
                    "No exchange API credentials configured. Please add your exchange credentials in settings."
                )
                return

            is_futures = bool(getattr(subscription.bot, 'bot_type', None) and str(subscription.bot.bot_type).upper() == 'FUTURES')
            bot_type = str(subscription.bot.bot_type).upper() if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type else None
            
            # Only create exchange client for old-style bots (not FUTURES/SPOT/SIGNALS_FUTURES using advanced workflow)
            if not is_futures and bot_type not in ['FUTURES', 'SPOT', 'SIGNALS_FUTURES']:
                logger.info(f"Creating exchange client for subscription {subscription_id} (testnet={use_testnet})")
                
                exchange = ExchangeFactory.create_exchange(
                    exchange_name=exchange_type.value,
                    api_key=api_key,
                    api_secret=api_secret,
                    testnet=use_testnet
                )
            else:
                # FUTURES, SPOT, and SIGNALS_FUTURES bots handle their own exchange clients
                exchange = None
            
            # Get current market data
            trading_pair = subscription.bot.trading_pair or 'BTC/USDT'
            exchange_symbol = trading_pair.replace('/', '')
            try:
                if is_futures:
                    # Use Futures client base_url and endpoints
                    ticker = bot.futures_client.get_ticker(exchange_symbol)
                    current_price = float(ticker['price'])
                elif bot_type == 'SPOT':
                    # SPOT bots have their own spot_client
                    current_price = bot.spot_client.get_current_price(exchange_symbol)
                elif exchange:
                    # Old-style bots use ExchangeFactory client
                    ticker = exchange.get_ticker(exchange_symbol)
                    current_price = float(ticker['price'])
                else:
                    # Fallback: use a reasonable default
                    current_price = 0.0
                    logger.warning(f"Could not get current price for {trading_pair}, using 0.0")
            except Exception as e:
                logger.error(f"Failed to get ticker for {trading_pair}: {e}")
                current_price = 0.0  # Use fallback instead of returning

            # Set bot's exchange client (only for old-style bots)
            if not is_futures and bot_type not in ['FUTURES', 'SPOT', 'SIGNALS_FUTURES'] and exchange:
                bot.exchange_client = exchange
            
            # Create subscription config
            subscription_config = {
                'subscription_id': subscription_id,
                'timeframe': subscription.bot.timeframe,
                'trading_pair': trading_pair,
                'is_testnet': use_testnet,
                'exchange_type': exchange_type.value,
                'user_id': subscription.user_id or 0  # 0 for marketplace users
                }

                # Execute bot prediction - Advanced workflow for Futures, Spot, and Signals bots
            if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type and subscription.bot.bot_type.upper() in ['FUTURES', 'SPOT', 'SIGNALS_FUTURES']:
                logger.info(f"🚀 Using ADVANCED WORKFLOW for {subscription.bot.name} ({subscription.bot.bot_type.upper()})")
                # Run async workflow in event loop
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    final_action, account_status, trade_result = loop.run_until_complete(
                        run_advanced_futures_workflow(bot, subscription_id, subscription_config, db)
                    )
                finally:
                    loop.close()
            else:
                logger.info(f"📊 Using STANDARD WORKFLOW for {subscription.bot.name}")
                final_action = bot.execute_full_cycle(subscription.bot.timeframe, subscription_config)
                account_status = None  # Not available in standard workflow
                
            if final_action:
                logger.info(f"Bot {subscription.bot.name} executed with action: {final_action.action}, value: {final_action.value}, reason: {final_action.reason}")
                
                # Prepare notification status tracking
                notification_status = {
                    "telegram_sent": False,
                    "discord_sent": False,
                    "email_sent": False
                }
                
                # Log action to database with comprehensive information
                crud.log_bot_action(
                    db, subscription_id, final_action.action,
                    details=f"{final_action.reason}. Value: {final_action.value or 0.0}. Price: ${current_price}",
                    price=current_price,
                    quantity=0.0,  # Will be updated if trade is executed
                    balance=account_status.get('available_balance', 0.0) if account_status else 0.0,
                    signal_data={
                        "confidence": final_action.value,
                        "reason": final_action.reason,
                        "timeframe": subscription.bot.timeframe,
                        "trading_pair": trading_pair,
                        "bot_type": subscription.bot.bot_type,
                        "execution_mode": "automated"
                    },
                    account_status=account_status,
                    notification_status=notification_status
                )
                
            # Get balance info for BUY/SELL actions (real API call)
                balance_info = ""
                # Only for old-style bots, not SPOT/FUTURES (they handle their own balance)
                if not is_futures and bot_type not in ['FUTURES', 'SPOT'] and exchange:
                    if final_action.action in ["BUY", "SELL"]:
                        try:
                        # Get balance from exchange using real API
                            # Handle different trading pair formats
                            if '/' in trading_pair:
                                # Format: BTC/USDT
                                base_asset = trading_pair.split('/')[0]  # BTC from BTC/USDT
                                quote_asset = trading_pair.split('/')[1]  # USDT from BTC/USDT
                            else:
                                # Format: BTCUSDT - try to extract base and quote
                                # Common patterns: BTCUSDT, ETHUSDT, etc.
                                if trading_pair.endswith('USDT'):
                                    base_asset = trading_pair[:-4]  # Remove 'USDT' suffix
                                    quote_asset = 'USDT'
                                elif trading_pair.endswith('BTC'):
                                    base_asset = trading_pair[:-3]  # Remove 'BTC' suffix
                                    quote_asset = 'BTC'
                                elif trading_pair.endswith('ETH'):
                                    base_asset = trading_pair[:-3]  # Remove 'ETH' suffix
                                    quote_asset = 'ETH'
                                else:
                                    # Fallback: assume first 3 chars are base, rest is quote
                                    base_asset = trading_pair[:3]
                                    quote_asset = trading_pair[3:]
                                    logger.warning(f"Unknown trading pair format: {trading_pair}, using fallback parsing")
                            
                            base_balance = exchange.get_balance(base_asset)
                            quote_balance = exchange.get_balance(quote_asset)
                            
                            base_total = float(base_balance.free) + float(base_balance.locked)
                            quote_total = float(quote_balance.free) + float(quote_balance.locked)
                            
                            # Calculate portfolio value in USDT
                            portfolio_value = quote_total + (base_total * current_price)
                            
                            mode_label = "TESTNET" if bool(subscription.is_testnet) else "LIVE"
                            balance_info = f"\n💼 Account Balance ({mode_label}):\n" \
                                            f"   • {base_asset}: {base_total:.6f} (Free: {base_balance.free}, Locked: {base_balance.locked})\n" \
                                            f"   • {quote_asset}: {quote_total:.2f} (Free: {quote_balance.free}, Locked: {quote_balance.locked})\n" \
                                            f"   • Portfolio Value: ~${portfolio_value:.2f} USDT\n"
                        except Exception as e:
                            logger.warning(f"Could not get balance info: {e}")
                            mode_label = "TESTNET" if bool(subscription.is_testnet) else "LIVE"
                            balance_info = f"\n💼 Account Balance ({mode_label}): Unable to fetch - {str(e)[:100]}\n"
            
                # Execute actual trading (if not HOLD)
                # Skip if advanced workflow already handled trading (FUTURES/SPOT/SIGNALS_FUTURES bots)
                trade_details = None
                if not is_futures and subscription.bot.bot_type not in ['FUTURES', 'SPOT', 'SIGNALS_FUTURES']:
                    trade_result = False
                    if final_action.action != "HOLD":
                        try:
                            trade_result_data = execute_trade_action(db, subscription, exchange, final_action, current_price)
                            trade_result = trade_result_data.get('success', False)
                            trade_details = trade_result_data
                            
                            if trade_result:
                                logger.info(f"Trade executed successfully: {final_action.action}")
                            else:
                                logger.warning(f"Trade execution failed: {final_action.action}")
                        except Exception as e:
                            logger.error(f"Failed to execute trade: {e}")
                            trade_details = {
                                'success': False,
                                'error': str(e)
                            }
                            crud.log_bot_action(
                                db, subscription_id, "TRADE_ERROR",
                                f"Failed to execute trade: {str(e)}"
                            )
                    else:
                        # For HOLD actions, no trade execution
                        trade_details = {
                            'success': True,
                            'message': 'No trade executed (HOLD signal)'
                        }
                else:
                    # For HOLD actions, no trade execution
                    trade_details = {
                        'success': True,
                        'message': 'No trade executed (HOLD signal)'
                    }
                
                # Send email notification AFTER trade execution
                try:
                    from datetime import datetime
                    from services.email_templates import send_combined_notification
                    # Different emoji for different actions
                    action_emoji = {
                        "BUY": "🟢",
                        "SELL": "🔴", 
                        "HOLD": "🟡"
                    }.get(final_action.action, "📊")
                    
                    # Send combined notification with trade result
                    # Get email for notification (studio user or marketplace user)
                    user_email = subscription.user.email if subscription.user_id else None
                    body_details = {
                            'trading_pair': trading_pair,
                            'current_price': current_price,
                            'reason': final_action.reason,
                            'confidence': final_action.value or 'N/A',
                            'timeframe': subscription.bot.timeframe,
                            'is_testnet': bool(subscription.is_testnet),
                            'balance_info': balance_info,
                            'subscription_id': subscription_id,
                            'trade_details': trade_details
                        }
                    send_combined_notification(
                        user_email,
                        subscription.bot.name,
                        final_action.action,
                        body_details
                    )

                    telegram_chat_id = None
                    discord_user_id = None
                    # Studio user: get from user.user_settings
                    if hasattr(subscription.user, 'user_settings') and subscription.user.user_settings:
                        telegram_chat_id = getattr(subscription.user.user_settings, 'telegram_chat_id', None)
                        discord_user_id = getattr(subscription.user.user_settings, 'discord_user_id', None)
                    # Marketplace user: get from UserSettings by principal_id
                    if not telegram_chat_id or discord_user_id and subscription.user_principal_id:
                        from core import crud
                        users_settings = crud.get_user_settings_by_principal(db, subscription.user_principal_id)
                        if users_settings:
                            telegram_chat_id = getattr(users_settings, 'telegram_chat_id', None)
                            discord_user_id = getattr(users_settings, 'discord_user_id', None)
                    if telegram_chat_id or discord_user_id:
                        logger.info(f"trade_result: {trade_result}")
                        # Build concise remaining balance line
                        remaining_balance_line = "Unable to fetch"
                        try:
                            # Try to parse from previously computed balance string
                            # If detailed values exist from balance_info block, reuse them
                            if '•' in balance_info:
                                # Example lines already computed above
                                # We will not parse; instead, compute again safely using trading_pair parsing
                                if '/' in trading_pair:
                                    base_asset_msg = trading_pair.split('/')[0]
                                    quote_asset_msg = trading_pair.split('/')[1]
                                else:
                                    if trading_pair.endswith('USDT'):
                                        base_asset_msg = trading_pair[:-4]
                                        quote_asset_msg = 'USDT'
                                    elif trading_pair.endswith('BTC'):
                                        base_asset_msg = trading_pair[:-3]
                                        quote_asset_msg = 'BTC'
                                    elif trading_pair.endswith('ETH'):
                                        base_asset_msg = trading_pair[:-3]
                                        quote_asset_msg = 'ETH'
                                    else:
                                        base_asset_msg = trading_pair[:3]
                                        quote_asset_msg = trading_pair[3:]
                                # Fetch quick balances again for a one-line summary
                                bb = exchange.get_balance(base_asset_msg)
                                qb = exchange.get_balance(quote_asset_msg)
                                bt = float(bb.free) + float(bb.locked)
                                qt = float(qb.free) + float(qb.locked)
                                pv = qt + (bt * float(current_price))
                                remaining_balance_line = f"{base_asset_msg}: {bt:.6f}, {quote_asset_msg}: {qt:.2f} (~${pv:.2f} USDT)"
                        except Exception:
                            pass

                        # Extract optional fields
                        entry_price = trade_details.get('current_price', current_price) if isinstance(trade_details, dict) else current_price
                        quantity = trade_details.get('quantity') if isinstance(trade_details, dict) else None
                        base_asset_td = trade_details.get('base_asset') if isinstance(trade_details, dict) else None
                        qty_text = f"{quantity} {base_asset_td}" if quantity and base_asset_td else (str(quantity) if quantity else 'N/A')
                        stop_loss_text = 'N/A'
                        take_profit_text = 'N/A'
                        try:
                            if getattr(final_action, 'recommendation', None):
                                rec = final_action.recommendation
                                sl = rec.get('stop_loss') or rec.get('stop_loss_price')
                                tp = rec.get('take_profit') or rec.get('take_profit_price')
                                if sl is not None:
                                    stop_loss_text = str(sl)
                                # Handle take_profit array format
                                if tp is not None:
                                    if isinstance(tp, list) and len(tp) > 0:
                                        # Format: TP1: $124500 (50%), TP2: $125000 (30%), TP3: $126000 (20%)
                                        tp_parts = []
                                        for tp_level in tp:
                                            level = tp_level.get('level', 'TP')
                                            price = tp_level.get('price', '?')
                                            size_pct = tp_level.get('size_pct', 0)
                                            tp_parts.append(f"{level}: ${price} ({size_pct}%)")
                                        take_profit_text = ', '.join(tp_parts)
                                    else:
                                        take_profit_text = str(tp)
                        except Exception:
                            pass

                        # Format message for all channels using unified format
                        message = format_notification_message(
                            bot_name=subscription.bot.name,
                            balance_info=balance_info,
                            available=account_status.get('available_balance', 0),
                            action=final_action.action,
                            reason=final_action.reason,
                            total_wallet=account_status.get('total_balance', 0),
                            entry_price= trade_result.get('entry_price') if trade_result else None,
                            quantity=trade_result.get('quantity') if trade_result else None,
                            stop_loss=trade_result.get("stop_loss", {}).get("price") if trade_result else None,
                            take_profit=trade_result.get("take_profit", {}).get("price") if trade_result else None,
                        )
                        if telegram_chat_id:
                            send_telegram_notification.delay(telegram_chat_id, message)
                        if discord_user_id:
                            send_discord_notification.delay(discord_user_id, message)
                    else:
                        logger.warning(f"No telegram_chat_id found in user settings for user {subscription.user.id if subscription.user else subscription.user_principal_id or 'N/A'}")

                except Exception as e:
                    logger.error(f"Failed to send signal notification: {e}")
                
            else:
                logger.warning(f"Bot {subscription.bot.name} returned no action")
                crud.log_bot_action(
                    db, subscription_id, "NO_ACTION",
                    "Bot analysis completed but no action was taken"
                )
            
            logger.info(f"✅ Bot execution completed. Next run was already scheduled at start to prevent duplicates.")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in run_bot_logic for subscription {subscription_id}: {e}")
        logger.error(traceback.format_exc())
        
        # Try to log error to database and schedule retry
        try:
            from core.database import SessionLocal
            from core import crud
            from datetime import timedelta
            db = SessionLocal()
            crud.log_bot_action(
                db, subscription_id, "ERROR",
                f"Bot execution failed: {str(e)}"
            )
            
            # Schedule retry after 5 minutes on error
            next_run = datetime.utcnow() + timedelta(minutes=5)
            crud.update_subscription_next_run(db, subscription_id, next_run)
            logger.info(f"⚠️ Bot execution failed. Retry scheduled at {next_run}")
            
            db.close()
        except:
            pass
    
    finally:
        # 🔓 CLEANUP: Release Redis lock
        try:
            if redis_client:
                redis_client.delete(lock_key)
                logger.info(f"🔓 Released execution lock for subscription {subscription_id}")
        except Exception as e:
            logger.warning(f"Failed to release Redis lock: {e}")

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def run_bot_rpa_logic(self, subscription_id: int):
    """Run bot RPA logic for a specific subscription"""
    lock_key = f"bot_execution_rpa_lock_{subscription_id}"
    redis_client = None

    try:
        # Try to acquire Redis lock
        from redis import Redis
        redis_client = Redis(host='redis', port=6379, db=0, decode_responses=True)
        
        # Set lock with 5-minute expiration (longer than typical bot execution)
        lock_acquired = redis_client.set(lock_key, "locked", nx=True, ex=300)
        
        if not lock_acquired:
            logger.info(f"🔒 Bot execution for subscription {subscription_id} already in progress by another worker, skipping")
            return {"status": "skipped", "reason": "duplicate_execution_prevented"}
            
        logger.info(f"🔓 Acquired execution lock for subscription {subscription_id}")
        
    except Exception as e:
        logger.warning(f"Failed to acquire Redis lock, proceeding without lock: {e}")
        redis_client = None  # Disable lock cleanup if Redis unavailable
    
    try:
        from core.database import SessionLocal
        from core import models
        from core import schemas
        from core import crud
        from services.exchange_factory import ExchangeFactory

        db = SessionLocal()

        try:
            logger.info(f"Running bot logic for subscription {subscription_id}")
            # Get subscription
            subscription = crud.get_subscription_by_id(db, subscription_id)
            if not subscription:
                logger.error(f"Subscription {subscription_id} not found")
                return

            # Skip if subscription is not active
            if subscription.status != models.SubscriptionStatus.ACTIVE:
                logger.info(f"Subscription {subscription_id} is not active (status: {subscription.status}), skipping")
                return

            # Skip if subscription has expired
            from datetime import datetime
            now = datetime.utcnow()
            if subscription.expires_at and subscription.expires_at < now:
                logger.info(f"Subscription {subscription_id} has expired (ended at {subscription.expires_at}), skipping")
                return
            
            # Skip if subscription hasn't started yet
            if subscription.started_at and subscription.started_at > now:
                logger.info(f"Subscription {subscription_id} hasn't started yet (starts at {subscription.started_at}), skipping")
                return
            
            # ⏰ UPDATE NEXT_RUN_AT IMMEDIATELY: Prevent duplicate scheduling
            try:
                bot_timeframe = subscription.bot.timeframe
                next_run = _calculate_next_run(bot_timeframe)
                crud.update_subscription_next_run(db, subscription_id, next_run)
                logger.info(f"⏰ Next run scheduled at {next_run} (preventing duplicate execution)")
            except Exception as e:
                logger.error(f"Failed to update next_run_at at start: {e}")

            # Initialize bot
            bot = initialize_bot_rpa_v1(subscription)
            if not bot:
                logger.error(f"Failed to initialize bot for subscription {subscription_id}")
                crud.update_subscription_status(db, subscription_id, schemas.SubscriptionStatus.ERROR)
                return
            
            exchange_type = subscription.bot.exchange_type or schemas.ExchangeType.BINANCE
            use_testnet = getattr(subscription, 'is_testnet', True)
            if getattr(subscription, 'is_trial', False):
                use_testnet = True
            
            api_key = None
            api_secret = None

            if subscription.user_principal_id:
    # Marketplace user - use principal_id (PRIORITY)
                logger.info(f"Looking for exchange credentials for marketplace user (principal: {subscription.user_principal_id})")
                from core.api_key_manager import get_bot_api_keys
                
                # Use get_bot_api_keys which handles TRIAL payment method
                creds = get_bot_api_keys(
                    user_principal_id=subscription.user_principal_id,
                    exchange=exchange_type.value,
                    is_testnet=use_testnet,
                    subscription_id=subscription_id  # Pass subscription_id for TRIAL check
                )
                if creds:
                    api_key = creds.get('api_key')
                    api_secret = creds.get('api_secret')
                    logger.info(f"Found exchange credentials for marketplace user (testnet={use_testnet})")
                else:
                    logger.error(f"No exchange credentials found for marketplace user {subscription.user_principal_id}")
            elif subscription.user_id:
                # Studio user - use user_id (FALLBACK)
                logger.info(f"Looking for exchange credentials for studio user {subscription.user.email}")
                from core.api_key_manager import APIKeyManager
                api_key_manager = APIKeyManager()
                creds = api_key_manager.get_user_exchange_credentials(
                    db=db, 
                    user_id=subscription.user.id, 
                    exchange=exchange_type.value,
                    is_testnet=use_testnet
                )
                if creds:
                    api_key = creds['api_key']
                    api_secret = creds['api_secret']
                    logger.info(f"Found exchange credentials for {exchange_type.value} (testnet={use_testnet})")
                else:
                    # Fallback to user's direct API credentials
                    logger.info(f"No exchange credentials found, checking user direct credentials")
                    api_key = subscription.user.api_key
                    api_secret = subscription.user.api_secret
                    if api_key and api_secret:
                        logger.info(f"Using user direct API credentials")
            else:
                logger.error(f"No user_id or user_principal_id found for subscription {subscription_id}")
            if not api_key or not api_secret:
                logger.error(f"No valid API credentials for subscription {subscription_id}")
                crud.log_bot_action(
                    db, subscription_id, "ERROR", 
                    "No exchange API credentials configured. Please add your exchange credentials in settings."
                )
                return
            
            is_futures = bool(getattr(subscription.bot, 'bot_type', None) and str(subscription.bot.bot_type).upper() == 'FUTURES_RPA')
            bot_type = str(subscription.bot.bot_type).upper() if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type else None
            
            # Only create exchange client for old-style bots (not FUTURES/SPOT using advanced workflow)
            if not is_futures and bot_type not in ['FUTURES', 'SPOT', 'FUTURES_RPA']:
                logger.info(f"Creating exchange client for subscription {subscription_id} (testnet={use_testnet})")
                
                exchange = ExchangeFactory.create_exchange(
                    exchange_name=exchange_type.value,
                    api_key=api_key,
                    api_secret=api_secret,
                    testnet=use_testnet
                )
            else:
                # FUTURES and SPOT bots handle their own exchange clients
                exchange = None
            
            # Get current market data
            trading_pair = subscription.bot.trading_pair or 'BTC/USDT'
            exchange_symbol = trading_pair.replace('/', '')
            try:
                if is_futures:
                    logger.info(f"Using Futures client for {trading_pair}")
                    # Use Futures client base_url and endpoints
                    ticker = bot.futures_client.get_ticker(exchange_symbol)
                    logger.info(f"Futures client ticker: {ticker}")
                    current_price = float(ticker['price'])
                elif bot_type == 'SPOT':
                    # SPOT bots have their own spot_client
                    current_price = bot.spot_client.get_current_price(exchange_symbol)
                elif exchange:
                    # Old-style bots use ExchangeFactory client
                    ticker = exchange.get_ticker(exchange_symbol)
                    current_price = float(ticker['price'])
                else:
                    # Fallback: use a reasonable default
                    current_price = 0.0
                    logger.warning(f"Could not get current price for {trading_pair}, using 0.0")
            except Exception as e:
                logger.error(f"Failed to get ticker for {trading_pair}: {e}")
                current_price = 0.0  # Use fallback instead of returning

            # Set bot's exchange client (only for old-style bots)
            if not is_futures and bot_type not in ['FUTURES', 'SPOT', 'FUTURES_RPA'] and exchange:
                bot.exchange_client = exchange
            
            # Create subscription config
            subscription_config = {
                'subscription_id': subscription_id,
                'timeframe': subscription.bot.timeframe,
                'trading_pair': trading_pair,
                'is_testnet': use_testnet,
                'exchange_type': exchange_type.value,
                'user_id': subscription.user_id or 0  # 0 for marketplace users
            }

                # Execute bot prediction - Advanced workflow for Futures bots
            if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type and subscription.bot.bot_type.upper() == 'FUTURES_RPA':
                logger.info(f"🚀 Using ADVANCED FUTURES WORKFLOW for {subscription.bot.name}")
                # Run async workflow in event loop
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    final_action, account_status, trade_result = loop.run_until_complete(
                        run_advanced_futures_rpa_workflow(bot, subscription_id, subscription_config, db)
                    )
                finally:
                    loop.close()
            else:
                logger.info(f"📊 Using STANDARD WORKFLOW for {subscription.bot.name}")
                final_action = bot.execute_full_cycle(subscription.bot.timeframe, subscription_config)
                account_status = None  # Not available in standard workflow
                
            if final_action:
                logger.info(f"Bot {subscription.bot.name} executed with action: {final_action.action}, value: {final_action.value}, reason: {final_action.reason}")
                
                # Log action to database
                crud.log_bot_action(
                    db, subscription_id, final_action.action,
                    f"{final_action.reason}. Value: {final_action.value or 0.0}. Price: ${current_price}"
                )

                # return {
                #     "status": "success",
                #     "action": final_action.action,
                #     "confidence": final_action.value,
                #     "reason": final_action.reason
                # }
                trade_details = None
                if not is_futures:
                    trade_result = False
                    logger.info(f"Executing trade action for {trading_pair}")
                    if final_action.action != "HOLD":
                        try:
                            trade_result_data = execute_trade_action(db, subscription, exchange, final_action, current_price)
                            trade_result = trade_result_data.get('success', False)
                            trade_details = trade_result_data
                            logger.info(f"Trade result data: {trade_result_data}")
                            if trade_result:
                                logger.info(f"Trade executed successfully: {final_action.action}")
                            else:
                                logger.warning(f"Trade execution failed: {final_action.action}")
                        except Exception as e:
                            logger.error(f"Failed to execute trade: {e}")
                            trade_details = {
                                'success': False,
                                'error': str(e)
                            }
                            crud.log_bot_action(
                                db, subscription_id, "TRADE_ERROR",
                                f"Failed to execute trade: {str(e)}"
                            )
                    else:
                        # For HOLD actions, no trade execution
                        trade_details = {
                            'success': True,
                            'message': 'No trade executed (HOLD signal)'
                        }
                
                # Send email notification AFTER trade execution
                try:
                    from datetime import datetime
                    from services.email_templates import send_combined_notification
                    # Different emoji for different actions
                    action_emoji = {
                        "BUY": "🟢",
                        "SELL": "🔴", 
                        "HOLD": "🟡"
                    }.get(final_action.action, "📊")
                    
                    # Send combined notification with trade result
                    # Get email for notification (studio user or marketplace user)
                    user_email = subscription.user.email if subscription.user_id else None
                    body_details = {
                            'trading_pair': trading_pair,
                            'current_price': current_price,
                            'reason': final_action.reason,
                            'confidence': final_action.value or 'N/A',
                            'timeframe': subscription.bot.timeframe,
                            'is_testnet': bool(subscription.is_testnet),
                            # 'balance_info': balance_info,
                            'subscription_id': subscription_id,
                            'trade_details': trade_details
                        }
                    send_combined_notification(
                        user_email,
                        subscription.bot.name,
                        final_action.action,
                        body_details
                    )

                    telegram_chat_id = None
                    discord_user_id = None
                    # Studio user: get from user.user_settings
                    if hasattr(subscription.user, 'user_settings') and subscription.user.user_settings:
                        telegram_chat_id = getattr(subscription.user.user_settings, 'telegram_chat_id', None)
                        discord_user_id = getattr(subscription.user.user_settings, 'discord_user_id', None)
                    # Marketplace user: get from UserSettings by principal_id
                    if not telegram_chat_id or discord_user_id and subscription.user_principal_id:
                        from core import crud
                        users_settings = crud.get_user_settings_by_principal(db, subscription.user_principal_id)
                        if users_settings:
                            telegram_chat_id = getattr(users_settings, 'telegram_chat_id', None)
                            discord_user_id = getattr(users_settings, 'discord_user_id', None)
                    if telegram_chat_id or discord_user_id:
                        logger.info(f"trade_result: {trade_result}")

                        # Format message for all channels using unified format
                        message = format_notification_message(
                            bot_name=subscription.bot.name,
                            # balance_info=balance_info,
                            available=account_status.get('available_balance', 0),
                            action=final_action.action,
                            reason=final_action.reason,
                            total_wallet=account_status.get('total_balance', 0),
                            entry_price= trade_result.get('entry_price') if trade_result else None,
                            quantity=trade_result.get('quantity') if trade_result else None,
                            stop_loss=trade_result.get("stop_loss", {}).get("price") if trade_result else None,
                            take_profit=trade_result.get("take_profit", {}).get("price") if trade_result else None,
                        )
                        if telegram_chat_id:
                            send_telegram_notification.delay(telegram_chat_id, message)
                        if discord_user_id:
                            send_discord_notification.delay(discord_user_id, message)
                    else:
                        logger.warning(f"No telegram_chat_id found in user settings for user {subscription.user.id if subscription.user else subscription.user_principal_id or 'N/A'}")

                except Exception as e:
                    logger.error(f"Failed to send signal notification: {e}")
                
            else:
                logger.warning(f"Bot {subscription.bot.name} returned no action")
                crud.log_bot_action(
                    db, subscription_id, "NO_ACTION",
                    "Bot analysis completed but no action was taken"
                )
            
            logger.info(f"✅ RPA bot execution completed. Next run was already scheduled at start to prevent duplicates.")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in RPA bot execution: {e}")
        logger.error(traceback.format_exc())
        
        # Try to schedule retry on error
        try:
            from core.database import SessionLocal
            from core import crud
            from datetime import timedelta
            db = SessionLocal()
            
            # Schedule retry after 5 minutes on error
            next_run = datetime.utcnow() + timedelta(minutes=5)
            crud.update_subscription_next_run(db, subscription_id, next_run)
            logger.info(f"⚠️ RPA bot execution failed. Retry scheduled at {next_run}")
            
            db.close()
        except:
            pass
            
        return {"status": "error", "reason": str(e)}
        
    finally:
        # Release lock
        if redis_client:
            try:
                redis_client.delete(lock_key)
                logger.info(f"🔓 Released execution lock for subscription {subscription_id}")
            except Exception as e:
                logger.warning(f"Failed to release lock: {e}")

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def run_bot_signal_logic(self, bot_id: int, subscription_id: int):
    """Run bot signal logic for a specific subscription"""
    lock_key = f"bot_execution_signal_lock_{subscription_id}"
    redis_client = None
    
    try:
        # Try to acquire Redis lock
        from redis import Redis
        redis_client = Redis(host='redis', port=6379, db=0, decode_responses=True)
        
        # Set lock with 5-minute expiration (longer than typical bot execution)
        lock_acquired = redis_client.set(lock_key, "locked", nx=True, ex=300)
        
        if not lock_acquired:
            logger.info(f"🔒 Bot execution for subscription {subscription_id} already in progress by another worker, skipping")
            return {"status": "skipped", "reason": "duplicate_execution_prevented"}
            
        logger.info(f"🔓 Acquired execution lock for subscription {subscription_id}")
        
    except Exception as e:
        logger.warning(f"Failed to acquire Redis lock, proceeding without lock: {e}")
        redis_client = None  # Disable lock cleanup if Redis unavailable
    try: 
        from core import models
        from core import schemas
        from core import crud
        from core.database import SessionLocal
        from datetime import datetime
        import uuid
        import subprocess
        from core.consts.index import MAIN_INDICATORS, SUB_INDICATORS, TIMEFRAME_ROBOT_MAP
        from services.image_analysis import analyze_image_with_openai_text
        from core.schemas import PayLoadAnalysis
        db = SessionLocal()

        try: 
            logger.info(f"Running bot signal logic for subscription {subscription_id}")

            subscription = crud.get_subscription_by_id_and_bot(db, subscription_id, bot_id)
            if not subscription:
                logger.error(f"Subscription {subscription_id} not found")
                return
            
            if subscription.status != models.SubscriptionStatus.ACTIVE:
                logger.info(f"Subscription {subscription_id} is not active (status: {subscription.status}), skipping")
                return
            
            now = datetime.utcnow()
            if subscription.expires_at and subscription.expires_at < now:
                logger.info(f"Subscription {subscription_id} has expired (ended at {subscription.expires_at}), skipping")
                return
            
            # ⏰ UPDATE NEXT_RUN_AT IMMEDIATELY: Prevent duplicate scheduling
            try:
                bot_timeframe = subscription.bot.timeframe
                next_run = _calculate_next_run(bot_timeframe)
                crud.update_subscription_next_run(db, subscription_id, next_run)
                logger.info(f"⏰ Next run scheduled at {next_run} (preventing duplicate execution)")
            except Exception as e:
                logger.error(f"Failed to update next_run_at at start: {e}")
            
            if subscription.user_principal_id:
                session_id = str(uuid.uuid4())
                logger.info(f"Running bot signal logic for subscription {subscription_id} with session ID {session_id}")

                all_strategies = subscription.bot.strategy_config
                main_selected = [s for s in all_strategies if s in MAIN_INDICATORS]
                sub_selected = [s for s in all_strategies if s in SUB_INDICATORS]

                trading_pair = subscription.bot.trading_pair.replace("/", "_") or 'BTC/USDT'

                timeframes_binance = [
                    TIMEFRAME_ROBOT_MAP.get(tf.lower(), tf)
                    for tf in subscription.bot.timeframes
                ]

                primary_timeframe = subscription.bot.timeframe
                primary_tf_mapped = TIMEFRAME_ROBOT_MAP.get(primary_timeframe.lower(), primary_timeframe)
                if primary_tf_mapped not in timeframes_binance:
                    timeframes_binance.append(primary_tf_mapped)
                logger.info(f"🔍 DEBUG: timeframes for robot: {timeframes_binance} and primary: {primary_tf_mapped}")
                robot_file = os.path.abspath("binance.robot")

                driver_path = os.path.abspath("drivers")
                os.environ["PATH"] += os.pathsep + driver_path

                env = os.environ.copy()
                env["BROWSER"] = "chrome"
                print("====== ROBOT  ======")
                sys.stdout.flush()
                logger.info(f"🔍 DEBUG: About to run Robot Framework with session_id: {session_id}")
                sys.stdout.flush()

                logger.info(f"🔍 DEBUG: body run robot: {trading_pair} {timeframes_binance} \n {main_selected} \n {sub_selected}")

                result = subprocess.run([
                    "robot",
                    "--variable", f"session_id:{session_id}",
                    "--variable", f"trading_pair:{trading_pair}",
                    "--variable", f"timeframe:{json.dumps(timeframes_binance)}",
                    "--variable", f"main_indicators:{json.dumps(main_selected)}",
                    "--variable", f"sub_indicators:{json.dumps(sub_selected)}",
                    robot_file
                ], capture_output=True, text=True, env=env,
                    encoding='utf-8',
                    errors='replace')
                logger.info("====== ROBOT STDOUT ======")
                sys.stdout.flush()
                logger.info(result)
                sys.stdout.flush()

                try:
                    print(f"🔍 DEBUG: Robot completed with returncode: {result.returncode}")
                    sys.stdout.flush()
                    print(f"🔍 DEBUG: Now checking for session file...")
                    sys.stdout.flush()

                    image_path_file = os.path.join("/app/screenshots", f"{session_id}_image.txt")
                    print(f"🔍 DEBUG: Looking for session file: {image_path_file}")
                    sys.stdout.flush()
                    print(f"🔍 DEBUG: Session ID: {session_id}")
                    sys.stdout.flush()
                    
                    # Initialize image_paths to avoid UnboundLocalError in finally block
                    image_paths = []
                    
                    # Wait for session file to be created (race condition fix)
                    import time
                    max_retries = 10
                    retry_delay = 0.5

                    for attempt in range(max_retries):
                        if os.path.exists(image_path_file):
                            print(f"✅ DEBUG: Session file found after {attempt + 1} attempts!")
                            sys.stdout.flush()
                            break
                        else:
                            print(f"🔄 DEBUG: Attempt {attempt + 1}/{max_retries} - waiting for session file...")
                            sys.stdout.flush()
                            time.sleep(retry_delay)
                    else:
                        print(f"❌ DEBUG: Session file NOT found after {max_retries} attempts: {image_path_file}")
                        sys.stdout.flush()
                        print("⚠️ Không tìm thấy đường dẫn ảnh đã chụp.")
                        sys.stdout.flush()
                        return
                    
                    with open(image_path_file, "r") as f:
                        content = f.read().strip()
                        image_paths = [line.strip() for line in content.splitlines() if line.strip()]
                        if not image_paths:
                            print("⚠️ Không có ảnh nào được tạo.")
                            return
                        # print(f"📸 DEBUG: Image path from file: {image_path}")
                        sys.stdout.flush()
                    sys.stdout.flush()
                    success = result.returncode == 0

                    bot_config = PayLoadAnalysis(
                        bot_name=subscription.bot.name,
                        trading_pair=subscription.bot.trading_pair,
                        timeframes=subscription.bot.timeframes,
                        primary_timeframe=subscription.bot.timeframe,
                        strategies=subscription.bot.strategy_config,
                        # custom_prompt=subscription.risk_config
                    )

                    response = analyze_image_with_openai_text(image_paths, bot_config)
                    bot_name = f"🤖 BOT {subscription.bot.name}"
                    final_response = f"{bot_name}\n\n{response}"

                    telegram_chat_id = None
                    discord_user_id = None
                    # Studio user: get from user.user_settings
                    if hasattr(subscription.user, 'user_settings') and subscription.user.user_settings:
                        telegram_chat_id = getattr(subscription.user.user_settings, 'telegram_chat_id', None)
                        discord_user_id = getattr(subscription.user.user_settings, 'discord_user_id', None)
                    # Marketplace user: get from UserSettings by principal_id
                    if not telegram_chat_id or discord_user_id and subscription.user_principal_id:
                        from core import crud
                        users_settings = crud.get_user_settings_by_principal(db, subscription.user_principal_id)
                        if users_settings:
                            telegram_chat_id = getattr(users_settings, 'telegram_chat_id', None)
                            discord_user_id = getattr(users_settings, 'discord_user_id', None)
                    logger.info(f"telegram chat id and discord user id: {telegram_chat_id}, {discord_user_id}")
                    if telegram_chat_id:
                        send_telegram_beauty_notification.delay(telegram_chat_id, final_response)
                    if discord_user_id:
                        send_discord_notification.delay(discord_user_id, final_response)
                    
                    logger.info(f"✅ Signal bot execution completed. Next run was already scheduled at start to prevent duplicates.")
                        
                except Exception as e:
                    logger.error(f"🚨 EXCEPTION in scheduled_bot_task: {e}")
                    sys.stdout.flush()
                    import traceback
                    logger.error(f"🚨 TRACEBACK: {traceback.format_exc()}")
                    sys.stdout.flush()
                    
                    # Try to schedule retry on error
                    try:
                        from datetime import timedelta
                        from core import crud
                        next_run = datetime.utcnow() + timedelta(minutes=5)
                        crud.update_subscription_next_run(db, subscription_id, next_run)
                        logger.info(f"⚠️ Signal bot execution failed. Retry scheduled at {next_run}")
                    except:
                        pass
                        
                finally:
                    if os.path.exists(image_path_file):
                        try:
                            os.remove(image_path_file)
                            print(f"✅ Removed session file: {image_path_file}")
                        except Exception as e:
                            print(f"❌ Error removing session file: {e}")
                    # Xóa tất cả ảnh đã dùng nếu tồn tại
                    for img_path in image_paths:
                        if os.path.exists(img_path):
                            try:
                                os.remove(img_path)
                                print(f"🧹 Removed image: {img_path}")
                            except Exception as e:
                                print(f"❌ Error removing image {img_path}: {e}")

                    db.close()
                        
            return
        except Exception as e:
            logger.error(f"🚨 EXCEPTION in scheduled_bot_task: {e}")
            sys.stdout.flush()
            import traceback
            logger.error(f"🚨 TRACEBACK: {traceback.format_exc()}")
            sys.stdout.flush()
            return
    except Exception as e:
            logger.error(f"🚨 EXCEPTION in scheduled_bot_task: {e}")
            sys.stdout.flush()
            import traceback
            logger.error(f"🚨 TRACEBACK: {traceback.format_exc()}")
            sys.stdout.flush()
            return
    finally:
        # 🔓 CLEANUP: Release Redis lock
        try:
            if redis_client:
                redis_client.delete(lock_key)
                logger.info(f"🔓 Released execution lock for subscription {subscription_id}")
        except Exception as e:
            logger.warning(f"Failed to release Redis lock: {e}")

@app.task
def schedule_active_bots():
    """Schedule active bots for execution"""
    try:
        from core.database import SessionLocal
        from core import crud
        from core import models
        
        db = SessionLocal()
        
        try:
            # Get all active subscriptions
            active_subscriptions = crud.get_active_subscriptions(db)
            
            for subscription in active_subscriptions:
                # Check subscription time range first
                now = datetime.utcnow()
                
                # Skip if subscription has expired
                if subscription.expires_at and subscription.expires_at < now:
                    logger.debug(f"Subscription {subscription.id} has expired (ended at {subscription.expires_at}), skipping")
                    continue
                
                # Skip if subscription hasn't started yet
                if subscription.started_at and subscription.started_at > now:
                    logger.debug(f"Subscription {subscription.id} hasn't started yet (starts at {subscription.started_at}), skipping")
                    continue
                
                # Check if it's time to run this bot
                should_run = False
                
                if subscription.next_run_at:
                    # If next_run_at is set, check if it's time to run
                    should_run = subscription.next_run_at <= now
                else:
                    # If next_run_at is NULL, run immediately
                    should_run = True
                    logger.info(f"Subscription {subscription.id} has no next_run_at, scheduling immediately")
                
                if should_run:
                    logger.info(f"Scheduling bot execution for subscription {subscription.id}")
                    
                    # Convert bot_type enum to string for comparison
                    bot_type_str = str(subscription.bot.bot_type).upper() if subscription.bot.bot_type else None
                    bot_mode_str = str(subscription.bot.bot_mode).upper() if subscription.bot.bot_mode else "ACTIVE"
                    
                    # Handle SIGNALS_FUTURES type (signals-only futures bot using bot template)
                    if bot_type_str == "SIGNALS_FUTURES":
                        run_bot_logic.delay(subscription.id)
                        logger.info(f"✅ Triggered run_bot_logic for SIGNALS_FUTURES bot (subscription {subscription.id})")
                    elif bot_mode_str != "PASSIVE" and bot_type_str in ["FUTURES", "SPOT"]:
                        # Active FUTURES and SPOT bots use run_bot_logic
                        run_bot_logic.delay(subscription.id)
                        logger.info(f"✅ Triggered run_bot_logic for {bot_type_str} bot (subscription {subscription.id})")
                    elif bot_type_str == "FUTURES_RPA":
                        run_bot_rpa_logic.delay(subscription.id)
                        logger.info(f"✅ Triggered run_bot_rpa_logic for RPA bot (subscription {subscription.id})")
                    else:
                        # Handle PASSIVE bots (legacy signal-only using Robot Framework)
                        run_bot_signal_logic.delay(subscription.bot.id, subscription.id)
                        logger.info(f"✅ Triggered run_bot_signal_logic for PASSIVE bot (subscription {subscription.id})")

                    # ✅ NOTE: next_run_at is now updated by the task itself after completion
                    # This ensures accurate scheduling based on actual execution time
                else:
                    logger.debug(f"Subscription {subscription.id} not ready to run yet. Next run: {subscription.next_run_at}")
                    
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in schedule_active_bots: {e}")
        logger.error(traceback.format_exc())

@app.task
def cleanup_old_logs():
    """Clean up old bot action logs"""
    try:
        from core.database import SessionLocal
        from core import crud
        
        # Clean up logs older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        deleted_count = crud.cleanup_old_bot_actions(cutoff_date)
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old bot action logs")
            
    except Exception as e:
        logger.error(f"Error in cleanup_old_logs: {e}")
        logger.error(traceback.format_exc())

@app.task
def send_email_notification(email: str, subject: str, body: str):
    """Send email notification"""
    try:
        from services.sendgrid_email_service import SendGridEmailService
        from services.gmail_smtp_service import GmailSMTPService
        
        # Try SendGrid first
        try:
            sendgrid_service = SendGridEmailService()
            success = sendgrid_service.send_email(email, subject, body)
            if success:
                    logger.info(f"Email sent via SendGrid to {email}")
                    return
        except Exception as e:
            logger.warning(f"SendGrid failed: {e}")
        
        # Fallback to Gmail SMTP
        try:
            gmail_service = GmailSMTPService()
            success = gmail_service.send_email(email, subject, body)
            if success:
                logger.info(f"Email sent via Gmail SMTP to {email}")
                return
        except Exception as e:
            logger.warning(f"Gmail SMTP failed: {e}")
        
        logger.error(f"All email services failed for {email}")
        
    except Exception as e:
        logger.error(f"Error sending email notification: {e}")

@app.task
def send_telegram_notification(chat_id, text):
    from services.telegram_service import TelegramService
    telegram_service = TelegramService()
    telegram_service.send_telegram_message_v2(chat_id=chat_id, text=text)

@app.task 
def send_telegram_beauty_notification(chat_id, text):
    from services.telegram_service import TelegramService
    telegram_service = TelegramService()
    telegram_service.send_message_safe_telegram(chat_id=chat_id, text=text)

@app.task
def send_discord_notification(user_id, message):
    try:
        queue_discord_dm(user_id, message)
        logger.info(f"Queued Discord DM to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to queue Discord DM: {e}")

@app.task
def send_sendgrid_notification(email: str, bot_name: str, action: str, details: dict):
    """Send SendGrid notification"""
    try:
        from services.sendgrid_email_service import SendGridEmailService
        
        sendgrid_service = SendGridEmailService()
        success = sendgrid_service.send_trade_notification(email, bot_name, action, details)
        
        if success:
            logger.info(f"SendGrid notification sent to {email}")
        else:
            logger.error(f"Failed to send SendGrid notification to {email}")
            
    except Exception as e:
        logger.error(f"Error sending SendGrid notification: {e}")

@app.task
def test_task():
    """Test task for debugging"""
    logger.info("Test task executed successfully")
    return "Test task completed"

@app.task(bind=True)
def run_futures_bot_trading(self, user_principal_id: str = None, config: Dict[str, Any] = None):
    """
    Celery task to run Binance Futures Bot with auto-confirmation
    
    Args:
        user_principal_id: Optional user principal ID for database API keys
        config: Bot configuration override
    """
    try:
        import sys
        import os
        import asyncio
        
        # Add bot_files to path
        bot_files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_files')
        if bot_files_path not in sys.path:
            sys.path.insert(0, bot_files_path)
        
        from binance_futures_bot import BinanceFuturesBot, main_execution
        
        logger.info(f"🚀 Starting Futures Bot Celery task")
        logger.info(f"   User Principal ID: {user_principal_id or 'None (Direct Keys)'}")
        logger.info(f"   Config provided: {'Yes' if config else 'No'}")
        
        # Log task start to database
        try:
            from utils.execution_logger import ExecutionLogger
            bot_id = config.get('bot_id', 1) if config else 1
            subscription_id = config.get('subscription_id') if config else None
            execution_logger = ExecutionLogger(bot_id, subscription_id, self.request.id)
            execution_logger.system(
                "Futures Bot Celery task started",
                {
                    'user_principal_id': user_principal_id,
                    'config_provided': bool(config),
                    'trading_pair': config.get('trading_pair', 'BTCUSDT') if config else 'BTCUSDT'
                }
            )
        except Exception as e:
            logger.error(f"❌ Failed to log task start: {e}")
        
        # Default configuration for Celery execution
        default_config = {
            'trading_pair': 'BTCUSDT',
            'testnet': True,
            'leverage': 10,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04,
            'position_size_pct': 0.05,
            'timeframes': ['30m', '1h', '4h'],
            'primary_timeframe': '1h',
            'use_llm_analysis': True,
            'llm_model': 'openai',
            'require_confirmation': False,  # Disable confirmation for Celery
            'auto_confirm': True,  # Enable auto-confirmation
            'bot_id': None,  # Will be set from config if provided
            'subscription_id': None  # Will be set from config if provided
        }
        
        # Merge with provided config
        if config:
            default_config.update(config)
        
        # Log bot_id and subscription_id for debugging
        logger.info(f"📋 Config: bot_id={default_config.get('bot_id')}, subscription_id={default_config.get('subscription_id')}")
        
        # Normalize trading pair: remove '/' for Binance Futures API (BTC/USDT → BTCUSDT)
        if 'trading_pair' in default_config and '/' in default_config['trading_pair']:
            original_pair = default_config['trading_pair']
            default_config['trading_pair'] = original_pair.replace('/', '')
            logger.info(f"🔧 Normalized trading pair: {original_pair} → {default_config['trading_pair']}")
            
        logger.info(f"🤖 Bot Config: {default_config['trading_pair']} | {len(default_config['timeframes'])} timeframes | Auto-confirm: ON")
        
        # LLM API keys - get from environment
        llm_api_keys = {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'claude_api_key': os.getenv('CLAUDE_API_KEY'),
            'gemini_api_key': os.getenv('GEMINI_API_KEY')
        }
        
        # Exchange API keys MUST come from database via principal ID
        if not user_principal_id:
            logger.error("user_principal_id is required for Celery tasks - all exchange keys must come from database")
            return {'status': 'error', 'message': 'user_principal_id is required'}
        
        # Initialize bot - ONLY database lookup allowed
        logger.info(f"🏦 Using database API keys for principal: {user_principal_id}")
        bot = BinanceFuturesBot(default_config, api_keys=llm_api_keys, user_principal_id=user_principal_id)
        
        # Run the trading cycle asynchronously
        async def run_trading_cycle():
            try:
                # Check account status
                account_status = bot.check_account_status()
                logger.info(f"💰 Account Status: {account_status}")
                
                # Crawl multi-timeframe data
                multi_timeframe_data = bot.crawl_data()
                if not multi_timeframe_data.get("timeframes"):
                    logger.error("❌ Failed to crawl multi-timeframe data")
                    return {'status': 'error', 'message': 'Data crawl failed'}
                
                logger.info(f"📊 Crawled {len(multi_timeframe_data['timeframes'])} timeframes")
                
                # Analyze data
                analysis = bot.analyze_data(multi_timeframe_data)
                if 'error' in analysis:
                    logger.error(f"❌ Analysis error: {analysis['error']}")
                    return {'status': 'error', 'message': f'Analysis failed: {analysis["error"]}'}
                
                # Generate signal
                signal = bot.generate_signal(analysis)
                logger.info(f"🎯 Signal: {signal.action} | Confidence: {signal.value*100:.1f}% | Reason: {signal.reason}")
                
                # Execute trade (auto-confirmed)
                trade_result = None
                if signal.action != "HOLD":
                    logger.info(f"🚀 AUTO-EXECUTING {signal.action} trade via Celery...")
                    trade_result = await bot.setup_position(signal, analysis, subscription)
                    
                    # Save transaction if successful
                    if trade_result.get('status') == 'success':
                        bot.save_transaction_to_db(trade_result)
                        logger.info(f"✅ Trade executed and saved: {trade_result.get('main_order_id')}")
                        
                        # Log detailed execution to database for UI display
                        try:
                            # Format comprehensive trade details
                            log_details = format_trade_log_details(trade_result, signal, bot.trading_pair)
                            
                            crud.log_bot_action(
                                db, subscription_id, signal.action,
                                details=log_details,
                                price=trade_result.get('entry_price', 0),
                                quantity=float(trade_result.get('quantity', 0)),
                                balance=account_status.get('available_balance', 0) if account_status else 0,
                                signal_data={
                                    'confidence': signal.value,
                                    'reason': signal.reason,
                                    'timeframe': timeframes[0] if timeframes else '1h',
                                    'trading_pair': bot.trading_pair,
                                    'bot_type': 'FUTURES',
                                    'execution_mode': 'automated',
                                    'exchange': bot.exchange_name
                                },
                                trade_result={
                                    'entry_price': trade_result.get('entry_price'),
                                    'quantity': trade_result.get('quantity'),
                                    'leverage': trade_result.get('leverage'),
                                    'stop_loss': trade_result.get('stop_loss', {}).get('price') if isinstance(trade_result.get('stop_loss'), dict) else trade_result.get('stop_loss'),
                                    'take_profit': trade_result.get('take_profit', {}).get('price') if isinstance(trade_result.get('take_profit'), dict) else trade_result.get('take_profit'),
                                    'position_value': trade_result.get('position_value'),
                                    'order_id': trade_result.get('main_order_id'),
                                    'status': 'OPEN',
                                    'exchange': trade_result.get('exchange')
                                },
                                account_status=account_status
                            )
                            logger.info("📝 Trade logged to database for UI display")
                        except Exception as log_error:
                            logger.error(f"❌ Failed to log trade action: {log_error}")
                            import traceback
                            logger.error(traceback.format_exc())
                    else:
                        logger.error(f"❌ Trade failed: {trade_result}")
                else:
                    trade_result = {'status': 'success', 'action': 'HOLD', 'reason': signal.reason}
                
                return {
                    'status': 'success',
                    'signal': {
                        'action': signal.action,
                        'confidence': signal.value,
                        'reason': signal.reason
                    },
                    'trade_result': trade_result,
                    'account_status': account_status,
                    'timeframes_analyzed': len(analysis.get('multi_timeframe', {})),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"❌ Error in trading cycle: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return {'status': 'error', 'message': str(e)}
        
        # Run the async trading cycle
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_trading_cycle())
            logger.info(f"🎉 Futures Bot Celery task completed: {result['status']}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Error in Futures Bot Celery task: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'status': 'error', 'message': str(e)}

@app.task(bind=True)
def schedule_futures_bot_trading(self, interval_minutes: int = 60, user_principal_id: str = None, config: Dict[str, Any] = None):
    """
    Schedule periodic Futures Bot trading
    
    Args:
        interval_minutes: Interval between trades in minutes
        user_principal_id: Optional user principal ID
        config: Bot configuration override
    """
    try:
        logger.info(f"⏰ Scheduling Futures Bot every {interval_minutes} minutes")
        
        # Execute the bot immediately
        result = run_futures_bot_trading.delay(user_principal_id, config)
        
        # Schedule next execution
        schedule_futures_bot_trading.apply_async(
            args=[interval_minutes, user_principal_id, config],
            countdown=interval_minutes * 60  # Convert to seconds
        )
        
        logger.info(f"✅ Futures Bot scheduled and executed. Next run in {interval_minutes} minutes")
        return {'status': 'scheduled', 'next_run_in_minutes': interval_minutes}
        
    except Exception as e:
        logger.error(f"❌ Error scheduling Futures Bot: {e}")
        return {'status': 'error', 'message': str(e)}

def apply_risk_management(subscription, signal, analysis, account_status, db):
    """
    Apply risk management rules before executing trade
    Returns: (approved: bool, reason: str, adjusted_signal: Action)
    """
    try:
        from core import schemas, crud
        from datetime import datetime, timedelta
        
        logger.info("=" * 80)
        logger.info("🛡️ RISK MANAGEMENT CHECK START")
        logger.info("=" * 80)
        
        # Get risk config: Subscription override OR Bot default
        risk_config_dict = subscription.bot.risk_config
        
        if subscription.bot.risk_config:
            logger.info("📋 Using BOT-LEVEL risk config (default)")
        else:
            logger.info("✅ No risk management configured, trade approved")
            logger.info("=" * 80)
            return True, "No risk management configured", signal
        
        # Debug: Log raw config dict
        logger.info(f"\n📋 Raw Risk Config Dict:")
        logger.info(f"   Type: {type(risk_config_dict)}")
        import json
        logger.info(f"   Content: {json.dumps(risk_config_dict, indent=2, default=str)}")
        
        risk_config = schemas.RiskConfig(**risk_config_dict)
        
        # Debug: Log parsed config
        logger.info(f"\n🔧 Parsed Risk Config:")
        logger.info(f"   Mode: {risk_config.mode}")
        logger.info(f"   Daily Loss Limit: {risk_config.daily_loss_limit_percent}")
        logger.info(f"   Min R/R Ratio: {risk_config.min_risk_reward_ratio}")
        logger.info(f"   Max Leverage: {risk_config.max_leverage}")
        logger.info(f"   Max Position Size: {risk_config.max_position_size}")
        
        logger.info(f"\n📊 Signal: {signal.action} | Confidence: {signal.value*100:.1f}%")
        
        # Log all configured rules
        logger.info("\n📋 Configured Risk Rules:")
        if risk_config.stop_loss_percent:
            logger.info(f"  • Stop Loss: {risk_config.stop_loss_percent}%")
        if risk_config.take_profit_percent:
            logger.info(f"  • Take Profit: {risk_config.take_profit_percent}%")
        if risk_config.min_risk_reward_ratio:
            logger.info(f"  • Min Risk/Reward: {risk_config.min_risk_reward_ratio}:1")
        if risk_config.max_leverage:
            logger.info(f"  • Max Leverage: {risk_config.max_leverage}x")
        if risk_config.daily_loss_limit_percent:
            logger.info(f"  • Daily Loss Limit: {risk_config.daily_loss_limit_percent}%")
        if risk_config.trading_window and risk_config.trading_window.enabled:
            logger.info(f"  • Trading Window: {risk_config.trading_window.start_hour}:00-{risk_config.trading_window.end_hour}:00 UTC")
        if risk_config.cooldown and risk_config.cooldown.enabled:
            logger.info(f"  • Cooldown: {risk_config.cooldown.cooldown_minutes} min after {risk_config.cooldown.trigger_loss_count} losses")
        
        logger.info("\n🔍 Starting Risk Checks...")
        
        # 1. Check trading window
        logger.info("\n1️⃣ Trading Window Check:")
        if risk_config.trading_window and risk_config.trading_window.enabled:
            now = datetime.utcnow()
            current_hour = now.hour
            current_day = now.weekday()  # 0=Monday, 6=Sunday
            day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            
            logger.info(f"  Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            logger.info(f"  Current Day: {day_names[current_day]} ({current_day})")
            logger.info(f"  Current Hour: {current_hour}:00")
            
            window = risk_config.trading_window
            if window.days_of_week:
                allowed_days = [day_names[d] for d in window.days_of_week]
                logger.info(f"  Allowed Days: {', '.join(allowed_days)}")
                
                if current_day not in window.days_of_week:
                    logger.warning(f"  ❌ REJECTED: Current day {day_names[current_day]} not in allowed days")
                    logger.warning("\n" + "=" * 80)
                    logger.warning("🚫 RISK MANAGEMENT: TRADE REJECTED")
                    logger.warning("=" * 80)
                    logger.warning(f"   Reason: Outside trading window (day check)")
                    logger.warning(f"   Current Day: {day_names[current_day]} ({current_day})")
                    logger.warning(f"   Allowed Days: {', '.join([day_names[d] for d in window.days_of_week])}")
                    logger.warning(f"   Config Source: {risk_config.mode} mode")
                    logger.warning("=" * 80)
                    return False, f"Outside trading window: Current day {current_day} not in allowed days {window.days_of_week}", signal
                else:
                    logger.info(f"  ✅ Day check passed")
            
            if window.start_hour is not None and window.end_hour is not None:
                logger.info(f"  Allowed Hours: {window.start_hour}:00 - {window.end_hour}:00 UTC")
                
                if window.start_hour <= window.end_hour:
                    is_allowed = window.start_hour <= current_hour < window.end_hour
                else:
                    is_allowed = current_hour >= window.start_hour or current_hour < window.end_hour
                
                if not is_allowed:
                    logger.warning(f"  ❌ REJECTED: Current hour {current_hour}:00 outside allowed window")
                    logger.warning("\n" + "=" * 80)
                    logger.warning("🚫 RISK MANAGEMENT: TRADE REJECTED")
                    logger.warning("=" * 80)
                    logger.warning(f"   Reason: Outside trading window (hour check)")
                    logger.warning(f"   Current Hour: {current_hour}:00 UTC")
                    logger.warning(f"   Allowed Hours: {window.start_hour}:00 - {window.end_hour}:00 UTC")
                    logger.warning(f"   Config Source: {risk_config.mode} mode")
                    logger.warning("=" * 80)
                    return False, f"Outside trading window: {window.start_hour}:00-{window.end_hour}:00 UTC", signal
                else:
                    logger.info(f"  ✅ Hour check passed")
        else:
            logger.info("  ⏭️ Trading window not configured, skipping")
        
        # 2. Check cooldown status
        logger.info("\n2️⃣ Cooldown Status Check:")
        if subscription.cooldown_until:
            now = datetime.utcnow()
            logger.info(f"  Cooldown Until: {subscription.cooldown_until}")
            logger.info(f"  Current Time: {now}")
            logger.info(f"  Consecutive Losses: {subscription.consecutive_losses or 0}")
            
            if now < subscription.cooldown_until:
                remaining = (subscription.cooldown_until - now).total_seconds() / 60
                logger.warning(f"  ❌ REJECTED: In cooldown for {remaining:.1f} more minutes")
                logger.warning("\n" + "=" * 80)
                logger.warning("🚫 RISK MANAGEMENT: TRADE REJECTED")
                logger.warning("=" * 80)
                logger.warning(f"   Reason: Active cooldown period")
                logger.warning(f"   Consecutive Losses: {subscription.consecutive_losses or 0}")
                logger.warning(f"   Cooldown Until: {subscription.cooldown_until}")
                logger.warning(f"   Remaining: {remaining:.1f} minutes")
                logger.warning(f"   Config Source: {risk_config.mode} mode")
                logger.warning("=" * 80)
                return False, f"In cooldown for {remaining:.1f} more minutes", signal
            else:
                logger.info(f"  ✅ Cooldown expired, clearing status")
                subscription.cooldown_until = None
                db.commit()
        else:
            logger.info("  ✅ No active cooldown")
        
        # 3. Check daily loss limit
        logger.info("\n3️⃣ Daily Loss Limit Check:")
        logger.info(f"  Config Daily Loss Limit: {risk_config.daily_loss_limit_percent}%")
        logger.info(f"  Account Status Available: {account_status is not None}")
        
        if risk_config.daily_loss_limit_percent:
            if not account_status:
                logger.warning(f"  ⚠️ Daily loss limit configured ({risk_config.daily_loss_limit_percent}%) but account_status is None")
                logger.warning(f"  ⏭️ Skipping check (cannot verify without account balance)")
            else:
                available_balance = account_status.get('available_balance', 0)
                daily_loss = float(subscription.daily_loss_amount or 0)
                
                logger.info(f"  Available Balance: ${available_balance:.2f}")
                logger.info(f"  Daily Loss Limit: {risk_config.daily_loss_limit_percent}%")
                logger.info(f"  Current Daily Loss: ${daily_loss:.2f}")
                
                # Reset daily loss if new day
                now = datetime.utcnow()
                if subscription.last_loss_reset_date != now.date():
                    logger.info(f"  🔄 New day detected, resetting daily loss counter")
                    logger.info(f"     Last Reset: {subscription.last_loss_reset_date}")
                    logger.info(f"     Current Date: {now.date()}")
                    subscription.daily_loss_amount = 0
                    subscription.last_loss_reset_date = now.date()
                    db.commit()
                    daily_loss = 0
                
                loss_limit = available_balance * (risk_config.daily_loss_limit_percent / 100)
                logger.info(f"  Calculated Loss Limit: ${loss_limit:.2f}")
                
                if daily_loss >= loss_limit:
                    logger.warning(f"  ❌ REJECTED: Daily loss limit reached: ${daily_loss:.2f} >= ${loss_limit:.2f}")
                    logger.warning("\n" + "=" * 80)
                    logger.warning("🚫 RISK MANAGEMENT: TRADE REJECTED")
                    logger.warning("=" * 80)
                    logger.warning(f"   Reason: Daily loss limit exceeded")
                    logger.warning(f"   Daily Loss Limit: {risk_config.daily_loss_limit_percent}%")
                    logger.warning(f"   Available Balance: ${available_balance:.2f}")
                    logger.warning(f"   Loss Limit Amount: ${loss_limit:.2f}")
                    logger.warning(f"   Current Daily Loss: ${daily_loss:.2f}")
                    logger.warning(f"   Over Limit By: ${daily_loss - loss_limit:.2f}")
                    logger.warning(f"   Config Source: {risk_config.mode} mode")
                    logger.warning("=" * 80)
                    return False, f"Daily loss limit reached: ${daily_loss:.2f} >= ${loss_limit:.2f}", signal
                else:
                    remaining = loss_limit - daily_loss
                    logger.info(f"  ✅ Within limit (${remaining:.2f} remaining)")
        else:
            logger.info("  ⏭️ Daily loss limit not configured in risk config")
        
        # 4. Check minimum Risk/Reward ratio
        logger.info("\n4️⃣ Risk/Reward Ratio Check:")
        logger.info(f"  Config Min R/R Ratio: {risk_config.min_risk_reward_ratio}")
        logger.info(f"  Signal has 'recommendation' attribute: {hasattr(signal, 'recommendation')}")
        
        if risk_config.min_risk_reward_ratio:
            if not hasattr(signal, 'recommendation'):
                logger.warning(f"  ⚠️ Min R/R ratio configured ({risk_config.min_risk_reward_ratio}:1) but signal has no 'recommendation' attribute")
                logger.info(f"     Signal type: {type(signal)}")
                logger.info(f"     Signal attributes: {dir(signal)}")
                logger.warning(f"  ⏭️ Skipping check (signal doesn't provide R/R data)")
            else:
                rec = signal.recommendation
                logger.info(f"  Recommendation data: {rec}")
                
            if rec and 'risk_reward' in rec:
                rr_value = rec.get('risk_reward')
                
                # Skip if risk_reward is N/A or invalid
                if rr_value in ['N/A', 'n/a', None, '']:
                    logger.info(f"  ⏭️ Risk/Reward is '{rr_value}' - Skipping R/R check (TP/SL from risk_config will be used)")
                else:
                    try:
                        rr = float(rr_value)
                        logger.info(f"  Current R/R Ratio: {rr:.2f}:1")
                        logger.info(f"  Minimum Required: {risk_config.min_risk_reward_ratio}:1")
                        
                        if rr < risk_config.min_risk_reward_ratio:
                            logger.warning(f"  ❌ REJECTED: Risk/Reward ratio too low: {rr:.2f} < {risk_config.min_risk_reward_ratio}")
                            logger.warning("\n" + "=" * 80)
                            logger.warning("🚫 RISK MANAGEMENT: TRADE REJECTED")
                            logger.warning("=" * 80)
                            logger.warning(f"   Reason: Risk/Reward ratio below minimum")
                            logger.warning(f"   Min R/R Required: {risk_config.min_risk_reward_ratio}:1")
                            logger.warning(f"   LLM Provided R/R: {rr:.2f}:1")
                            logger.warning(f"   Shortfall: {risk_config.min_risk_reward_ratio - rr:.2f}")
                            if rec:
                                logger.warning(f"   LLM Entry: {rec.get('entry_price', 'N/A')}")
                                logger.warning(f"   LLM Stop Loss: {rec.get('stop_loss', 'N/A')}")
                                logger.warning(f"   LLM Take Profit: {rec.get('take_profit', 'N/A')}")
                            logger.warning(f"   Config Source: {risk_config.mode} mode")
                            logger.warning("=" * 80)
                            return False, f"Risk/Reward ratio too low: {rr:.2f} < {risk_config.min_risk_reward_ratio}", signal
                        else:
                            logger.info(f"  ✅ R/R ratio acceptable")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"  ⚠️ Could not parse risk_reward: {rr_value} - Error: {e}")
                        logger.info(f"  ⏭️ Skipping R/R check (TP/SL from risk_config will be used)")
            else:
                logger.warning(f"  ⚠️ Recommendation exists but no 'risk_reward' field found")
                logger.info(f"     Available fields: {list(rec.keys()) if rec else 'None'}")
                logger.warning(f"  ⏭️ Skipping check")
        else:
            logger.info("  ⏭️ Min R/R ratio not configured in risk config")
        
        # 5. Adjust leverage if max_leverage is set
        logger.info("\n5️⃣ Leverage Check & Adjustment:")
        logger.info(f"  Config Max Leverage: {risk_config.max_leverage}x")
        logger.info(f"  Signal has 'recommendation' attribute: {hasattr(signal, 'recommendation')}")
        
        if risk_config.max_leverage:
            if not hasattr(signal, 'recommendation'):
                logger.warning(f"  ⚠️ Max leverage configured ({risk_config.max_leverage}x) but signal has no 'recommendation' attribute")
                logger.warning(f"  ⏭️ Skipping check (signal doesn't provide leverage data)")
            else:
                rec = signal.recommendation
                logger.info(f"  Recommendation type: {type(rec)}")
                
                if rec and 'leverage' in rec:
                    try:
                        leverage = int(rec['leverage'])
                        logger.info(f"  Current Leverage: {leverage}x")
                        logger.info(f"  Max Allowed: {risk_config.max_leverage}x")
                        
                        if leverage > risk_config.max_leverage:
                            logger.warning(f"  ⚠️ Leverage adjusted: {leverage}x → {risk_config.max_leverage}x")
                            rec['leverage'] = risk_config.max_leverage
                        else:
                            logger.info(f"  ✅ Leverage within limit")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"  ⚠️ Could not parse leverage: {rec.get('leverage')} - Error: {e}")
                else:
                    logger.warning(f"  ⚠️ Recommendation exists but no 'leverage' field found")
                    logger.info(f"     Available fields: {list(rec.keys()) if rec else 'None'}")
                    logger.warning(f"  ⏭️ Skipping check")
        else:
            logger.info("  ⏭️ Max leverage not configured in risk config")
        
        # Final Summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ RISK MANAGEMENT: ALL CHECKS PASSED")
        logger.info("=" * 80)
        
        # Detailed approval reason
        approval_summary = []
        approval_summary.append(f"✅ Mode: {risk_config.mode}")
        
        if risk_config.trading_window and risk_config.trading_window.enabled:
            approval_summary.append(f"✅ Trading Window: Within allowed time")
        
        if subscription.cooldown_until:
            approval_summary.append(f"✅ Cooldown: No active cooldown")
        
        if risk_config.daily_loss_limit_percent and account_status:
            daily_loss = float(subscription.daily_loss_amount or 0)
            available_balance = account_status.get('available_balance', 0)
            loss_limit = available_balance * (risk_config.daily_loss_limit_percent / 100)
            remaining = loss_limit - daily_loss
            approval_summary.append(f"✅ Daily Loss Limit: ${remaining:.2f} remaining (${daily_loss:.2f}/${loss_limit:.2f})")
        
        if risk_config.min_risk_reward_ratio and hasattr(signal, 'recommendation'):
            rec = signal.recommendation
            if rec and 'risk_reward' in rec:
                try:
                    rr = float(rec['risk_reward'])
                    approval_summary.append(f"✅ Risk/Reward: {rr:.2f}:1 >= {risk_config.min_risk_reward_ratio}:1")
                except:
                    pass
        
        if risk_config.max_leverage and hasattr(signal, 'recommendation'):
            rec = signal.recommendation
            if rec and 'leverage' in rec:
                leverage = int(rec.get('leverage', 0))
                if leverage <= risk_config.max_leverage:
                    approval_summary.append(f"✅ Leverage: {leverage}x <= {risk_config.max_leverage}x")
                else:
                    approval_summary.append(f"⚠️ Leverage: Adjusted {leverage}x → {risk_config.max_leverage}x")
        
        logger.info("\n📊 APPROVAL SUMMARY:")
        for item in approval_summary:
            logger.info(f"   {item}")
        
        reason = f"All checks passed: {len(approval_summary)} validations completed"
        logger.info(f"\n💡 Reason: {reason}")
        logger.info("=" * 80)
        
        return True, reason, signal
        
    except Exception as e:
        logger.error(f"❌ Error in risk management: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # On error, allow trade to proceed (fail-open for safety)
        return True, f"Risk management error (fail-open): {e}", signal


async def run_advanced_futures_workflow(bot, subscription_id: int, subscription_config: dict, db):
    """
    Advanced multi-timeframe futures trading workflow
    Applies MAIN_EXECUTION() advanced features to CELERY execution
    """
    try:
        from datetime import datetime
        from core import crud, models
        trade_result = None
        logger.info(f"🎯 Starting ADVANCED FUTURES WORKFLOW for subscription {subscription_id}")
        
        # Get subscription for risk management
        subscription = crud.get_subscription_by_id(db, subscription_id)
        if not subscription:
            logger.error(f"Subscription {subscription_id} not found")
            from bots.bot_sdk.Action import Action
            return Action(action="HOLD", value=0.0, reason="Subscription not found"), None, None
        
        # 0. MULTI-PAIR PRIORITY LOGIC: Find first available trading pair without OPEN position
        logger.info("=" * 80)
        logger.info("🎯 Step 0: MULTI-PAIR TRADING - Finding available trading pair...")
        logger.info("=" * 80)
        
        # Build list of trading pairs in priority order: [primary, secondary1, secondary2, ...]
        primary_pair = subscription_config.get('trading_pair') or subscription.trading_pair
        secondary_pairs = subscription.secondary_trading_pairs or []
        
        # Ensure secondary_pairs is a list
        if isinstance(secondary_pairs, str):
            import json
            try:
                secondary_pairs = json.loads(secondary_pairs)
            except:
                secondary_pairs = []
        
        all_trading_pairs = [primary_pair] + (secondary_pairs if secondary_pairs else [])
        
        logger.info(f"📋 Trading Pairs Priority List:")
        logger.info(f"   1️⃣ Primary: {primary_pair}")
        if secondary_pairs:
            for idx, pair in enumerate(secondary_pairs, start=2):
                logger.info(f"   {idx}️⃣ Secondary: {pair}")
        else:
            logger.info(f"   ℹ️  No secondary pairs configured")
        logger.info(f"   📊 Total pairs to check: {len(all_trading_pairs)}")
        
        # Find first available pair (no OPEN position)
        selected_trading_pair = None
        
        for idx, trading_pair in enumerate(all_trading_pairs, start=1):
            # Normalize trading pair: Remove '/' for DB query (BTC/USDT -> BTCUSDT)
            trading_pair_normalized = trading_pair.replace('/', '') if trading_pair else trading_pair
            
            logger.info(f"\n🔍 Checking pair {idx}/{len(all_trading_pairs)}: {trading_pair} (DB: {trading_pair_normalized})")
            
            # Use SELECT FOR UPDATE to prevent race conditions
            open_positions = db.query(models.Transaction).filter(
                models.Transaction.subscription_id == subscription_id,
                models.Transaction.symbol == trading_pair_normalized,
                models.Transaction.status == 'OPEN'
            ).with_for_update().all()
            
            if open_positions:
                logger.info(f"   ⏭️  SKIP: {len(open_positions)} OPEN position(s) found")
                for pos in open_positions:
                    logger.info(f"      - Position #{pos.id}: {pos.action} {pos.quantity} @ ${pos.entry_price}, P&L: ${pos.unrealized_pnl:.2f}")
                # Continue to next pair
                continue
            else:
                # Found available pair!
                selected_trading_pair = trading_pair
                logger.info(f"   ✅ AVAILABLE: No OPEN positions")
                logger.info(f"   🎯 SELECTED for trading: {trading_pair}")
                break
        
        # Check if all pairs have OPEN positions
        if selected_trading_pair is None:
            logger.warning("\n" + "=" * 80)
            logger.warning("⏸️  ALL TRADING PAIRS HAVE OPEN POSITIONS")
            logger.warning("=" * 80)
            logger.warning(f"   Checked {len(all_trading_pairs)} pair(s): {', '.join(all_trading_pairs)}")
            logger.warning(f"   All pairs currently have active positions")
            logger.warning(f"   💡 Will trade again when any position is CLOSED")
            logger.warning("=" * 80)
            db.commit()  # Release lock
            from bots.bot_sdk.Action import Action
            return Action(action="HOLD", value=0.0, reason=f"All {len(all_trading_pairs)} trading pairs have OPEN positions"), None, None
        
        # Update subscription_config with selected pair
        subscription_config['trading_pair'] = selected_trading_pair
        bot.trading_pair = selected_trading_pair.replace('/', '')  # Update bot instance
        
        db.commit()  # Release lock before proceeding
        logger.info("\n" + "=" * 80)
        logger.info(f"🎯 SELECTED TRADING PAIR: {selected_trading_pair}")
        logger.info("=" * 80)
        logger.info(f"   Priority: {all_trading_pairs.index(selected_trading_pair) + 1} of {len(all_trading_pairs)}")
        logger.info(f"   Proceeding with LLM analysis for {selected_trading_pair}...")
        logger.info("=" * 80)
        
        # 1. Check account status (like main_execution) - Skip for SIGNALS_FUTURES
        logger.info("💰 Step 1: Checking account status...")
        
        # SIGNALS_FUTURES bots don't need account status (signals-only, no trading)
        bot_type_str = str(subscription.bot.bot_type).upper() if subscription.bot.bot_type else None
        if bot_type_str == "SIGNALS_FUTURES":
            logger.info("📡 SIGNALS_FUTURES bot - Skip account check (signals-only, no trading)")
            account_status = None
        else:
            # Active trading bots need account balance check
            account_status = bot.check_account_status()
            if account_status:
                logger.info(f"Account Balance: ${account_status.get('available_balance', 0):.2f}")
        
        # 2. Crawl multi-timeframe data (instead of single timeframe)
        logger.info("📊 Step 2: Crawling multi-timeframe data...")
        multi_timeframe_data = bot.crawl_data()
        if not multi_timeframe_data.get("timeframes"):
            logger.error("❌ Failed to crawl multi-timeframe data")
            from bots.bot_sdk.Action import Action
            return Action(action="HOLD", value=0.0, reason="Multi-timeframe data crawl failed"), account_status, None
        
        timeframes_crawled = list(multi_timeframe_data['timeframes'].keys())
        logger.info(f"✅ Crawled {len(timeframes_crawled)} timeframes: {timeframes_crawled}")
        
        # 3. Analyze all timeframes (instead of single timeframe)
        logger.info("🔍 Step 3: Analyzing multi-timeframe data...")
        analysis = bot.analyze_data(multi_timeframe_data)
        if 'error' in analysis:
            logger.error(f"❌ Multi-timeframe analysis error: {analysis['error']}")
            from bots.bot_sdk.Action import Action
            return Action(action="HOLD", value=0.0, reason=f"Multi-timeframe analysis failed: {analysis['error']}"), account_status, None

        analyzed_timeframes = len(analysis.get('multi_timeframe', {}))
        primary_timeframe = analysis.get('primary_timeframe', 'unknown')
        logger.info(f"✅ Analyzed {analyzed_timeframes} timeframes, primary: {primary_timeframe}")
        
        # 4. Generate signal with multi-timeframe confirmation (instead of basic signal)
        logger.info("🎯 Step 4: Generating advanced multi-timeframe signal...")
        signal = bot.generate_signal(analysis)
        
        logger.info(f"📊 ADVANCED SIGNAL: {signal.action} | Confidence: {signal.value*100:.1f}% | Reason: {signal.reason}")
        
        # Log advanced signal details
        if hasattr(signal, 'recommendation') and signal.recommendation:
            rec = signal.recommendation
            logger.info(f"🎯 LLM Recommendation Details:")
            logger.info(f"   Strategy: {rec.get('action', 'N/A')}")
            logger.info(f"   Strategy: {rec.get('strategy', 'N/A')}")
            logger.info(f"   Entry Price: {rec.get('entry_price', 'Market')}")
            # Handle take_profit array
            tp = rec.get('take_profit', 'N/A')
            if isinstance(tp, list) and len(tp) > 0:
                logger.info(f"   Take Profit Levels:")
                for tp_level in tp:
                    level = tp_level.get('level', 'TP')
                    price = tp_level.get('price', '?')
                    size_pct = tp_level.get('size_pct', 0)
                    logger.info(f"     {level}: ${price} ({size_pct}% position)")
            else:
                logger.info(f"   Take Profit: {tp}")
            logger.info(f"   Stop Loss: {rec.get('stop_loss', 'N/A')}")
            logger.info(f"   Risk/Reward: {rec.get('risk_reward', 'N/A')}")

        if signal.action != "HOLD":
            # 4.5. Apply Risk Management (NEW)
            logger.info("🛡️ Step 4.5: Applying Risk Management rules...")
            risk_approved, risk_reason, adjusted_signal = apply_risk_management(
                subscription, signal, analysis, account_status, db
            )

            if not risk_approved:
                logger.warning("=" * 80)
                logger.warning(f"🚫 TRADE REJECTED BY RISK MANAGEMENT")
                logger.warning(f"   Reason: {risk_reason}")
                logger.warning("=" * 80)
                from bots.bot_sdk.Action import Action
                return Action(action="HOLD", value=0.0, reason=f"Risk Management: {risk_reason}"), account_status, None

            logger.info("=" * 80)
            logger.info(f"✅ TRADE APPROVED BY RISK MANAGEMENT")
            logger.info(f"   Details: {risk_reason}")
            logger.info("=" * 80)
            signal = adjusted_signal  # Use adjusted signal (e.g., leverage may be capped)

            # 5. Execute advanced position setup (if not HOLD)
            logger.info(f"🚀 Step 5: Executing ADVANCED POSITION SETUP for {signal.action}...")
            logger.info("🤖 AUTO-CONFIRMED via Celery (no user confirmation required)")
            
            # Use advanced setup_position with capital management, stop loss, take profit
            trade_result = await bot.setup_position(signal, analysis, subscription)
            
            if trade_result.get('status') == 'success':
                logger.info(f"✅ Advanced trade executed successfully!")
                logger.info(f"   Order ID: {trade_result.get('main_order_id')}")
                logger.info(f"   Position Value: ${trade_result.get('position_value', 0):.2f}")
                logger.info(f"   Leverage: {trade_result.get('leverage', 'N/A')}x")
                logger.info(f"   Stop Loss Order: {trade_result.get('stop_loss', {}).get('order_id', 'N/A')}")
                logger.info(f"   Take Profit Order: {trade_result.get('take_profit', {}).get('order_id', 'N/A')}")
                
                # Save transaction to database (like main_execution)
                bot.save_transaction_to_db(trade_result)
                logger.info("💾 Transaction saved to database")
                
                # Update risk tracking: Reset consecutive losses on successful trade
                try:
                    logger.info("\n" + "=" * 80)
                    logger.info("📊 RISK TRACKING UPDATE: Trade Success")
                    logger.info("=" * 80)
                    logger.info(f"  Previous Consecutive Losses: {subscription.consecutive_losses or 0}")
                    subscription.consecutive_losses = 0
                    db.commit()
                    logger.info(f"  New Consecutive Losses: 0 (RESET)")
                    logger.info("  ✅ Consecutive losses counter reset due to successful trade")
                    logger.info("=" * 80)
                except Exception as e:
                    logger.error(f"❌ Failed to update risk tracking: {e}")
                    
            else:
                logger.error(f"❌ Advanced trade execution failed: {trade_result}")
                
                # Update risk tracking: Increment consecutive losses
                try:
                    logger.info("\n" + "=" * 80)
                    logger.info("📊 RISK TRACKING UPDATE: Trade Failed")
                    logger.info("=" * 80)
                    prev_losses = subscription.consecutive_losses or 0
                    subscription.consecutive_losses = prev_losses + 1
                    logger.info(f"  Previous Consecutive Losses: {prev_losses}")
                    logger.info(f"  New Consecutive Losses: {subscription.consecutive_losses}")
                    
                    # Check if cooldown should be triggered
                    risk_config_dict = subscription.risk_config or subscription.bot.risk_config
                    if risk_config_dict:
                        from core import schemas
                        from datetime import timedelta
                        risk_config = schemas.RiskConfig(**risk_config_dict)
                        
                        if risk_config.cooldown and risk_config.cooldown.enabled:
                            logger.info(f"\n  🔍 Cooldown Check:")
                            logger.info(f"     Trigger Threshold: {risk_config.cooldown.trigger_loss_count} losses")
                            logger.info(f"     Current Losses: {subscription.consecutive_losses}")
                            
                            if subscription.consecutive_losses >= risk_config.cooldown.trigger_loss_count:
                                cooldown_until = datetime.utcnow() + timedelta(minutes=risk_config.cooldown.cooldown_minutes)
                                subscription.cooldown_until = cooldown_until
                                logger.warning(f"\n  🚫 COOLDOWN TRIGGERED!")
                                logger.warning(f"     Reason: {subscription.consecutive_losses} consecutive losses >= {risk_config.cooldown.trigger_loss_count}")
                                logger.warning(f"     Duration: {risk_config.cooldown.cooldown_minutes} minutes")
                                logger.warning(f"     Paused Until: {cooldown_until}")
                            else:
                                remaining = risk_config.cooldown.trigger_loss_count - subscription.consecutive_losses
                                logger.info(f"     ✅ No cooldown yet ({remaining} more losses until cooldown)")
                    
                    db.commit()
                    logger.info(f"\n  ✅ Risk tracking updated successfully")
                    logger.info("=" * 80)
                except Exception as e:
                    logger.error(f"❌ Failed to update risk tracking: {e}")
        else:
            logger.info("📊 Signal is HOLD - no position setup needed")
        
        # Return the signal (for compatibility with existing workflow)
        logger.info(f"🎉 ADVANCED FUTURES WORKFLOW completed successfully")
        return signal, account_status, trade_result
        
    except Exception as e:
        logger.error(f"❌ Error in advanced futures workflow: {e}")
        import traceback
        logger.error(traceback.format_exc())
        from bots.bot_sdk.Action import Action
        return Action(action="HOLD", value=0.0, reason=f"Advanced workflow error: {e}"), None, None

async def run_advanced_futures_rpa_workflow(bot, subscription_id: int, subscription_config: Dict[str, Any], db):
    """
    Advanced multi-timeframe futures trading workflow với RPA
    """
    try:
        from bots.bot_sdk.Action import Action
        from core import crud, models
        logger.info(f"🎯 Starting ADVANCED FUTURES RPA WORKFLOW for subscription {subscription_id}")
        trade_result = None
        
        # Get subscription for risk management
        subscription = crud.get_subscription_by_id(db, subscription_id)
        if not subscription:
            logger.error(f"Subscription {subscription_id} not found")
            return Action(action="HOLD", value=0.0, reason="Subscription not found"), None, None
        
        # 0. MULTI-PAIR PRIORITY LOGIC: Find first available trading pair without OPEN position
        logger.info("=" * 80)
        logger.info("🎯 Step 0: MULTI-PAIR TRADING (RPA) - Finding available trading pair...")
        logger.info("=" * 80)
        
        # Build list of trading pairs in priority order: [primary, secondary1, secondary2, ...]
        primary_pair = subscription_config.get('trading_pair') or subscription.trading_pair
        secondary_pairs = subscription.secondary_trading_pairs or []
        
        # Ensure secondary_pairs is a list
        if isinstance(secondary_pairs, str):
            import json
            try:
                secondary_pairs = json.loads(secondary_pairs)
            except:
                secondary_pairs = []
        
        all_trading_pairs = [primary_pair] + (secondary_pairs if secondary_pairs else [])
        
        logger.info(f"📋 Trading Pairs Priority List:")
        logger.info(f"   1️⃣ Primary: {primary_pair}")
        if secondary_pairs:
            for idx, pair in enumerate(secondary_pairs, start=2):
                logger.info(f"   {idx}️⃣ Secondary: {pair}")
        else:
            logger.info(f"   ℹ️  No secondary pairs configured")
        logger.info(f"   📊 Total pairs to check: {len(all_trading_pairs)}")
        
        # Find first available pair (no OPEN position)
        selected_trading_pair = None
        
        for idx, trading_pair in enumerate(all_trading_pairs, start=1):
            # Normalize trading pair: Remove '/' for DB query (BTC/USDT -> BTCUSDT)
            trading_pair_normalized = trading_pair.replace('/', '') if trading_pair else trading_pair
            
            logger.info(f"\n🔍 Checking pair {idx}/{len(all_trading_pairs)}: {trading_pair} (DB: {trading_pair_normalized})")
            
            # Use SELECT FOR UPDATE to prevent race conditions
            open_positions = db.query(models.Transaction).filter(
                models.Transaction.subscription_id == subscription_id,
                models.Transaction.symbol == trading_pair_normalized,
                models.Transaction.status == 'OPEN'
            ).with_for_update().all()
            
            if open_positions:
                logger.info(f"   ⏭️  SKIP: {len(open_positions)} OPEN position(s) found")
                for pos in open_positions:
                    logger.info(f"      - Position #{pos.id}: {pos.action} {pos.quantity} @ ${pos.entry_price}, P&L: ${pos.unrealized_pnl:.2f}")
                # Continue to next pair
                continue
            else:
                # Found available pair!
                selected_trading_pair = trading_pair
                logger.info(f"   ✅ AVAILABLE: No OPEN positions")
                logger.info(f"   🎯 SELECTED for RPA trading: {trading_pair}")
                break
        
        # Check if all pairs have OPEN positions
        if selected_trading_pair is None:
            logger.warning("\n" + "=" * 80)
            logger.warning("⏸️  ALL TRADING PAIRS HAVE OPEN POSITIONS (RPA)")
            logger.warning("=" * 80)
            logger.warning(f"   Checked {len(all_trading_pairs)} pair(s): {', '.join(all_trading_pairs)}")
            logger.warning(f"   All pairs currently have active positions")
            logger.warning(f"   💡 Will trade again when any position is CLOSED")
            logger.warning("=" * 80)
            db.commit()  # Release lock
            return Action(action="HOLD", value=0.0, reason=f"All {len(all_trading_pairs)} trading pairs have OPEN positions"), None, None
        
        # Update subscription_config with selected pair
        subscription_config['trading_pair'] = selected_trading_pair
        bot.trading_pair = selected_trading_pair.replace('/', '_')  # RPA uses underscore format
        
        db.commit()  # Release lock before proceeding
        logger.info("\n" + "=" * 80)
        logger.info(f"🎯 SELECTED TRADING PAIR (RPA): {selected_trading_pair}")
        logger.info("=" * 80)
        logger.info(f"   Priority: {all_trading_pairs.index(selected_trading_pair) + 1} of {len(all_trading_pairs)}")
        logger.info(f"   Proceeding with RPA + LLM analysis for {selected_trading_pair}...")
        logger.info("=" * 80)
        
        # 1. Check account status - Skip for SIGNALS_FUTURES
        logger.info("💰 Step 1: Checking account status...")
        
        # SIGNALS_FUTURES bots don't need account status (signals-only, no trading)
        bot_type_str = str(subscription.bot.bot_type).upper() if subscription.bot.bot_type else None
        if bot_type_str == "SIGNALS_FUTURES":
            logger.info("📡 SIGNALS_FUTURES bot - Skip account check (signals-only, no trading)")
            account_status = None
        else:
            # Active trading bots need account balance check
            account_status = bot.check_account_status()
            if account_status:
                logger.info(f"Account Balance: ${account_status.get('available_balance', 0):.2f}")
        
        # 2. Capture multi-timeframe data using RPA
        logger.info("📊 Step 2: Capturing multi-timeframe data with RPA...")
        image_paths = bot.capture_chart_data()
        if not image_paths:
            logger.error("❌ Failed to capture multi-timeframe data with RPA")
            return Action(action="HOLD", value=0.0, reason="RPA data capture failed"), account_status, None

        # 3. Analyze images with LLM
        logger.info("🔍 Step 3: Analyzing multi-timeframe data with LLM...")
        action = await bot.analyze_images_with_llm(image_paths)
        logger.info(f"🎯 RPA LLM Analysis Result: {action}")
        
        # Log LLM analysis result
        try:
            from utils.execution_logger import ExecutionLogger
            bot_id = config.get('bot_id', 1)
            subscription_id = config.get('subscription_id')
            execution_logger = ExecutionLogger(bot_id, subscription_id, self.request.id)
            execution_logger.analysis(
                f"LLM Analysis: {action.action} signal with {action.value*100:.1f}% confidence",
                {
                    'action': action.action,
                    'confidence': action.value,
                    'reason': action.reason,
                    'signal_strength': action.value
                }
            )
        except Exception as e:
            logger.error(f"❌ Failed to log LLM analysis: {e}")
        
        if action.action == "HOLD":
            logger.info("📊 Signal is HOLD - no position setup needed")
            return action, account_status, None

        logger.info(f"📊 ADVANCED RPA SIGNAL: {action.action} | Confidence: {action.value*100:.1f}%")
        
        # 4. Execute advanced position setup
        logger.info(f"🚀 Step 4: Executing ADVANCED POSITION SETUP for {action.action}...")
        # trade_result = await bot.setup_position(action)

        if hasattr(action, 'recommendation') and action.recommendation:
            rec = action.recommendation
            logger.info(f"🎯 LLM Recommendation Details:")
            logger.info(f"   Strategy: {rec.get('action', 'N/A')}")
            logger.info(f"   Strategy: {rec.get('strategy', 'N/A')}")
            logger.info(f"   Entry Price: {rec.get('entry_price', 'Market')}")
            # Handle take_profit array
            tp = rec.get('take_profit', 'N/A')
            if isinstance(tp, list) and len(tp) > 0:
                logger.info(f"   Take Profit Levels:")
                for tp_level in tp:
                    level = tp_level.get('level', 'TP')
                    price = tp_level.get('price', '?')
                    size_pct = tp_level.get('size_pct', 0)
                    logger.info(f"     {level}: ${price} ({size_pct}% position)")
            else:
                logger.info(f"   Take Profit: {tp}")
            logger.info(f"   Stop Loss: {rec.get('stop_loss', 'N/A')}")
            logger.info(f"   Risk/Reward: {rec.get('risk_reward', 'N/A')}")
        
        # 4.5. Apply Risk Management (NEW)
        logger.info("🛡️ Step 4.5: Applying Risk Management rules...")
        risk_approved, risk_reason, adjusted_action = apply_risk_management(
            subscription, action, {}, account_status, db
        )
        
        if not risk_approved:
            logger.warning(f"🚫 Trade rejected by Risk Management: {risk_reason}")
            return Action(action="HOLD", value=0.0, reason=f"Risk Management: {risk_reason}"), account_status, None
        
        logger.info(f"✅ Risk Management approved: {risk_reason}")
        action = adjusted_action  # Use adjusted action
        
        # 5. Execute advanced position setup (if not HOLD)
        if action.action != "HOLD":
            logger.info(f"🚀 Step 5: Executing ADVANCED POSITION SETUP for {action.action}...")
            logger.info("🤖 AUTO-CONFIRMED via Celery (no user confirmation required)")
            
            # Use advanced setup_position with capital management, stop loss, take profit
            trade_result = await bot.setup_position(action, None, subscription)
            
            if trade_result.get('status') == 'success':
                logger.info(f"✅ Advanced trade executed successfully!")
                logger.info(f"   Order ID: {trade_result.get('main_order_id')}")
                logger.info(f"   Position Value: ${trade_result.get('position_value', 0):.2f}")
                logger.info(f"   Leverage: {trade_result.get('leverage', 'N/A')}x")
                logger.info(f"   Stop Loss Order: {trade_result.get('stop_loss', {}).get('order_ids', 'N/A')}")
                logger.info(f"   Take Profit Order: {trade_result.get('take_profit', {}).get('order_ids', 'N/A')}")
                
                # Save transaction to database (like main_execution)
                bot.save_transaction_to_db(trade_result)
                logger.info("💾 Transaction saved to database")
                
                # Update risk tracking: Reset consecutive losses on successful trade
                try:
                    logger.info("\n" + "=" * 80)
                    logger.info("📊 RISK TRACKING UPDATE: Trade Success")
                    logger.info("=" * 80)
                    logger.info(f"  Previous Consecutive Losses: {subscription.consecutive_losses or 0}")
                    subscription.consecutive_losses = 0
                    db.commit()
                    logger.info(f"  New Consecutive Losses: 0 (RESET)")
                    logger.info("  ✅ Consecutive losses counter reset due to successful trade")
                    logger.info("=" * 80)
                except Exception as e:
                    logger.error(f"❌ Failed to update risk tracking: {e}")
                
                # Log execution to database
                try:
                    from utils.execution_logger import ExecutionLogger
                    bot_id = config.get('bot_id', 1)
                    subscription_id = config.get('subscription_id')
                    execution_logger = ExecutionLogger(bot_id, subscription_id, self.request.id)
                    
                    # Log successful trade execution
                    execution_logger.transaction(
                        f"Trade executed: {action} {trade_result.get('quantity', 0)} {trade_result.get('symbol', 'N/A')} at ${trade_result.get('entry_price', 0)}",
                        {
                            'action': action,
                            'symbol': trade_result.get('symbol'),
                            'quantity': trade_result.get('quantity'),
                            'entry_price': trade_result.get('entry_price'),
                            'leverage': trade_result.get('leverage'),
                            'order_id': trade_result.get('main_order_id'),
                            'confidence': trade_result.get('confidence'),
                            'position_value': trade_result.get('position_value')
                        }
                    )
                    logger.info("📝 Execution logged to database")
                except Exception as e:
                    logger.error(f"❌ Failed to log execution: {e}")
            else:
                logger.error(f"❌ Advanced trade execution failed: {trade_result}")
                
                # Update risk tracking: Increment consecutive losses
                try:
                    from datetime import datetime, timedelta
                    logger.info("\n" + "=" * 80)
                    logger.info("📊 RISK TRACKING UPDATE: Trade Failed (RPA)")
                    logger.info("=" * 80)
                    prev_losses = subscription.consecutive_losses or 0
                    subscription.consecutive_losses = prev_losses + 1
                    logger.info(f"  Previous Consecutive Losses: {prev_losses}")
                    logger.info(f"  New Consecutive Losses: {subscription.consecutive_losses}")
                    
                    # Check if cooldown should be triggered
                    risk_config_dict = subscription.risk_config or subscription.bot.risk_config
                    if risk_config_dict:
                        from core import schemas
                        risk_config = schemas.RiskConfig(**risk_config_dict)
                        
                        if risk_config.cooldown and risk_config.cooldown.enabled:
                            logger.info(f"\n  🔍 Cooldown Check:")
                            logger.info(f"     Trigger Threshold: {risk_config.cooldown.trigger_loss_count} losses")
                            logger.info(f"     Current Losses: {subscription.consecutive_losses}")
                            
                            if subscription.consecutive_losses >= risk_config.cooldown.trigger_loss_count:
                                cooldown_until = datetime.utcnow() + timedelta(minutes=risk_config.cooldown.cooldown_minutes)
                                subscription.cooldown_until = cooldown_until
                                logger.warning(f"\n  🚫 COOLDOWN TRIGGERED!")
                                logger.warning(f"     Reason: {subscription.consecutive_losses} consecutive losses >= {risk_config.cooldown.trigger_loss_count}")
                                logger.warning(f"     Duration: {risk_config.cooldown.cooldown_minutes} minutes")
                                logger.warning(f"     Paused Until: {cooldown_until}")
                            else:
                                remaining = risk_config.cooldown.trigger_loss_count - subscription.consecutive_losses
                                logger.info(f"     ✅ No cooldown yet ({remaining} more losses until cooldown)")
                    
                    db.commit()
                    logger.info(f"\n  ✅ Risk tracking updated successfully")
                    logger.info("=" * 80)
                except Exception as e:
                    logger.error(f"❌ Failed to update risk tracking: {e}")
                
                # Log failed execution
                try:
                    from utils.execution_logger import ExecutionLogger
                    bot_id = config.get('bot_id', 1)
                    subscription_id = config.get('subscription_id')
                    execution_logger = ExecutionLogger(bot_id, subscription_id, self.request.id)
                    execution_logger.error(
                        f"Trade execution failed: {trade_result.get('error', 'Unknown error')}",
                        {'error': trade_result}
                    )
                except Exception as e:
                    logger.error(f"❌ Failed to log error: {e}")
        else:
            logger.info("📊 Signal is HOLD - no position setup needed")
            # Log hold signal
            try:
                from utils.execution_logger import ExecutionLogger
                bot_id = config.get('bot_id', 1)
                subscription_id = config.get('subscription_id')
                execution_logger = ExecutionLogger(bot_id, subscription_id, self.request.id)
                execution_logger.system(
                    "Signal is HOLD - no position setup needed",
                    {'signal': 'HOLD', 'action': action}
                )
            except Exception as e:
                logger.error(f"❌ Failed to log hold signal: {e}")
        
        logger.info(f"🎉 ADVANCED FUTURES RPA WORKFLOW completed successfully")
        return action, account_status, trade_result
        
    except Exception as e:
        logger.error(f"❌ Error in advanced futures RPA workflow: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Log error to database
        try:
            from utils.execution_logger import ExecutionLogger
            bot_id = config.get('bot_id', 1) if config else 1
            subscription_id = config.get('subscription_id') if config else None
            execution_logger = ExecutionLogger(bot_id, subscription_id, self.request.id)
            execution_logger.error(
                f"Advanced futures RPA workflow error: {str(e)}",
                {
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'workflow': 'advanced_futures_rpa'
                }
            )
        except Exception as log_error:
            logger.error(f"❌ Failed to log error: {log_error}")
        
        return Action(action="HOLD", value=0.0, reason=f"Advanced RPA workflow error: {e}"), None, None

@app.task(bind=True, max_retries=3)
def create_subscription_from_paypal_task(self, payment_id: str):
    """Celery task to create subscription from PayPal payment"""
    try:
        from core.database import SessionLocal
        from core import crud, models
        
        # Get fresh database session
        db = SessionLocal()
        
        try:
            # Get payment details
            payment = crud.get_paypal_payment(db, payment_id)
            if not payment:
                logger.error(f"PayPal payment {payment_id} not found for subscription creation")
                return
            
            if payment.status != models.PayPalPaymentStatus.COMPLETED:
                logger.error(f"PayPal payment {payment_id} not completed (status: {payment.status})")
                return
            
            # Check if subscription already exists
            existing_subscription = db.query(models.Subscription).filter(
                models.Subscription.user_principal_id == payment.user_principal_id,
                models.Subscription.bot_id == payment.bot_id,
                models.Subscription.status == models.SubscriptionStatus.ACTIVE
            ).first()
            
            if existing_subscription:
                logger.info(f"Active subscription already exists for user {payment.user_principal_id}, bot {payment.bot_id}")
                return existing_subscription.id
            
            # Get bot details  
            bot = crud.get_bot_by_id(db, payment.bot_id)
            if not bot:
                logger.error(f"Bot {payment.bot_id} not found for subscription creation")
                return
            
            # Calculate subscription dates
            now = datetime.utcnow()
            expires_at = now + timedelta(days=payment.duration_days)
            
            # Create subscription
            subscription_data = {
                "user_principal_id": payment.user_principal_id,
                "bot_id": payment.bot_id,
                "status": models.SubscriptionStatus.ACTIVE,
                "pricing_plan_id": None,  # PayPal doesn't use pricing plans
                "started_at": now,
                "expires_at": expires_at,
                "is_marketplace_subscription": True,
                "trading_pair": "BTCUSDT",  # Default trading pair
                "timeframes": ["1h"],  # Default timeframe
                "instance_name": f"paypal_{payment.id}_{int(now.timestamp())}",  # Required field
                "marketplace_user_email": payment.payer_email,
                "marketplace_subscription_start": now,
                "marketplace_subscription_end": expires_at
            }
            
            subscription = models.Subscription(**subscription_data)
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            logger.info(f"Created subscription {subscription.id} from PayPal payment {payment_id}")
            
            # Schedule bot execution
            try:
                run_bot_logic.apply_async(args=[subscription.id], countdown=30)
                logger.info(f"Scheduled bot execution for subscription {subscription.id}")
            except Exception as e:
                logger.warning(f"Failed to schedule bot execution for subscription {subscription.id}: {e}")
            
            return subscription.id
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to create subscription from PayPal payment {payment_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(countdown=60 * (2 ** self.request.retries))

@app.task(bind=True, max_retries=3)
def sync_payment_to_studio_task(self, payment_id: str):
    """Celery task to sync PayPal payment to Studio subscription API"""
    try:
        from core.database import SessionLocal
        from services.paypal_service import get_paypal_service
        
        # Get fresh database session
        db = SessionLocal()
        
        try:
            paypal_service = get_paypal_service(db)
            result = paypal_service.sync_subscription_to_studio(payment_id)
            
            if result["status"] == "success":
                logger.info(f"Studio sync successful for payment {payment_id}")
                return result
            elif result["status"] == "skipped":
                logger.info(f"Studio sync skipped for payment {payment_id}: {result['reason']}")
                return result
            else:
                logger.error(f"Studio sync failed for payment {payment_id}: {result}")
                raise Exception(f"Studio sync failed: {result.get('error', 'Unknown error')}")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to sync payment {payment_id} to Studio: {e}")
        # Retry with exponential backoff
        raise self.retry(countdown=60 * (2 ** self.request.retries))


# ============================================================================
# POSITION MONITORING & PERFORMANCE TRACKING TASKS
# ============================================================================

@app.task(bind=True)
def monitor_open_positions_task(self):
    """
    Celery task to monitor all open positions
    - Check TP/SL hit
    - Update unrealized P&L
    - Close positions when needed
    
    Schedule: Run every 1-5 minutes
    """
    try:
        from core.database import SessionLocal
        from services.position_monitor import PositionMonitor
        from binance.client import Client
        import os
        
        logger.info("📊 Starting position monitoring task...")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Initialize Binance client (use mainnet for monitoring)
            api_key = os.getenv('BINANCE_MAINNET_API_KEY')
            api_secret = os.getenv('BINANCE_MAINNET_API_SECRET')
            
            if not api_key or not api_secret:
                logger.warning("No Binance mainnet credentials, skipping monitoring")
                return {"status": "skipped", "reason": "No mainnet credentials"}
            
            futures_client = Client(api_key, api_secret)
            
            # Run monitoring
            monitor = PositionMonitor(db, futures_client)
            results = monitor.monitor_open_positions()
            
            logger.info(f"✅ Position monitoring complete: {results}")
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Position monitoring task failed: {e}")
        logger.error(traceback.format_exc())
        # Retry with backoff
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


@app.task(bind=True)
def update_bot_performance_metrics(self, bot_id: int):
    """
    Calculate and update performance metrics for a bot
    - Win rate
    - Average P&L
    - Risk-reward achievement
    - Total trades
    
    Triggered when a position closes
    """
    try:
        from core.database import SessionLocal
        from core import models
        from sqlalchemy import func
        
        logger.info(f"📈 Calculating performance metrics for bot {bot_id}...")
        
        db = SessionLocal()
        
        try:
            # Get all closed transactions for this bot
            transactions = db.query(models.Transaction).filter(
                models.Transaction.bot_id == bot_id,
                models.Transaction.status == 'CLOSED'
            ).all()
            
            if not transactions:
                logger.info(f"No closed transactions for bot {bot_id}")
                return {"status": "no_data"}
            
            # Calculate metrics
            total_trades = len(transactions)
            winning_trades = len([t for t in transactions if t.is_winning])
            losing_trades = total_trades - winning_trades
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            total_pnl = sum([float(t.pnl_usd or 0) for t in transactions])
            avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
            
            avg_win = sum([float(t.pnl_usd or 0) for t in transactions if t.is_winning]) / winning_trades if winning_trades > 0 else 0
            avg_loss = sum([float(t.pnl_usd or 0) for t in transactions if not t.is_winning]) / losing_trades if losing_trades > 0 else 0
            
            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else 0
            
            # Update bot metadata with performance stats
            bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
            if bot:
                # Store in bot_metadata JSON
                # SQLAlchemy JSON field: Need to copy, modify, reassign
                from sqlalchemy.orm.attributes import flag_modified
                
                metadata_dict = dict(bot.bot_metadata) if bot.bot_metadata else {}
                metadata_dict['performance'] = {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': round(win_rate, 2),
                    'total_pnl': round(total_pnl, 2),
                    'avg_pnl': round(avg_pnl, 2),
                    'avg_win': round(avg_win, 2),
                    'avg_loss': round(avg_loss, 2),
                    'profit_factor': round(profit_factor, 2),
                    'last_updated': datetime.now().isoformat()
                }
                bot.bot_metadata = metadata_dict
                flag_modified(bot, 'bot_metadata')
                
                db.commit()
            
            metrics = {
                'bot_id': bot_id,
                'total_trades': total_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'profit_factor': round(profit_factor, 2)
            }
            
            logger.info(f"✅ Bot {bot_id} performance updated: {metrics}")
            return metrics
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Failed to update bot performance for {bot_id}: {e}")
        logger.error(traceback.format_exc())
        raise self.retry(exc=e, countdown=60)


@app.task(bind=True)
def update_prompt_performance_metrics(self, prompt_id: int):
    """
    Calculate and update performance metrics for a prompt template
    - Win rate across all bots using this prompt
    - Average P&L
    - Total trades
    
    Triggered when a position closes
    """
    try:
        from core.database import SessionLocal
        from core import models
        
        logger.info(f"📈 Calculating performance metrics for prompt {prompt_id}...")
        
        db = SessionLocal()
        
        try:
            # Get all closed transactions using this prompt
            transactions = db.query(models.Transaction).filter(
                models.Transaction.prompt_id == prompt_id,
                models.Transaction.status == 'CLOSED'
            ).all()
            
            if not transactions:
                logger.info(f"No closed transactions for prompt {prompt_id}")
                return {"status": "no_data"}
            
            # Calculate metrics
            total_trades = len(transactions)
            winning_trades = len([t for t in transactions if t.is_winning])
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            total_pnl = sum([float(t.pnl_usd or 0) for t in transactions])
            avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
            
            # Update prompt usage stats
            usage_stat = db.query(models.PromptUsageStats).filter(
                models.PromptUsageStats.prompt_id == prompt_id
            ).first()
            
            if usage_stat:
                usage_stat.success_count = winning_trades
                usage_stat.total_uses = total_trades
                usage_stat.updated_at = datetime.now()
                db.commit()
            
            metrics = {
                'prompt_id': prompt_id,
                'total_trades': total_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_pnl': round(avg_pnl, 2)
            }
            
            logger.info(f"✅ Prompt {prompt_id} performance updated: {metrics}")
            return metrics
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Failed to update prompt performance for {prompt_id}: {e}")
        logger.error(traceback.format_exc())
        raise self.retry(exc=e, countdown=60)


@app.task(bind=True)
def update_risk_management_performance(self, bot_id: int):
    """
    Analyze risk management effectiveness for a bot
    - TP hit rate vs SL hit rate
    - Average RR achievement
    - Slippage analysis
    
    Triggered when a position closes
    """
    try:
        from core.database import SessionLocal
        from core import models
        
        logger.info(f"📊 Analyzing risk management for bot {bot_id}...")
        
        db = SessionLocal()
        
        try:
            # Get all closed transactions
            transactions = db.query(models.Transaction).filter(
                models.Transaction.bot_id == bot_id,
                models.Transaction.status == 'CLOSED'
            ).all()
            
            if not transactions:
                return {"status": "no_data"}
            
            # Analyze exit reasons
            tp_hits = len([t for t in transactions if t.exit_reason == 'TP_HIT'])
            sl_hits = len([t for t in transactions if t.exit_reason == 'SL_HIT'])
            manual_exits = len([t for t in transactions if t.exit_reason == 'MANUAL'])
            
            # Calculate RR achievement
            avg_planned_rr = sum([float(t.risk_reward_ratio or 0) for t in transactions]) / len(transactions)
            avg_actual_rr = sum([float(t.actual_rr_ratio or 0) for t in transactions]) / len(transactions)
            
            rr_achievement_rate = (avg_actual_rr / avg_planned_rr * 100) if avg_planned_rr > 0 else 0
            
            # Analyze slippage
            transactions_with_slippage = [t for t in transactions if t.slippage]
            avg_slippage = sum([float(t.slippage) for t in transactions_with_slippage]) / len(transactions_with_slippage) if transactions_with_slippage else 0
            
            risk_metrics = {
                'bot_id': bot_id,
                'total_trades': len(transactions),
                'tp_hit_rate': round(tp_hits / len(transactions) * 100, 2),
                'sl_hit_rate': round(sl_hits / len(transactions) * 100, 2),
                'manual_exit_rate': round(manual_exits / len(transactions) * 100, 2),
                'avg_planned_rr': round(avg_planned_rr, 2),
                'avg_actual_rr': round(avg_actual_rr, 2),
                'rr_achievement_rate': round(rr_achievement_rate, 2),
                'avg_slippage': round(avg_slippage, 4)
            }
            
            logger.info(f"✅ Risk management analysis for bot {bot_id}: {risk_metrics}")
            return risk_metrics
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Failed to analyze risk management for {bot_id}: {e}")
        logger.error(traceback.format_exc())
        raise self.retry(exc=e, countdown=60)


@app.task(bind=True)
def sync_open_positions_realtime(self):
    """
    Real-time position sync task
    - Fetches position status from exchange APIs
    - Updates transactions with real-time data
    - Auto-detects closed positions
    - Updates P&L, prices, exit info
    
    Features:
    - Multi-exchange support (Bybit, Binance, OKX, Bitget, Huobi, Kraken)
    - Real-time unrealized P&L calculation
    - Auto-close detection
    - Configurable interval (default: 100s)
    
    Schedule: Run every 100 seconds (configurable in beat_schedule)
    """
    try:
        from core.database import SessionLocal
        from services.position_sync_service import PositionSyncService
        
        logger.info("🔄 Starting real-time position sync...")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Initialize sync service
            sync_service = PositionSyncService(db)
            
            # Sync all open positions
            results = sync_service.sync_all_open_positions()
            
            # Log summary
            if results["total"] > 0:
                logger.info(f"✅ Position sync complete:")
                logger.info(f"   📊 Total: {results['total']}")
                logger.info(f"   ✅ Updated: {results['updated']}")
                logger.info(f"   🔒 Closed: {results['closed']}")
                if results['errors'] > 0:
                    logger.warning(f"   ❌ Errors: {results['errors']}")
            else:
                logger.debug("No open positions to sync")
            
            return results
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Position sync task failed: {e}")
        logger.error(traceback.format_exc())
        # Retry with backoff (30 seconds)
        raise self.retry(exc=e, countdown=30)
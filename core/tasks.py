def format_notification_message(bot_name, balance_info, action, reason, current_price=None, available=None, total_wallet=None):
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
        f"Action: {action}\n"
        f"Reason: {reason}"
    )
    return msg
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

# Helper to push DM to Redis queue
def queue_discord_dm(user_id, message):
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'active-trading-redis-1'), port=int(os.getenv('REDIS_PORT', 6379)), db=0)
    payload = {'user_id': user_id, 'message': message}
    r.rpush('discord_dm_queue', json.dumps(payload))
def initialize_bot(subscription):
    """Initialize bot from subscription - Load from S3"""
    try:
        # Import here to avoid circular imports
        from core import models
        from core import schemas
        from core.database import SessionLocal
        from services.s3_manager import S3Manager
        from core.bot_base_classes import get_base_classes
        
        # Initialize S3 manager
        s3_manager = S3Manager()
        
        # Get bot information
        bot_id = subscription.bot.id
        logger.info(f"Initializing bot {bot_id} from S3...")
        
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
        import tempfile
        import os
        
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
                bot_config = {
                    'trading_pair': subscription.bot.trading_pair.replace('/', ''),
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
                    
                    # Celery execution
                    'require_confirmation': False,  # No confirmation for Celery
                    'auto_confirm': True  # Auto-confirm trades (for Celery/automated execution)
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
            if subscription.bot.strategy_config:
                logger.info(f"🎯 Merging DATABASE STRATEGY CONFIG: {subscription.bot.strategy_config}")
                bot_config.update(subscription.bot.strategy_config)

            # Prepare subscription context for bot (includes principal ID)
            subscription_context = {
                'subscription_id': subscription.id,
                'user_principal_id': subscription.user_principal_id,
                'exchange': subscription.bot.exchange_type.value if subscription.bot.exchange_type else 'binance',
                'trading_pair': subscription.bot.trading_pair.replace('/', ''),
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
            if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type and subscription.bot.bot_type.upper() == 'FUTURES':
                try:
                    logger.info(f"Attempting FUTURES BOT direct initialization...")
                    # Import BinanceFuturesBot directly for futures bots
                    import sys
                    import os
                    bot_files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_files')
                    if bot_files_path not in sys.path:
                        sys.path.insert(0, bot_files_path)
                    
                    from binance_futures_bot import BinanceFuturesBot
                    bot_instance = BinanceFuturesBot(bot_config, api_keys, subscription.user_principal_id)
                    init_success = True
                    logger.info(f"✅ FUTURES BOT initialized successfully with principal ID")
                except Exception as e:
                    logger.warning(f"FUTURES BOT direct init failed: {e}")
            
            # Method 2: Try downloaded bot with 3 arguments (config, api_keys, principal_id)
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
# def initialize_bot(subscription):
#     """Initialize bot from subscription - Load from S3"""
#     try:
#         # Import here to avoid circular imports
#         from core import models
#         from core import schemas
#         from core.database import SessionLocal
#         from services.s3_manager import S3Manager
#         from core.bot_base_classes import get_base_classes
        

#         # Get bot information
#         bot_id = subscription.bot.id
#         logger.info(f"Initializing bot {bot_id} from local bot_files...")

#         # Lấy đường dẫn code_path từ subscription.bot.code_path
#         code_path = getattr(subscription.bot, 'code_path', None)
#         if not code_path:
#             logger.error(f"No code_path found for bot {bot_id}")
#             return None

#         # Đọc code từ file local
#         try:
#             with open(code_path, 'r', encoding='utf-8') as f:
#                 code_content = f.read()
#             logger.info(f"Read bot code from {code_path}: {len(code_content)} characters")
#         except Exception as e:
#             logger.error(f"Failed to read bot code from {code_path}: {e}")
#             return None

#         # Load base classes from bot_sdk folder
#         base_classes = get_base_classes()

#         # Combine base classes with downloaded bot code
#         full_code = base_classes + "\n" + code_content

#         import tempfile
#         with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
#             f.write(full_code)
#             temp_file_path = f.name
        
#         try:
#             # Load bot module from temporary file
#             spec = importlib.util.spec_from_file_location("bot_module", temp_file_path)
#             if not spec or not spec.loader:
#                 logger.error("Could not create module spec")
#                 return None
            
#             bot_module = importlib.util.module_from_spec(spec)
#             spec.loader.exec_module(bot_module)
            
#             # Find bot class in the module
#             bot_class = None
#             for attr_name in dir(bot_module):
#                 attr = getattr(bot_module, attr_name)
#                 if (inspect.isclass(attr) and 
#                     hasattr(attr, 'execute_algorithm') and 
#                     attr_name != 'CustomBot'):
#                     bot_class = attr
#                     break
            
#             if not bot_class:
#                 logger.error("No valid bot class found in module")
#                 return None
            
#             # Prepare bot configuration - Rich config for Futures bots
#             if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type and subscription.bot.bot_type.upper() == 'FUTURES':
#                 # Rich configuration for Futures bots (like main_execution)
#                 bot_config = {
#                     'trading_pair': subscription.bot.trading_pair.replace('/', ''),
#                     'testnet': subscription.is_testnet if subscription.is_testnet else True,
#                     'leverage': 5,
#                     'stop_loss_pct': 0.02,  # 2%
#                     'take_profit_pct': 0.04,  # 4%
#                     'position_size_pct': 0.1,  # 10% of balance
                    
#                     # 🎯 Optimized 3 timeframes for better performance
#                     'timeframes': subscription.bot.timeframes,
#                     'primary_timeframe': subscription.bot.timeframe,  # Primary timeframe for final decision
                    
#                     'use_llm_analysis': True,  # Enable LLM analysis with full system
#                     'llm_model': 'openai',  # Primary LLM model to use
                    
#                     # Technical indicators (fallback when LLM fails)
#                     'rsi_period': 14,
#                     'rsi_oversold': 30,     # Buy signal threshold
#                     'rsi_overbought': 70,   # Sell signal threshold
                    
#                     # Capital management (CRITICAL for risk control)
#                     'base_position_size_pct': 0.02,    # 2% minimum position
#                     'max_position_size_pct': 0.10,     # 10% maximum position  
#                     'max_portfolio_exposure': 0.30,    # 30% total exposure limit
#                     'max_drawdown_threshold': 0.15,    # 15% stop-loss threshold
                    
#                     # Celery execution
#                     'require_confirmation': False,  # No confirmation for Celery
#                     'auto_confirm': True  # Auto-confirm trades (for Celery/automated execution)
#                 }
#                 logger.info(f"🚀 Applied RICH FUTURES CONFIG: {len(bot_config['timeframes'])} timeframes, {bot_config['leverage']}x leverage")
#             else:
#                 # Standard configuration for other bots
#                 bot_config = {
#                     'short_window': 50,
#                     'long_window': 200,
#                     'position_size': 0.3,
#                     'min_volume_threshold': 1000000,
#                     'volatility_threshold': 0.05
#                 }
#                 logger.info("📊 Applied STANDARD CONFIG for non-futures bot")
            
#             # Override with subscription strategy_config if available (from database)
#             if subscription.bot.strategy_config:
#                 logger.info(f"🎯 Merging DATABASE STRATEGY CONFIG: {subscription.bot.strategy_config}")
#                 bot_config.update(subscription.bot.strategy_config)

#             # Prepare subscription context for bot (includes principal ID)
#             subscription_context = {
#                 'subscription_id': subscription.id,
#                 'user_principal_id': subscription.user_principal_id,
#                 'exchange': subscription.bot.exchange_type.value if subscription.bot.exchange_type else 'binance',
#                 'trading_pair': subscription.bot.trading_pair.replace('/', ''),
#                 'timeframe': subscription.bot.timeframe,
#                 'is_testnet': subscription.is_testnet if subscription.is_testnet else True,
#                 'is_marketplace_subscription': getattr(subscription, 'is_marketplace_subscription', False)
#             }
            
#             # Try multiple initialization approaches for compatibility
#             bot_instance = None
#             init_success = False
            
#             # Create api_keys dict for backward compatibility
#             api_keys = {
#                 'exchange': subscription_context['exchange'],
#                 'testnet': subscription_context['is_testnet']
#             }
            
#             # Method 1: Try BinanceFuturesBot direct initialization (for Futures bots)
#             if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type and subscription.bot.bot_type.upper() == 'FUTURES':
#                 try:
#                     logger.info(f"Attempting FUTURES BOT direct initialization...")
#                     # Import BinanceFuturesBot directly for futures bots
#                     import sys
#                     import os
#                     bot_files_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot_files')
#                     if bot_files_path not in sys.path:
#                         sys.path.insert(0, bot_files_path)
                    
#                     from binance_futures_bot import BinanceFuturesBot
#                     bot_instance = BinanceFuturesBot(bot_config, api_keys, subscription.user_principal_id)
#                     init_success = True
#                     logger.info(f"✅ FUTURES BOT initialized successfully with principal ID")
#                 except Exception as e:
#                     logger.warning(f"FUTURES BOT direct init failed: {e}")
            
#             # Method 2: Try downloaded bot with 3 arguments (config, api_keys, principal_id)
#             if not init_success:
#                 try:
#                     bot_instance = bot_class(bot_config, api_keys, subscription.user_principal_id)
#                     init_success = True
#                     logger.info(f"✅ Downloaded bot initialized with 3 args: {bot_class.__name__}")
#                 except TypeError as e:
#                     logger.warning(f"3-arg constructor failed: {e}")
            
#             # Method 3: Try downloaded bot with 2 arguments (config, api_keys)
#             if not init_success:
#                 try:
#                     bot_instance = bot_class(bot_config, api_keys)
#                     init_success = True
#                     logger.info(f"✅ Downloaded bot initialized with 2 args: {bot_class.__name__}")
#                 except TypeError as e:
#                     logger.warning(f"2-arg constructor failed: {e}")
            
#             # Method 4: Try downloaded bot with 1 argument (config)
#             if not init_success:
#                 try:
#                     bot_instance = bot_class(bot_config)
#                     init_success = True
#                     logger.info(f"✅ Downloaded bot initialized with 1 arg: {bot_class.__name__}")
#                 except TypeError as e:
#                     logger.warning(f"1-arg constructor failed: {e}")
            
#             # Method 5: Try downloaded bot with no arguments
#             if not init_success:
#                 try:
#                     bot_instance = bot_class()
#                     init_success = True
#                     logger.info(f"✅ Downloaded bot initialized with no args: {bot_class.__name__}")
#                 except Exception as e:
#                     logger.error(f"No-arg constructor failed: {e}")
            
#             # If initialization succeeded, manually inject context for non-futures bots
#             if init_success and bot_instance:
#                 # Manually inject subscription context for downloaded bots
#                 if hasattr(bot_instance, 'user_principal_id'):
#                     bot_instance.user_principal_id = subscription_context['user_principal_id']
#                 if hasattr(bot_instance, 'subscription_id'):
#                     bot_instance.subscription_id = subscription_context['subscription_id']
#                 if hasattr(bot_instance, 'trading_pair'):
#                     bot_instance.trading_pair = subscription_context['trading_pair']
#                 if hasattr(bot_instance, 'timeframe'):
#                     bot_instance.timeframe = subscription_context['timeframe']
#                 if hasattr(bot_instance, 'is_testnet'):
#                     bot_instance.is_testnet = subscription_context['is_testnet']
                
#                 # Set config manually if the bot has attributes for it
#                 if hasattr(bot_instance, 'short_window'):
#                     bot_instance.short_window = bot_config.get('short_window', 50)
#                 if hasattr(bot_instance, 'long_window'):
#                     bot_instance.long_window = bot_config.get('long_window', 200)
#                 if hasattr(bot_instance, 'position_size'):
#                     bot_instance.position_size = bot_config.get('position_size', 0.3)
                
#                 logger.info(f"Context injected - Principal ID: {subscription_context['user_principal_id']}")
#             else:
#                 logger.error(f"All bot initialization methods failed")
#                 return None
            
#             return bot_instance
            
#         finally:
#             # Clean up temporary file
#             try:
#                 os.unlink(temp_file_path)
#             except:
#                 pass
        
#     except Exception as e:
#         logger.error(f"Error initializing bot: {e}")
#         logger.error(traceback.format_exc())
#         return None

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
                from core.api_key_manager import APIKeyManager
                api_key_manager = APIKeyManager()
                creds = api_key_manager.get_user_credentials_by_principal_id(
                    db=db,
                    user_principal_id=subscription.user_principal_id,
                    exchange=exchange_type.value,
                    is_testnet=use_testnet
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

            logger.info(f"Creating exchange client for subscription {subscription_id} (testnet={use_testnet})")
            
            exchange = ExchangeFactory.create_exchange(
                exchange_name=exchange_type.value,
                api_key=api_key,
                api_secret=api_secret,
                testnet=use_testnet
            )
            
            # Get current market data
            trading_pair = subscription.bot.trading_pair or 'BTC/USDT'
            exchange_symbol = trading_pair.replace('/', '')
            try:
                ticker = exchange.get_ticker(exchange_symbol)
                current_price = float(ticker['price'])
            except Exception as e:
                logger.error(f"Failed to get ticker for {trading_pair}: {e}")
                crud.log_bot_action(
                    db, subscription_id, "ERROR", 
                    f"Failed to get ticker for {trading_pair}: {str(e)}"
                )
                return

            # Set bot's exchange client
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
            if hasattr(subscription.bot, 'bot_type') and subscription.bot.bot_type and subscription.bot.bot_type.upper() == 'FUTURES':
                logger.info(f"🚀 Using ADVANCED FUTURES WORKFLOW for {subscription.bot.name}")
                # Run async workflow in event loop
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    final_action, account_status = loop.run_until_complete(
                        run_advanced_futures_workflow(bot, subscription_id, subscription_config, db)
                    )
                finally:
                    loop.close()
            else:
                logger.info(f"📊 Using STANDARD WORKFLOW for {subscription.bot.name}")
                final_action = bot.execute_full_cycle(subscription.timeframe, subscription_config)
                
            if final_action:
                logger.info(f"Bot {subscription.bot.name} executed with action: {final_action.action}, value: {final_action.value}, reason: {final_action.reason}")
                
                # Log action to database
                crud.log_bot_action(
                    db, subscription_id, final_action.action,
                    f"{final_action.reason}. Value: {final_action.value or 0.0}. Price: ${current_price}"
                )
                
            # Get balance info for BUY/SELL actions (real API call)
                balance_info = ""
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
                trade_result = False
                trade_details = None
                
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
                                if tp is not None:
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
                            total_wallet=account_status.get('total_balance', 0)
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

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in run_bot_logic for subscription {subscription_id}: {e}")
        logger.error(traceback.format_exc())
        
        # Try to log error to database
        try:
            from core.database import SessionLocal
            from core import crud
            db = SessionLocal()
            crud.log_bot_action(
                db, subscription_id, "ERROR",
                f"Bot execution failed: {str(e)}"
            )
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
        from services.image_analysis import analyze_image_with_openai
        from core.schemas import PayLoadBotRun
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

                    bot_config = PayLoadBotRun(
                        trading_pair=subscription.bot.trading_pair,
                        timeframe=subscription.bot.timeframes,
                        strategies=subscription.bot.strategy_config,
                        # custom_prompt=subscription.risk_config
                    )

                    response = analyze_image_with_openai(image_paths, bot_config)
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
                    if telegram_chat_id:
                        send_telegram_beauty_notification.delay(telegram_chat_id, final_response)
                    if discord_user_id:
                        send_discord_notification.delay(discord_user_id, final_response)
                except Exception as e:
                    logger.error(f"🚨 EXCEPTION in scheduled_bot_task: {e}")
                    sys.stdout.flush()
                    import traceback
                    logger.error(f"🚨 TRACEBACK: {traceback.format_exc()}")
                    sys.stdout.flush()
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
                    
                    if subscription.bot.bot_mode != "PASSIVE":
                        run_bot_logic.delay(subscription.id)
                        # Queue the bot execution task      
                    else:
                        # Handle PASSIVE bots
                        run_bot_signal_logic.delay(subscription.bot.id, subscription.id)

                    # Update next run time based on timeframe
                    if subscription.bot.timeframe == "1m":
                        next_run = datetime.utcnow() + timedelta(minutes=1)
                    elif subscription.bot.timeframe == "5m":
                        next_run = datetime.utcnow() + timedelta(minutes=5)
                    elif subscription.bot.timeframe == "15m":
                        next_run = datetime.utcnow() + timedelta(minutes=15)
                    elif subscription.bot.timeframe == "1h":
                        next_run = datetime.utcnow() + timedelta(hours=1)
                    elif subscription.bot.timeframe == "4h":
                        next_run = datetime.utcnow() + timedelta(hours=4)
                    elif subscription.bot.timeframe == "1d":
                        next_run = datetime.utcnow() + timedelta(days=1)
                    else:
                        next_run = datetime.utcnow() + timedelta(hours=1)  # Default to 1 hour
                    
                    crud.update_subscription_next_run(db, subscription.id, next_run)
                    logger.info(f"Updated next_run_at for subscription {subscription.id} to {next_run}")
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

# @app.task
# def send_telegram_notification(chat_id: str | int, text: str):
#     try:
#         from services.telegram_service import TelegramService
#         telegram_service = TelegramService()
#     except Exception as e:
#         logger.error(f"Error sending email notification: {e}")

    
# @app.task
# def send_discord_notification():
#     return
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
            'auto_confirm': True  # Enable auto-confirmation
        }
        
        # Merge with provided config
        if config:
            default_config.update(config)
            
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
                    trade_result = await bot.setup_position(signal, analysis)
                    
                    # Save transaction if successful
                    if trade_result.get('status') == 'success':
                        bot.save_transaction_to_db(trade_result)
                        logger.info(f"✅ Trade executed and saved: {trade_result.get('main_order_id')}")
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

async def run_advanced_futures_workflow(bot, subscription_id: int, subscription_config: dict, db):
    """
    Advanced multi-timeframe futures trading workflow
    Applies MAIN_EXECUTION() advanced features to CELERY execution
    """
    try:
        from datetime import datetime
        
        logger.info(f"🎯 Starting ADVANCED FUTURES WORKFLOW for subscription {subscription_id}")
        
        # 1. Check account status (like main_execution)
        logger.info("💰 Step 1: Checking account status...")
        account_status = bot.check_account_status()
        if account_status:
            logger.info(f"Account Balance: ${account_status.get('available_balance', 0):.2f}")
        
        # 2. Crawl multi-timeframe data (instead of single timeframe)
        logger.info("📊 Step 2: Crawling multi-timeframe data...")
        multi_timeframe_data = bot.crawl_data()
        if not multi_timeframe_data.get("timeframes"):
            logger.error("❌ Failed to crawl multi-timeframe data")
            from bots.bot_sdk.Action import Action
            return Action(action="HOLD", value=0.0, reason="Multi-timeframe data crawl failed")
        
        timeframes_crawled = list(multi_timeframe_data['timeframes'].keys())
        logger.info(f"✅ Crawled {len(timeframes_crawled)} timeframes: {timeframes_crawled}")
        
        # 3. Analyze all timeframes (instead of single timeframe)
        logger.info("🔍 Step 3: Analyzing multi-timeframe data...")
        analysis = bot.analyze_data(multi_timeframe_data)
        if 'error' in analysis:
            logger.error(f"❌ Multi-timeframe analysis error: {analysis['error']}")
            from bots.bot_sdk.Action import Action
            return Action(action="HOLD", value=0.0, reason=f"Multi-timeframe analysis failed: {analysis['error']}")
        
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
            logger.info(f"   Take Profit: {rec.get('take_profit', 'N/A')}")
            logger.info(f"   Stop Loss: {rec.get('stop_loss', 'N/A')}")
            logger.info(f"   Risk/Reward: {rec.get('risk_reward', 'N/A')}")
        
        # 5. Execute advanced position setup (if not HOLD)
        if signal.action != "HOLD":
            logger.info(f"🚀 Step 5: Executing ADVANCED POSITION SETUP for {signal.action}...")
            logger.info("🤖 AUTO-CONFIRMED via Celery (no user confirmation required)")
            
            # Use advanced setup_position with capital management, stop loss, take profit
            trade_result = await bot.setup_position(signal, analysis)
            
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
            else:
                logger.error(f"❌ Advanced trade execution failed: {trade_result}")
        else:
            logger.info("📊 Signal is HOLD - no position setup needed")
        
        # Return the signal (for compatibility with existing workflow)
        logger.info(f"🎉 ADVANCED FUTURES WORKFLOW completed successfully")
        return signal, account_status
        
    except Exception as e:
        logger.error(f"❌ Error in advanced futures workflow: {e}")
        import traceback
        logger.error(traceback.format_exc())
        from bots.bot_sdk.Action import Action
        return Action(action="HOLD", value=0.0, reason=f"Advanced workflow error: {e}")

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
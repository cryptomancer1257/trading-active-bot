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

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.celery_app import app
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                    'trading_pair': 'BTCUSDT',
                    'testnet': True,
                    'leverage': 5,
                    'stop_loss_pct': 0.02,  # 2%
                    'take_profit_pct': 0.04,  # 4%
                    'position_size_pct': 0.1,  # 10% of balance
                    
                    # 🎯 Dynamic 5 timeframes - Bạn có thể thay đổi tùy ý!
                    'timeframes': ['5m', '30m', '1h', '4h', '1d'],  
                    'primary_timeframe': '1h',  # Primary timeframe for final decision
                    
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
            if subscription.strategy_config:
                logger.info(f"🎯 Merging DATABASE STRATEGY CONFIG: {subscription.strategy_config}")
                bot_config.update(subscription.strategy_config)
            
            # Prepare subscription context for bot (includes principal ID)
            subscription_context = {
                'subscription_id': subscription.id,
                'user_principal_id': subscription.user_principal_id,
                'exchange': subscription.exchange_type.value if subscription.exchange_type else 'binance',
                'trading_pair': subscription.trading_pair,
                'timeframe': subscription.timeframe,
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

def execute_trade_action(db, subscription, exchange, action, current_price):
    """Execute trade action"""
    try:
        from core import crud
        
        # Get trading pair
        trading_pair = subscription.trading_pair or 'BTC/USDT'
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
            
            # Check if we have enough base currency
            if sell_quantity > base_total:
                logger.warning(f"Insufficient {base_asset} balance for sell order")
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
    Main task to run bot logic
    """
    try:
        # Import here to avoid circular imports
        from core import models
        from core import schemas
        from core import crud
        from core.database import SessionLocal
        from services.exchange_factory import ExchangeFactory
        
        db = SessionLocal()
        
        try:
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
            exchange_type = subscription.exchange_type or schemas.ExchangeType.BINANCE
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
            trading_pair = subscription.trading_pair or 'BTC/USDT'
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
                'timeframe': subscription.timeframe,
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
                    final_action = loop.run_until_complete(
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
                        base_asset = trading_pair.split('/')[0]  # BTC from BTC/USDT
                        quote_asset = trading_pair.split('/')[1]  # USDT from BTC/USDT
                        
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
                    user_email = subscription.user.email if subscription.user_id else subscription.marketplace_user_email
                    
                    send_combined_notification(
                        user_email,
                        subscription.bot.name,
                        final_action.action,
                        {
                            'trading_pair': trading_pair,
                            'current_price': current_price,
                            'reason': final_action.reason,
                            'confidence': final_action.value or 'N/A',
                            'timeframe': subscription.timeframe,
                            'is_testnet': bool(subscription.is_testnet),
                            'balance_info': balance_info,
                            'subscription_id': subscription_id,
                            'trade_details': trade_details
                        }
                    )
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
                    
                    # Queue the bot execution task
                    run_bot_logic.delay(subscription.id)
                    
                    # Update next run time based on timeframe
                    if subscription.timeframe == "1m":
                        next_run = datetime.utcnow() + timedelta(minutes=1)
                    elif subscription.timeframe == "5m":
                        next_run = datetime.utcnow() + timedelta(minutes=5)
                    elif subscription.timeframe == "15m":
                        next_run = datetime.utcnow() + timedelta(minutes=15)
                    elif subscription.timeframe == "1h":
                        next_run = datetime.utcnow() + timedelta(hours=1)
                    elif subscription.timeframe == "4h":
                        next_run = datetime.utcnow() + timedelta(hours=4)
                    elif subscription.timeframe == "1d":
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
            'timeframes': ['5m', '30m', '1h', '4h', '1d'],
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
        return signal
        
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
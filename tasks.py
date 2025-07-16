import logging
import traceback
import time
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import importlib.util
import inspect
import os
import tempfile
import asyncio

from celery import Celery
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
celery_app = Celery(
    'bot_marketplace',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        'tasks.run_bot_logic': {'queue': 'bot_execution'},
        'tasks.cleanup_old_logs': {'queue': 'maintenance'},
    },
    task_default_retry_delay=60,
    task_max_retries=3,
    beat_schedule={
        'cleanup-old-logs': {
            'task': 'tasks.cleanup_old_logs',
            'schedule': 300.0,  # Run every 5 minutes
        },
    },
)

def initialize_bot_from_s3(subscription):
    """Initialize bot from S3 storage"""
    try:
        # Import here to avoid circular imports
        import crud
        
        bot = subscription.bot
        
        # Get bot version from subscription metadata or use bot's current version
        bot_version = None
        if subscription.metadata:
            bot_version = subscription.metadata.get('bot_version')
        if not bot_version:
            bot_version = bot.version
        
        # Load bot from S3
        bot_instance = crud.load_bot_from_s3(
            bot_id=bot.id,
            version=bot_version,
            user_config=subscription.strategy_config or {},
            user_api_keys={
                'key': subscription.user.api_key,
                'secret': subscription.user.api_secret
            }
        )
        
        if not bot_instance:
            logger.error(f"Failed to load bot {bot.id} from S3")
            return None
            
        logger.info(f"Successfully loaded bot {bot.id} from S3 (version: {bot_version})")
        return bot_instance
        
    except Exception as e:
        logger.error(f"Error initializing bot from S3: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def initialize_bot(subscription):
    """Initialize bot - first try S3, then fallback to local"""
    try:
        # First try to load from S3
        bot_instance = initialize_bot_from_s3(subscription)
        if bot_instance:
            return bot_instance
            
        # Fallback to local file loading for backward compatibility
        logger.warning(f"S3 loading failed for bot {subscription.bot.id}, trying local file")
        
        # Import here to avoid circular imports
        from bots.bot_sdk import CustomBot
        
        bot = subscription.bot
        
        if not bot.code_path or not os.path.exists(bot.code_path):
            logger.error(f"Bot code file not found: {bot.code_path}")
            return None
        
        # Load bot code dynamically
        spec = importlib.util.spec_from_file_location("bot_module", bot.code_path)
        if spec and spec.loader:
            bot_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bot_module)
            
            # Find the bot class in the module
            bot_class = None
            for name in dir(bot_module):
                obj = getattr(bot_module, name)
                if (isinstance(obj, type) and 
                    issubclass(obj, CustomBot) and 
                    obj != CustomBot):
                    bot_class = obj
                    break
            
            if not bot_class:
                logger.error("No bot class found in the uploaded file")
                return None
            
            # Initialize bot with configuration
            bot_config = {}
            if bot.default_config:
                bot_config.update(bot.default_config)
            if subscription.strategy_config:
                bot_config.update(subscription.strategy_config)
            
            user_api_keys = {
                'key': subscription.user.api_key,
                'secret': subscription.user.api_secret
            }
            
            bot_instance = bot_class(bot_config, user_api_keys)
            return bot_instance
        else:
            logger.error(f"Failed to load spec for {bot.code_path}")
            return None
        
    except Exception as e:
        logger.error(f"Error initializing bot: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def execute_trade_action(db: Session, subscription: models.Subscription, exchange, action: Action, current_price: float):
    """
    Execute trade action based on Action object
    
    Args:
        db: Database session
        subscription: Subscription object
        exchange: Exchange client
        action: Action object with type and value
        current_price: Current market price
    """
    try:
        symbol = subscription.symbol.replace('/', '')  # BTCUSDT format
        user_id = subscription.user_id
        
        # Get current balance
        base_asset = symbol.replace('USDT', '')  # BTC
        quote_asset = 'USDT'
        
        base_balance = exchange.get_balance(base_asset)
        quote_balance = exchange.get_balance(quote_asset)
        
        base_free = float(base_balance.free)
        quote_free = float(quote_balance.free)
        
        logger.info(f"Current balance: {base_free} {base_asset}, {quote_free} {quote_asset}")
        
        # Calculate quantity based on action type
        if action.action == "BUY":
            if action.type == "PERCENTAGE":
                # Buy with percentage of USDT balance
                usdt_amount = quote_free * action.value
                quantity_str, calc_info = exchange.calculate_quantity(symbol, "BUY", usdt_amount, current_price)
                
                logger.info(f"BUY calculation: {action.value*100}% of {quote_free} USDT = {usdt_amount} USDT")
                logger.info(f"Quantity to buy: {quantity_str} {base_asset} at ${current_price}")
                
                # Execute buy order
                order = exchange.create_market_order(symbol, "BUY", quantity_str)
                
                # Log successful trade
                crud.log_bot_action(
                    db, subscription.id, "BUY",
                    f"Bought {quantity_str} {base_asset} at ${current_price} (${usdt_amount:.2f} USDT). Order ID: {order.order_id}"
                )
                
                # Send email notification
                if hasattr(subscription, 'user') and subscription.user.email:
                    try:
                        from email_tasks import send_trade_notification
                        send_trade_notification.delay(
                            subscription.user.email,
                            {
                                "side": "BUY",
                                "symbol": subscription.symbol,
                                "quantity": quantity_str,
                                "price": str(current_price),
                                "type": "MARKET",
                                "order_id": order.order_id,
                                "timestamp": datetime.utcnow().isoformat(),
                                "is_testnet": getattr(subscription, 'is_testnet', True),
                                "reason": action.reason
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to send trade email: {e}")
                
            elif action.type == "USDT_AMOUNT":
                # Buy with specific USDT amount
                usdt_amount = action.value
                quantity_str, calc_info = exchange.calculate_quantity(symbol, "BUY", usdt_amount, current_price)
                
                order = exchange.create_market_order(symbol, "BUY", quantity_str)
                
                crud.log_bot_action(
                    db, subscription.id, "BUY",
                    f"Bought {quantity_str} {base_asset} with {usdt_amount} USDT at ${current_price}. Order ID: {order.order_id}"
                )
            
            elif action.type == "QUANTITY":
                # Buy specific quantity
                quantity_str = f"{action.value:.8f}".rstrip('0').rstrip('.')
                
                order = exchange.create_market_order(symbol, "BUY", quantity_str)
                
                crud.log_bot_action(
                    db, subscription.id, "BUY", 
                    f"Bought {quantity_str} {base_asset} at ${current_price}. Order ID: {order.order_id}"
                )
        
        elif action.action == "SELL":
            if action.type == "PERCENTAGE":
                # Sell percentage of BTC holdings
                sell_quantity = base_free * action.value
                quantity_str, calc_info = exchange.calculate_quantity(symbol, "SELL", sell_quantity, current_price)
                
                logger.info(f"SELL calculation: {action.value*100}% of {base_free} {base_asset} = {sell_quantity} {base_asset}")
                logger.info(f"Quantity to sell: {quantity_str} {base_asset} at ${current_price}")
                
                # Execute sell order
                order = exchange.create_market_order(symbol, "SELL", quantity_str)
                
                # Calculate profit/loss
                usdt_received = float(quantity_str) * current_price
                
                # Log successful trade
                crud.log_bot_action(
                    db, subscription.id, "SELL",
                    f"Sold {quantity_str} {base_asset} at ${current_price} (${usdt_received:.2f} USDT). Order ID: {order.order_id}"
                )
                
                # Send email notification
                if hasattr(subscription, 'user') and subscription.user.email:
                    try:
                        from email_tasks import send_trade_notification
                        send_trade_notification.delay(
                            subscription.user.email,
                            {
                                "side": "SELL",
                                "symbol": subscription.symbol,
                                "quantity": quantity_str,
                                "price": str(current_price),
                                "type": "MARKET",
                                "order_id": order.order_id,
                                "timestamp": datetime.utcnow().isoformat(),
                                "is_testnet": getattr(subscription, 'is_testnet', True),
                                "reason": action.reason,
                                "pnl": f"+{usdt_received:.2f}"
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to send trade email: {e}")
                
            elif action.type == "USDT_AMOUNT":
                # Sell to get specific USDT amount
                sell_quantity = action.value / current_price
                quantity_str, calc_info = exchange.calculate_quantity(symbol, "SELL", sell_quantity, current_price)
                
                order = exchange.create_market_order(symbol, "SELL", quantity_str)
                
                crud.log_bot_action(
                    db, subscription.id, "SELL",
                    f"Sold {quantity_str} {base_asset} to get {action.value} USDT at ${current_price}. Order ID: {order.order_id}"
                )
                
            elif action.type == "QUANTITY":
                # Sell specific quantity
                quantity_str = f"{action.value:.8f}".rstrip('0').rstrip('.')
                
                order = exchange.create_market_order(symbol, "SELL", quantity_str)
                
                crud.log_bot_action(
                    db, subscription.id, "SELL",
                    f"Sold {quantity_str} {base_asset} at ${current_price}. Order ID: {order.order_id}"
                )
        
        logger.info(f"Trade executed successfully: {action.action} {action.value} {action.type}")
        
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        crud.log_bot_action(
            db, subscription.id, "ERROR",
            f"Trade execution failed: {action.action} {action.value} {action.type}. Error: {str(e)}"
        )
        raise

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def run_bot_logic(self, subscription_id: int):
    """
    Main task to run bot logic
    This task will be called periodically for each active subscription
    """
    db = SessionLocal()
    
    try:
        # Get subscription
        subscription = crud.get_subscription_by_id(db, subscription_id)
        if not subscription:
            logger.error(f"Subscription {subscription_id} not found")
            return

        # Skip if subscription is not active
        if subscription.status != schemas.SubscriptionStatus.ACTIVE:
            logger.info(f"Subscription {subscription_id} is not active, skipping")
            return

        # Initialize bot
        bot = initialize_bot(subscription)
        if not bot:
            logger.error(f"Failed to initialize bot for subscription {subscription_id}")
            # Mark subscription as error
            crud.update_subscription_status(db, subscription_id, schemas.SubscriptionStatus.ERROR)
            return

        # Create exchange client
        exchange_type = subscription.exchange_type or schemas.ExchangeType.BINANCE
        
        # Use testnet for trial subscriptions or if explicitly configured
        use_testnet = getattr(subscription, 'is_testnet', True)
        
        # Extra safety: always use testnet for trial subscriptions
        if getattr(subscription, 'is_trial', False):
            use_testnet = True
        
        logger.info(f"Creating exchange client for subscription {subscription_id} (testnet={use_testnet})")
        
        exchange = ExchangeFactory.create_exchange(
            exchange_name=exchange_type.value,
            api_key=subscription.user.api_key,
            api_secret=subscription.user.api_secret,
            testnet=use_testnet
        )
        
        # Get current market data
        symbol = subscription.symbol
        try:
            ticker = exchange.get_ticker(symbol)
            current_price = float(ticker['price'])
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            # Log the error but don't fail completely
            crud.log_bot_action(
                db, subscription_id, "ERROR", 
                f"Failed to get ticker for {symbol}: {str(e)}"
            )
            return

        # Run bot logic
        try:
            # Use execute_full_cycle instead of analyze_market for proper data handling
            # This will crawl real market data, preprocess it, and run the algorithm
            
            # Convert strategy_config to dict if it's a database column
            strategy_config = {}
            if subscription.strategy_config:
                if isinstance(subscription.strategy_config, dict):
                    strategy_config = subscription.strategy_config
                else:
                    # If it's a database column, convert to dict
                    strategy_config = dict(subscription.strategy_config) if subscription.strategy_config else {}
            
            timeframe = strategy_config.get('timeframe', '1h')
            action = bot.execute_full_cycle(timeframe, strategy_config)
            
            if action and action.action != "HOLD":
                # Execute trade
                execute_trade_action(db, subscription, exchange, action, current_price)
            else:
                # Log hold action
                crud.log_bot_action(
                    db, subscription_id, "HOLD",
                    f"Bot decided to hold at price {current_price}. Reason: {action.reason if action else 'No action returned'}"
                )
                
        except Exception as e:
            logger.error(f"Error running bot logic: {str(e)}")
            crud.log_bot_action(
                db, subscription_id, "ERROR",
                f"Bot logic error: {str(e)}"
            )
            
        # Schedule next run
        next_run_delay = subscription.run_interval or 300  # Default 5 minutes
        run_bot_logic.apply_async(args=[subscription_id], countdown=next_run_delay)
        
        # Update last run time
        subscription.last_run_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"Error in run_bot_logic for subscription {subscription_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task for subscription {subscription_id}")
            raise self.retry(countdown=60, exc=e)
        else:
            logger.error(f"Max retries reached for subscription {subscription_id}")
            # Mark subscription as error
            crud.update_subscription_status(db, subscription_id, schemas.SubscriptionStatus.ERROR)

    finally:
        db.close()

@celery_app.task
def test_bot_from_s3(bot_id: int, version: str = None, test_config: Dict[str, Any] = None):
    """
    Test task to verify bot can be loaded and run from S3
    """
    try:
        # Load bot from S3
        bot_instance = crud.load_bot_from_s3(
            bot_id=bot_id,
            version=version,
            user_config=test_config or {},
            user_api_keys={}
        )
        
        if not bot_instance:
            return {
                "success": False,
                "error": "Failed to load bot from S3"
            }
        
        # Test basic functionality
        test_result = bot_manager.test_bot(bot_id, test_config or {})
        
        return {
            "success": True,
            "bot_id": bot_id,
            "version": version,
            "test_result": test_result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Bot test failed: {str(e)}"
        }

@celery_app.task
def backup_bot_to_s3(bot_id: int, version: str = None):
    """
    Backup bot from local storage to S3
    """
    db = SessionLocal()
    
    try:
        bot_record = crud.get_bot_by_id(db, bot_id)
        if not bot_record:
            return {"success": False, "error": "Bot not found"}
        
        # Read local bot file
        if not bot_record.code_path or not os.path.exists(bot_record.code_path):
            return {"success": False, "error": "Bot code file not found"}
        
        with open(bot_record.code_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        # Upload to S3
        upload_result = s3_manager.upload_bot_code(
            bot_id=bot_id,
            code_content=code_content,
            filename="bot.py",
            version=version
        )
        
        # Update bot record
        bot_record.code_path = upload_result['s3_key']
        bot_record.version = upload_result['version']
        db.commit()
        
        return {
            "success": True,
            "bot_id": bot_id,
            "s3_key": upload_result['s3_key'],
            "version": upload_result['version']
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

    finally:
        db.close()

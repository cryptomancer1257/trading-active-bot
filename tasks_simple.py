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
        'tasks_simple.run_bot_logic': {'queue': 'bot_execution'},
        'tasks_simple.cleanup_old_logs': {'queue': 'maintenance'},
    },
    task_default_retry_delay=60,
    task_max_retries=3,
    beat_schedule={
        'cleanup-old-logs': {
            'task': 'tasks_simple.cleanup_old_logs',
            'schedule': 300.0,  # Run every 5 minutes
        },
    },
)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def run_bot_logic(self, subscription_id: int):
    """
    Simplified bot logic task
    """
    try:
        logger.info(f"Starting bot logic for subscription {subscription_id}")
        
        # Import here to avoid circular imports
        import models
        import schemas
        import crud
        from database import SessionLocal
        from bots.bot_sdk import CustomBot, Action
        from exchange_factory import ExchangeFactory
        
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
                crud.update_subscription_status(db, subscription_id, schemas.SubscriptionStatus.ERROR)
                return
            
            # Create exchange client
            exchange_type = subscription.exchange_type or schemas.ExchangeType.BINANCE
            
            # Use testnet for trial subscriptions
            use_testnet = getattr(subscription, 'is_testnet', True)
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
                crud.log_bot_action(
                    db, subscription_id, "ERROR", 
                    f"Failed to get ticker for {symbol}: {str(e)}"
                )
                return
            
            # Run bot logic
            try:
                # Convert strategy_config to dict
                strategy_config = {}
                if subscription.strategy_config:
                    if isinstance(subscription.strategy_config, dict):
                        strategy_config = subscription.strategy_config
                    else:
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
                crud.update_subscription_status(db, subscription_id, schemas.SubscriptionStatus.ERROR)
        
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Critical error in run_bot_logic: {str(e)}")
        logger.error(traceback.format_exc())

def initialize_bot(subscription):
    """Initialize bot - simplified version"""
    try:
        import crud
        
        # First try to load from S3
        bot_instance = crud.load_bot_from_s3(
            bot_id=subscription.bot.id,
            version=subscription.bot.version,
            user_config=subscription.strategy_config or {},
            user_api_keys={
                'key': subscription.user.api_key,
                'secret': subscription.user.api_secret
            }
        )
        
        if bot_instance:
            logger.info(f"Successfully loaded bot {subscription.bot.id} from S3")
            return bot_instance
        else:
            logger.error(f"Failed to load bot {subscription.bot.id} from S3")
            return None
            
    except Exception as e:
        logger.error(f"Error initializing bot: {str(e)}")
        return None

def execute_trade_action(db, subscription, exchange, action, current_price):
    """Simplified trade execution"""
    try:
        import crud
        
        symbol = subscription.symbol.replace('/', '')
        
        # Get current balance
        base_asset = symbol.replace('USDT', '')
        quote_asset = 'USDT'
        
        base_balance = exchange.get_balance(base_asset)
        quote_balance = exchange.get_balance(quote_asset)
        
        base_free = float(base_balance.free)
        quote_free = float(quote_balance.free)
        
        logger.info(f"Current balance: {base_free} {base_asset}, {quote_free} {quote_asset}")
        
        if action.action == "BUY":
            # Buy with percentage of USDT balance
            usdt_amount = quote_free * action.value
            quantity_str, calc_info = exchange.calculate_quantity(symbol, "BUY", usdt_amount, current_price)
            
            logger.info(f"BUY: {action.value*100}% of {quote_free} USDT = {usdt_amount} USDT")
            logger.info(f"Quantity: {quantity_str} {base_asset} at ${current_price}")
            
            # Execute buy order
            order = exchange.create_market_order(symbol, "BUY", quantity_str)
            
            crud.log_bot_action(
                db, subscription.id, "BUY",
                f"Bought {quantity_str} {base_asset} at ${current_price}. Order ID: {order.order_id}"
            )
            
        elif action.action == "SELL":
            # Sell percentage of BTC holdings
            sell_quantity = base_free * action.value
            quantity_str, calc_info = exchange.calculate_quantity(symbol, "SELL", sell_quantity, current_price)
            
            logger.info(f"SELL: {action.value*100}% of {base_free} {base_asset} = {sell_quantity} {base_asset}")
            logger.info(f"Quantity: {quantity_str} {base_asset} at ${current_price}")
            
            # Execute sell order
            order = exchange.create_market_order(symbol, "SELL", quantity_str)
            
            crud.log_bot_action(
                db, subscription.id, "SELL",
                f"Sold {quantity_str} {base_asset} at ${current_price}. Order ID: {order.order_id}"
            )
        
        logger.info(f"Trade executed successfully: {action.action}")
        
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        crud.log_bot_action(
            db, subscription.id, "ERROR",
            f"Trade execution failed: {str(e)}"
        )

@celery_app.task
def cleanup_old_logs():
    """Clean up old logs - simplified version"""
    try:
        logger.info("Starting cleanup of old logs")
        # Add cleanup logic here
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")

@celery_app.task
def test_task():
    """Test task"""
    logger.info("Test task executed successfully")
    return "Test task completed" 
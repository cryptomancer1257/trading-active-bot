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

from celery_app import app
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_bot(subscription):
    """Initialize bot from subscription - Load from S3"""
    try:
        # Import here to avoid circular imports
        import models
        import schemas
        from database import SessionLocal
        from bots.bot_sdk import CustomBot
        from s3_manager import S3Manager
        
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
        
        # Add necessary base classes to the code
        base_classes = '''
# Base classes for bot execution
import pandas as pd
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Action:
    """Trading action class"""
    def __init__(self, action_type: str, amount: float, reason: str = "", action_method: str = "FIXED"):
        self.action_type = action_type.upper()  # BUY, SELL, HOLD
        self.amount = amount
        self.reason = reason
        self.action_method = action_method  # FIXED, PERCENTAGE
        self.confidence = 1.0
    
    @classmethod
    def buy(cls, method: str, amount: float, reason: str = ""):
        return cls("BUY", amount, reason, method)
    
    @classmethod  
    def sell(cls, method: str, amount: float, reason: str = ""):
        return cls("SELL", amount, reason, method)
    
    def __str__(self):
        return f"Action({self.action_type}, {self.amount}, {self.reason})"

class CustomBot:
    """Base bot class"""
    def __init__(self, config: Dict[str, Any] = None, api_keys: Dict[str, str] = None):
        self.config = config or {}
        self.api_keys = api_keys or {}
        self.bot_name = "Base Bot"
        self.version = "1.0.0"
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        return Action("HOLD", 0.0, "Base implementation")
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        return {}

'''
        
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
            
            # Initialize bot instance
            if not bot_class:
                logger.error("No valid bot class found in module")
                return None
            
            # Prepare bot configuration
            bot_config = {
                'short_window': 50,
                'long_window': 200,
                'position_size': 0.3,
                'min_volume_threshold': 1000000,
                'volatility_threshold': 0.05
            }
            
            # Override with subscription config if available
            if subscription.strategy_config:
                bot_config.update(subscription.strategy_config)
            
            # Prepare API keys (mock for now, real implementation would get from user)
            api_keys = {
                'exchange': subscription.exchange_type.value if subscription.exchange_type else 'binance',
                'key': 'test_key',  # Would be real API key in production
                'secret': 'test_secret',  # Would be real API secret in production  
                'testnet': subscription.is_testnet if subscription.is_testnet else True
            }
            
            # Try to initialize bot with new constructor format first
            try:
                bot_instance = bot_class(bot_config, api_keys)
                logger.info(f"Successfully initialized bot with new constructor: {bot_class.__name__} v{latest_version}")
            except TypeError as e:
                # Fallback to old constructor format (no parameters)
                if "missing" in str(e) and "required positional arguments" in str(e):
                    try:
                        bot_instance = bot_class()
                        logger.info(f"Successfully initialized bot with old constructor: {bot_class.__name__} v{latest_version}")
                        # Set config manually if the bot has attributes for it
                        if hasattr(bot_instance, 'short_window'):
                            bot_instance.short_window = bot_config.get('short_window', 50)
                        if hasattr(bot_instance, 'long_window'):
                            bot_instance.long_window = bot_config.get('long_window', 200)
                        if hasattr(bot_instance, 'position_size'):
                            bot_instance.position_size = bot_config.get('position_size', 0.3)
                    except Exception as fallback_error:
                        logger.error(f"Both new and old constructor failed: {fallback_error}")
                        return None
                else:
                    logger.error(f"Bot initialization failed: {e}")
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
        import crud
        
        # Fix: Use trading_pair instead of symbol
        trading_pair = subscription.trading_pair or 'BTC/USDT'
        symbol = trading_pair.replace('/', '')
        
        # Get balance
        base_asset = symbol.replace('USDT', '')
        quote_asset = 'USDT'
        
        base_balance = exchange.get_balance(base_asset)
        quote_balance = exchange.get_balance(quote_asset)
        
        base_free = float(base_balance.free)
        quote_free = float(quote_balance.free)
        
        logger.info(f"Current balance: {base_free} {base_asset}, {quote_free} {quote_asset}")
        
        if action.action == "BUY":
            # Buy with percentage of USDT balance
            usdt_amount = quote_free * (action.value or 0.1)
            quantity_str, calc_info = exchange.calculate_quantity(symbol, "BUY", usdt_amount, current_price)
            
            logger.info(f"BUY: {(action.value or 0.1)*100}% of {quote_free} USDT = {usdt_amount} USDT")
            logger.info(f"Quantity: {quantity_str} {base_asset} at ${current_price}")
            
            # Execute buy order
            order = exchange.create_market_order(symbol, "BUY", quantity_str)
            
            crud.log_bot_action(
                db, subscription.id, "BUY",
                f"Bought {quantity_str} {base_asset} at ${current_price}. Order ID: {order.order_id}"
            )
            
            # Send email notification
            try:
                send_email_notification.delay(
                    subscription.user.email,
                    f"🚀 Bot Trade Executed - {subscription.bot.name}",
                    f"Your bot executed a BUY order:\n"
                    f"Symbol: {trading_pair}\n"
                    f"Quantity: {quantity_str} {base_asset}\n"
                    f"Price: ${current_price}\n"
                    f"Order ID: {order.order_id}\n"
                    f"Reason: {action.reason or 'Bot signal'}\n"
                    f"{'🧪 TESTNET' if getattr(subscription, 'is_testnet', True) else '🚀 MAINNET'}"
                )
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
            
        elif action.action == "SELL":
            # Sell percentage of holdings
            sell_quantity = base_free * (action.value or 0.5)
            quantity_str, calc_info = exchange.calculate_quantity(symbol, "SELL", sell_quantity, current_price)
            
            logger.info(f"SELL: {(action.value or 0.5)*100}% of {base_free} {base_asset}")
            logger.info(f"Quantity: {quantity_str} {base_asset} at ${current_price}")
            
            # Execute sell order
            order = exchange.create_market_order(symbol, "SELL", quantity_str)
            
            crud.log_bot_action(
                db, subscription.id, "SELL",
                f"Sold {quantity_str} {base_asset} at ${current_price}. Order ID: {order.order_id}"
            )
            
            # Send email notification
            try:
                send_email_notification.delay(
                    subscription.user.email,
                    f"🚀 Bot Trade Executed - {subscription.bot.name}",
                    f"Your bot executed a SELL order:\n"
                    f"Symbol: {trading_pair}\n"
                    f"Quantity: {quantity_str} {base_asset}\n"
                    f"Price: ${current_price}\n"
                    f"Order ID: {order.order_id}\n"
                    f"Reason: {action.reason or 'Bot signal'}\n"
                    f"{'🧪 TESTNET' if getattr(subscription, 'is_testnet', True) else '🚀 MAINNET'}"
                )
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
        
        logger.info(f"Trade executed successfully: {action.action}")
        
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        crud.log_bot_action(
            db, subscription.id, "ERROR",
            f"Trade execution failed: {str(e)}"
        )

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def run_bot_logic(self, subscription_id: int):
    """
    Main task to run bot logic
    """
    try:
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

            # Skip if subscription is not active - Fix: Use models.SubscriptionStatus
            if subscription.status != models.SubscriptionStatus.ACTIVE:
                logger.info(f"Subscription {subscription_id} is not active (status: {subscription.status}), skipping")
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
            
            # Get exchange credentials - prioritize exchange_credentials table
            api_key = None
            api_secret = None
            
            # First try to get from exchange_credentials table
            logger.info(f"Looking for exchange credentials for user {subscription.user.email}")
            credentials = crud.get_user_exchange_credentials(
                db, 
                user_id=subscription.user.id, 
                exchange=exchange_type.value,
                is_testnet=use_testnet
            )
            if credentials:
                cred = credentials[0]  # Get first matching credential
                api_key = cred.api_key
                api_secret = cred.api_secret
                logger.info(f"Found exchange credentials for {exchange_type.value} (testnet={use_testnet})")
            else:
                # Fallback to user's direct API credentials
                logger.info(f"No exchange credentials found, checking user direct credentials")
                api_key = subscription.user.api_key
                api_secret = subscription.user.api_secret
                if api_key and api_secret:
                    logger.info(f"Using user direct API credentials")
            
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
            
            # Get current market data - Fix: Use trading_pair
            trading_pair = subscription.trading_pair or 'BTC/USDT'
            # Convert to exchange format (BTCUSDT for Binance)
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

            # Run bot logic
            try:
                # Convert strategy_config to dict
                strategy_config = {}
                if subscription.strategy_config:
                    import json
                    strategy_config = json.loads(subscription.strategy_config)
                
                # Crawl market data - Fix: Pass timeframe, not trading_pair and exchange
                timeframe = subscription.timeframe or '1h'
                market_data = bot.crawl_market_data(timeframe)
                
                # Check if we have data before proceeding
                if market_data.empty:
                    logger.warning(f"No market data available for subscription {subscription_id}")
                    crud.log_bot_action(
                        db, subscription_id, "HOLD", 
                        "No market data available - skipping execution"
                    )
                    return
                
                # Preprocess data
                processed_data = bot.preprocess_data(market_data)
                
                # Execute algorithm - Fix: Pass timeframe as second parameter
                action = bot.execute_algorithm(processed_data, timeframe, strategy_config)
                
                # Post-process action
                final_action = bot.post_process_action(action, processed_data)
                
                # Always log the action first
                logger.info(f"Bot decided to {final_action.action}: {final_action.reason}")
                crud.log_bot_action(
                    db, subscription_id, final_action.action,
                    f"{final_action.reason}. Value: {final_action.value or 0.0}. Price: ${current_price}"
                )
                
                # Initialize bot with exchange client
                bot.exchange_client = exchange
                
                # Create subscription config
                subscription_config = {
                    'subscription_id': subscription_id,
                    'timeframe': subscription.timeframe,
                    'trading_pair': trading_pair,
                    'is_testnet': use_testnet,
                    'exchange_type': exchange_type.value,
                    'user_id': subscription.user.id
                }
                
                # Execute bot prediction
                final_action = bot.execute_full_cycle(subscription.timeframe, subscription_config)
                
                if final_action:
                    logger.info(f"Bot {subscription.bot.name} executed with action: {final_action.action}, value: {final_action.value}, reason: {final_action.reason}")
                    
                    # Log action to database
                    crud.log_bot_action(
                        db, subscription_id, final_action.action,
                        f"{final_action.reason}. Value: {final_action.value or 0.0}. Price: ${current_price}"
                    )
                    
                    # Get balance info for BUY/SELL actions (both live and testnet)
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
                    
                    # Send email notification for ALL actions (including HOLD)
                    try:
                        from datetime import datetime
                        # Different emoji for different actions
                        action_emoji = {
                            "BUY": "🟢",
                            "SELL": "🔴", 
                            "HOLD": "🟡"
                        }.get(final_action.action, "📊")
                        
                        send_email_notification.delay(
                            subscription.user.email,
                            f"{action_emoji} Bot {final_action.action} Signal - {subscription.bot.name}",
                            f"Your bot analysis complete:\n\n"
                            f"📈 Symbol: {trading_pair}\n"
                            f"💰 Price: ${current_price:.2f}\n"
                            f"🎯 Action: {final_action.action}\n"
                            f"📝 Reason: {final_action.reason}\n"
                            f"⚡ Confidence: {final_action.value or 'N/A'}\n"
                            f"⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                            f"🔄 Timeframe: {timeframe}\n"
                            f"{'🧪 TESTNET MODE' if bool(subscription.is_testnet) else '🚀 LIVE TRADING'}"
                            f"{balance_info}\n"
                            f"{'✅ Trade executed' if final_action.action != 'HOLD' and not bool(subscription.is_testnet) else '📊 Analysis only (testnet/hold)'}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send signal notification: {e}")
                
                # Execute trade only for BUY/SELL actions and not in testnet
                if final_action.action != "HOLD" and not subscription.is_testnet:
                    execute_trade_action(db, subscription, exchange, final_action, current_price)
                else:
                    if final_action.action != "HOLD":
                        logger.info("Testnet mode - trade not executed")
                    else:
                        logger.info("HOLD action - no trade execution")
                
                # Update last_run_at and calculate next_run_at
                from datetime import datetime, timedelta
                now = datetime.utcnow()
                subscription.last_run_at = now
                
                # Calculate next run time based on timeframe
                timeframe_minutes = {
                    '1m': 1, '5m': 5, '15m': 15, '30m': 30,
                    '1h': 60, '4h': 240, '1d': 1440, '1w': 10080
                }
                
                minutes = timeframe_minutes.get(timeframe, 60)  # Default to 1 hour
                subscription.next_run_at = now + timedelta(minutes=minutes)
                db.commit()
                
                # Schedule next execution
                run_bot_logic.apply_async(
                    args=[subscription_id], 
                    eta=subscription.next_run_at
                )
                
            except Exception as e:
                logger.error(f"Error running bot logic: {e}")
                logger.error(traceback.format_exc())
                
                # Update subscription status to ERROR if there are persistent failures
                crud.log_bot_action(
                    db, subscription_id, "ERROR",
                    f"Bot execution failed: {str(e)}"
                )

        except Exception as e:
            logger.error(f"Critical error in run_bot_logic: {e}")
            logger.error(traceback.format_exc())
            # Don't raise here to avoid task retry loops
        finally:
            db.close()

@app.task
def schedule_active_bots():
    """
    Periodic task to check and schedule bot executions based on timeframe
    This ensures bots continue running even after system restart
    """
    try:
        import models
        import crud
        from database import SessionLocal
        from datetime import datetime
        
        db = SessionLocal()
        logger.info("Checking active subscriptions for scheduling...")
        
        try:
            # Get all active subscriptions that need to run
            now = datetime.utcnow()
            active_subscriptions = db.query(models.Subscription).filter(
                models.Subscription.status == models.SubscriptionStatus.ACTIVE,
                models.Subscription.next_run_at.is_(None) | 
                (models.Subscription.next_run_at <= now)
            ).all()
            
            scheduled_count = 0
            for subscription in active_subscriptions:
                try:
                    # Check if subscription is still valid (not expired)
                    if subscription.expires_at and subscription.expires_at <= now:
                        logger.info(f"Subscription {subscription.id} expired, marking as cancelled")
                        crud.update_subscription_status(
                            db, subscription.id, models.SubscriptionStatus.CANCELLED
                        )
                        continue
                    
                    # Check trial expiration
                    if subscription.is_trial and subscription.trial_expires_at:
                        if subscription.trial_expires_at <= now:
                            logger.info(f"Trial subscription {subscription.id} expired")
                            crud.update_subscription_status(
                                db, subscription.id, models.SubscriptionStatus.EXPIRED
                            )
                            continue
                    
                    # Schedule bot execution
                    logger.info(f"Scheduling bot execution for subscription {subscription.id} (timeframe: {subscription.timeframe})")
                    run_bot_logic.apply_async(args=[subscription.id], countdown=5)
                    scheduled_count += 1
                    
                except Exception as e:
                    logger.error(f"Error scheduling subscription {subscription.id}: {e}")
            
            logger.info(f"Scheduled {scheduled_count} bot executions")

        except Exception as e:
            logger.error(f"Error in schedule_active_bots: {e}")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in schedule_active_bots outer: {e}")

@app.task
def cleanup_old_logs():
    """Clean up old logs"""
    try:
        logger.info("Starting cleanup of old logs")
        # Add actual cleanup logic here if needed
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")

@app.task
def send_email_notification(email: str, subject: str, body: str):
    """Send email notification - Simple version for testing"""
    try:
        # Try SendGrid first, fallback to Gmail SMTP
        try:
            from sendgrid_email_service import email_service as sendgrid_service
            if sendgrid_service.email_configured:
                success = sendgrid_service.send_email(
                    to_email=email,
                    subject=subject,
                    html_body=f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px; }}
                            .content {{ line-height: 1.6; }}
                            .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px; text-align: center; }}
                            pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h2>Bot Marketplace Notification</h2>
                            </div>
                            <div class="content">
                                <pre>{body}</pre>
                            </div>
                            <div class="footer">
                                <p>Bot Marketplace - Automated Trading Platform</p>
                                <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """,
                    text_body=body
                )
                if success:
                    logger.info(f"Email sent via SendGrid to {email}")
                    return
        except Exception as e:
            logger.warning(f"SendGrid failed: {e}, trying Gmail SMTP...")
        
        # Fallback to Gmail SMTP
        from gmail_smtp_service import email_service
        
        logger.info(f"Sending email to {email}: {subject}")
        
        # Create HTML version of the email
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; margin: -20px -20px 20px -20px; }}
                .content {{ line-height: 1.6; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px; text-align: center; }}
                pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Bot Marketplace Notification</h2>
                </div>
                <div class="content">
                    <pre>{body}</pre>
                </div>
                <div class="footer">
                    <p>Bot Marketplace - Automated Trading Platform</p>
                    <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email using Gmail SMTP service
        success = email_service.send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=body
        )
        
        if success:
            logger.info(f"Email notification processed successfully for {email}")
        else:
            logger.error(f"Failed to process email notification for {email}")
            
    except ImportError as e:
        logger.warning(f"Email service not available: {e}")
        logger.info(f"Would send email to {email}: {subject}")
        logger.info(f"Body: {body}")
    except Exception as e:
        logger.error(f"Error processing email notification for {email}: {e}")
        logger.info(f"Fallback - Would send email to {email}: {subject}")
        logger.info(f"Body: {body}")

@app.task
def send_sendgrid_notification(email: str, bot_name: str, action: str, details: dict):
    """Send email notification using SendGrid - No user configuration needed!"""
    try:
        # Import SendGrid email service
        from sendgrid_email_service import email_service
        
        logger.info(f"Sending SendGrid notification to {email}: {action} - {bot_name}")
        
        # Send email using SendGrid service with professional formatting
        success = email_service.send_bot_notification(
            to_email=email,
            bot_name=bot_name,
            action=action,
            details=details
        )
        
        if success:
            logger.info(f"SendGrid notification sent successfully for {email}")
        else:
            logger.error(f"Failed to send SendGrid notification for {email}")
            
    except ImportError as e:
        logger.warning(f"SendGrid email service not available: {e}")
        logger.info(f"Would send {action} notification to {email} for {bot_name}")
    except Exception as e:
        logger.error(f"Error sending SendGrid notification for {email}: {e}")
        logger.info(f"Fallback - Would send {action} notification to {email} for {bot_name}")

@app.task
def test_task():
    """Test task"""
    logger.info("Test task executed successfully")
    return "Test task completed"

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
        from s3_manager import S3Manager
        from bot_base_classes import get_base_classes
        
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
    """Execute trade action and return trade details for email"""
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
        
        trade_details = {
            'action': action.action,
            'symbol': trading_pair,
            'base_asset': base_asset,
            'quote_asset': quote_asset,
            'current_price': current_price,
            'reason': action.reason or 'Bot signal',
            'order_id': None,
            'quantity': None,
            'usdt_value': None,
            'percentage_used': None,
            'success': False,
            'error': None
        }
        
        if action.action == "BUY":
            # Fix: Handle percentage values > 1.0 as actual percentages, not decimals
            percentage = action.value or 0.1  # Default 10%
            if percentage > 1.0:
                percentage = percentage / 100.0  # Convert 5.0 → 0.05 (5%)
            
            # Buy with percentage of USDT balance
            usdt_amount = quote_free * percentage
            quantity_str, calc_info = exchange.calculate_quantity(symbol, "BUY", usdt_amount, current_price)
            
            logger.info(f"BUY: {percentage*100:.1f}% of {quote_free} USDT = {usdt_amount:.2f} USDT")
            logger.info(f"Quantity: {quantity_str} {base_asset} at ${current_price}")
            
            # Execute buy order
            order = exchange.create_market_order(symbol, "BUY", quantity_str)
            
            # Calculate USDT value
            usdt_value = float(quantity_str) * current_price
            percentage_used = percentage * 100
            
            # Update trade details
            trade_details.update({
                'order_id': order.order_id,
                'quantity': quantity_str,
                'usdt_value': usdt_value,
                'percentage_used': percentage_used,
                'success': True
            })
            
            crud.log_bot_action(
                db, subscription.id, "BUY",
                f"Bought {quantity_str} {base_asset} at ${current_price}. Order ID: {order.order_id}"
            )
            
        elif action.action == "SELL":
            # Fix: Handle percentage values > 1.0 as actual percentages, not decimals
            percentage = action.value or 0.5  # Default 50%
            if percentage > 1.0:
                percentage = percentage / 100.0  # Convert 5.0 → 0.05 (5%)
            
            # Sell percentage of holdings
            sell_quantity = base_free * percentage
            quantity_str, calc_info = exchange.calculate_quantity(symbol, "SELL", sell_quantity, current_price)
            
            logger.info(f"SELL: {percentage*100:.1f}% of {base_free} {base_asset}")
            logger.info(f"Quantity: {quantity_str} {base_asset} at ${current_price}")
            
            # Execute sell order
            order = exchange.create_market_order(symbol, "SELL", quantity_str)
            
            # Calculate USDT value and percentage
            usdt_value = float(quantity_str) * current_price
            percentage_sold = percentage * 100
            
            # Update trade details
            trade_details.update({
                'order_id': order.order_id,
                'quantity': quantity_str,
                'usdt_value': usdt_value,
                'percentage_used': percentage_sold,
                'success': True
            })
            
            crud.log_bot_action(
                db, subscription.id, "SELL",
                f"Sold {quantity_str} {base_asset} at ${current_price}. Order ID: {order.order_id}"
            )
        
        logger.info(f"Trade executed successfully: {action.action}")
        return trade_details
        
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        crud.log_bot_action(
            db, subscription.id, "ERROR",
            f"Trade execution failed: {str(e)}"
        )
        
        # Return error details
        return {
            'action': action.action,
            'symbol': trading_pair,
            'current_price': current_price,
            'reason': action.reason or 'Bot signal',
            'success': False,
            'error': str(e)
        }

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
                api_key = str(subscription.user.api_key) if subscription.user.api_key else None
                api_secret = str(subscription.user.api_secret) if subscription.user.api_secret else None
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
                api_key=str(api_key),
                api_secret=str(api_secret),
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
                
                # Prepare subscription config for bot
                subscription_config = {
                    'subscription_id': subscription.id,
                    'user_id': subscription.user_id,
                    'timeframe': timeframe,
                    'trading_pair': trading_pair,
                    'is_testnet': bool(subscription.is_testnet),
                    'risk_config': subscription.risk_config or {}
                }

                # Execute bot prediction
                final_action = bot.execute_full_cycle(timeframe, subscription_config)
                
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
                            # Get balance from exchange
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
                            logger.error(f"Could not get balance info: {e}", exc_info=True)
                            mode_label = "TESTNET" if bool(subscription.is_testnet) else "LIVE"
                            
                            # For testnet, provide mock balance when no credentials
                            if bool(subscription.is_testnet) and "credentials" in str(e).lower():
                                balance_info = f"\n💼 Account Balance ({mode_label} - DEMO):\n" \
                                             f"   • BTC: 0.100000 (Free: 0.100000, Locked: 0.000000)\n" \
                                             f"   • USDT: 10000.00 (Free: 10000.00, Locked: 0.00)\n" \
                                             f"   • Portfolio Value: ~${10000 + (0.1 * current_price):.2f} USDT\n" \
                                             f"   ⚠️ Demo balance - Configure exchange credentials for real data\n"
                            else:
                                balance_info = f"\n💼 Account Balance ({mode_label}): Error - {str(e)[:100]}...\n"
                    
                    # Execute trade for BUY/SELL actions (including testnet now!)
                    trade_details = None
                    if final_action.action != "HOLD":
                        trade_details = execute_trade_action(db, subscription, exchange, final_action, current_price)
                        logger.info(f"Trade executed: {final_action.action} ({'TESTNET' if bool(subscription.is_testnet) else 'LIVE'})")
                        if not trade_details['success']:
                            logger.error(f"Trade execution failed: {trade_details['error']}")
                            crud.log_bot_action(
                                db, subscription_id, "ERROR",
                                f"Trade execution failed: {trade_details['error']}"
                            )
                    else:
                        logger.info("HOLD action - no trade execution")
                    
                    # Send combined email notification (signal + trade execution)
                    try:
                        from datetime import datetime
                        from email_templates import create_email_content, EmailTemplates
                        
                        # Get balance info if available
                        balance_info = ""
                        if final_action.action in ["BUY", "SELL"]:
                            try:
                                # Get balance from exchange
                                base_asset = trading_pair.split('/')[0]  # BTC from BTC/USDT
                                quote_asset = trading_pair.split('/')[1]  # USDT from BTC/USDT
                                
                                base_balance = exchange.get_balance(base_asset)
                                quote_balance = exchange.get_balance(quote_asset)
                                
                                balance_info = EmailTemplates.get_balance_info_template(
                                    base_asset=base_asset,
                                    quote_asset=quote_asset,
                                    base_balance=base_balance,
                                    quote_balance=quote_balance,
                                    current_price=current_price,
                                    is_testnet=bool(subscription.is_testnet)
                                )
                            except Exception as e:
                                logger.error(f"Could not get balance info: {e}", exc_info=True)
                                mode_label = "TESTNET" if bool(subscription.is_testnet) else "LIVE"
                                
                                # For testnet, provide mock balance when no credentials
                                if bool(subscription.is_testnet) and "credentials" in str(e).lower():
                                    balance_info = EmailTemplates.get_demo_balance_template(
                                        base_asset=trading_pair.split('/')[0],
                                        quote_asset=trading_pair.split('/')[1],
                                        current_price=current_price,
                                        is_testnet=bool(subscription.is_testnet)
                                    )
                                else:
                                    balance_info = f"\n💼 Account Balance ({mode_label}): Error - {str(e)[:100]}...\n"
                        
                        # Create email content using template
                        email_subject, email_body = create_email_content(
                            action=final_action.action,
                            bot_name=subscription.bot.name,
                            trading_pair=trading_pair,
                            current_price=current_price,
                            reason=final_action.reason or 'Bot signal',
                            confidence=final_action.value,
                            timeframe=timeframe,
                            is_testnet=bool(subscription.is_testnet),
                            trade_details=trade_details,
                            balance_info=balance_info
                        )
                        
                        send_email_notification.delay(
                            subscription.user.email,
                            email_subject,
                            email_body
                        )
                    except Exception as e:
                        logger.error(f"Failed to send combined notification: {e}")
                
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

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Critical error in run_bot_logic: {e}")
        logger.error(traceback.format_exc())
        raise

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

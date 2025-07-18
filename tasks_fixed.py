#!/usr/bin/env python3
"""
Fixed run_bot_logic function
"""

import logging
from datetime import datetime, timedelta
from celery import Celery
import os
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# Initialize Celery app
app = Celery('bot_marketplace')

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def run_bot_logic(self, subscription_id: int):
    """
    Main task to run bot logic - FIXED VERSION
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

            # Skip if subscription is not active
            if subscription.status != models.SubscriptionStatus.ACTIVE:
                logger.info(f"Subscription {subscription_id} is not active (status: {subscription.status}), skipping")
                return

            # Initialize bot
            from tasks import initialize_bot
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
                
                # Send email notification for ALL actions (including HOLD)
                try:
                    from datetime import datetime
                    from tasks import send_email_notification
                    
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
                        f"🔄 Timeframe: {subscription.timeframe}\n"
                        f"{'🧪 TESTNET MODE' if bool(subscription.is_testnet) else '🚀 LIVE TRADING'}"
                        f"{balance_info}\n"
                        f"{'✅ Trade executed' if final_action.action != 'HOLD' and not bool(subscription.is_testnet) else '📊 Analysis only (testnet/hold)'}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send signal notification: {e}")
                
                # Execute actual trading (if not testnet and not HOLD)
                if final_action.action != "HOLD" and not use_testnet:
                    try:
                        from tasks import execute_trade_action
                        execute_trade_action(db, subscription, exchange, final_action, current_price)
                    except Exception as e:
                        logger.error(f"Failed to execute trade: {e}")
                        crud.log_bot_action(
                            db, subscription_id, "ERROR", 
                            f"Failed to execute {final_action.action} trade: {str(e)}"
                        )
            
            # Schedule next run
            from tasks import schedule_next_run
            schedule_next_run(db, subscription_id, subscription.timeframe)
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error running bot logic: {e}")
        import traceback
        traceback.print_exc() 
"""
WebSocket Manager for Zone Trading

Manages WebSocket connections to multiple exchanges (Binance, Bybit)
Monitors real-time prices and triggers zone-based trades
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from services.websocket_connectors import BinanceFuturesWebSocket, BybitFuturesWebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections to multiple exchanges
    Monitors prices and triggers zone-based trades
    """
    
    def __init__(self):
        self.connections = {}  # {exchange: connection}
        self.subscriptions = {}  # {symbol: [subscription_ids]}
        self.running = False
        self.last_trigger_check = {}  # {zone_id: timestamp} for debouncing
        self.price_callbacks = {}  # {(exchange, symbol): [callbacks]}
        self.last_subscriptions_reload = None  # Track last reload time
        
        # Initialize connectors (will be recreated with testnet flag in start())
        self.binance_ws = None
        self.bybit_ws = None
        
    async def start(self):
        """Start WebSocket connections for all active subscriptions"""
        try:
            logger.info("🚀 Starting WebSocket Manager...")
            self.running = True
            
            # Load active subscriptions from database
            subscriptions_by_exchange = await self._load_active_subscriptions()
            
            if not subscriptions_by_exchange:
                logger.warning("No active subscriptions found with zone trading enabled")
                return
            
            # Start WebSocket connections for each exchange
            tasks = []
            
            if 'binance' in subscriptions_by_exchange:
                symbols = subscriptions_by_exchange['binance']['symbols']
                testnet = subscriptions_by_exchange['binance'].get('testnet', False)
                logger.info(f"📊 Starting Binance WebSocket for {len(symbols)} symbols (testnet={testnet})")
                self.binance_ws = BinanceFuturesWebSocket()
                task = asyncio.create_task(
                    self.binance_ws.subscribe_ticker(symbols, self._on_binance_price_update)
                )
                tasks.append(task)
            
            if 'bybit' in subscriptions_by_exchange:
                symbols = subscriptions_by_exchange['bybit']['symbols']
                testnet = subscriptions_by_exchange['bybit'].get('testnet', False)
                logger.info(f"📊 Starting Bybit WebSocket for {len(symbols)} symbols (testnet={testnet})")
                self.bybit_ws = BybitFuturesWebSocket(testnet=testnet)
                task = asyncio.create_task(
                    self.bybit_ws.subscribe_ticker(symbols, self._on_bybit_price_update)
                )
                tasks.append(task)
            
            # Wait for all WebSocket tasks (they run indefinitely)
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"❌ WebSocket Manager startup failed: {e}")
            raise
    
    async def stop(self):
        """Stop all WebSocket connections"""
        logger.info("🛑 Stopping WebSocket Manager...")
        self.running = False
        
        # Close all connections with error handling
        try:
            if self.binance_ws:
                await self.binance_ws.close()
        except Exception as e:
            logger.warning(f"⚠️  Error closing Binance connection: {e}")
        
        try:
            if self.bybit_ws:
                await self.bybit_ws.close()
        except Exception as e:
            logger.warning(f"⚠️  Error closing Bybit connection: {e}")
        
        logger.info("✅ WebSocket Manager stopped")
    
    async def _load_active_subscriptions(self) -> Dict:
        """
        Load active subscriptions with zone trading enabled from database
        Group by exchange and symbol
        
        Returns:
            {
                'binance': {
                    'symbols': ['BTCUSDT', 'ETHUSDT'],
                    'subscriptions': {
                        'BTCUSDT': [subscription_id1, subscription_id2],
                        'ETHUSDT': [subscription_id3]
                    }
                },
                'bybit': {...}
            }
        """
        from core.database import SessionLocal
        from core import models
        
        db = SessionLocal()
        
        try:
            # Query subscriptions with zone trading enabled
            subscriptions = db.query(models.Subscription).join(
                models.Bot,
                models.Subscription.bot_id == models.Bot.id
            ).filter(
                models.Subscription.status == 'active',
                models.Bot.zone_trading_enabled == True
            ).all()
            
            if not subscriptions:
                return {}
            
            logger.info(f"📋 Found {len(subscriptions)} active subscriptions with zone trading")
            
            # Group by exchange
            result = {}
            
            for subscription in subscriptions:
                # Determine exchange from bot type or subscription config
                exchange = self._get_exchange_for_subscription(subscription)
                symbol = subscription.trading_pair
                
                if exchange not in result:
                    result[exchange] = {
                        'symbols': set(),
                        'subscriptions': {},
                        'testnet': subscription.is_testnet  # Track testnet status
                    }
                
                result[exchange]['symbols'].add(symbol)
                
                if symbol not in result[exchange]['subscriptions']:
                    result[exchange]['subscriptions'][symbol] = []
                
                result[exchange]['subscriptions'][symbol].append(subscription.id)
            
            # Convert sets to lists for JSON serialization
            for exchange in result:
                result[exchange]['symbols'] = list(result[exchange]['symbols'])
            
            # Store subscriptions mapping for price callbacks
            for exchange in result:
                for symbol, sub_ids in result[exchange]['subscriptions'].items():
                    self.subscriptions[symbol] = sub_ids
            
            return result
            
        finally:
            db.close()
    
    async def _reload_subscriptions_mapping(self):
        """
        Reload subscriptions mapping from database
        Picks up new subscriptions with zone trading enabled without restart
        """
        try:
            from core.database import SessionLocal
            from core import models
            
            db = SessionLocal()
            
            try:
                # Query active subscriptions with zone trading enabled
                subscriptions = db.query(models.Subscription).join(
                    models.Bot,
                    models.Subscription.bot_id == models.Bot.id
                ).filter(
                    models.Subscription.status == 'active',
                    models.Bot.zone_trading_enabled == True
                ).all()
                
                # Rebuild subscriptions mapping
                new_mapping = {}
                for subscription in subscriptions:
                    symbol = subscription.trading_pair
                    if symbol not in new_mapping:
                        new_mapping[symbol] = []
                    new_mapping[symbol].append(subscription.id)
                
                # Update mapping atomically
                self.subscriptions = new_mapping
                
                logger.info(f"🔄 Reloaded subscriptions mapping: {len(new_mapping)} symbols, {sum(len(subs) for subs in new_mapping.values())} subscriptions")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error reloading subscriptions mapping: {e}")
    
    def _get_exchange_for_subscription(self, subscription) -> str:
        """Determine exchange for a subscription (binance or bybit)"""
        # Check bot_type or other indicators
        bot = subscription.bot
        
        # For now, default to binance for futures, can be extended
        if hasattr(bot, 'exchange_type') and bot.exchange_type:
            # Convert enum to string value - handle both enum and string
            try:
                if hasattr(bot.exchange_type, 'value'):
                    exchange_str = str(bot.exchange_type.value).lower()
                elif hasattr(bot.exchange_type, 'name'):
                    exchange_str = str(bot.exchange_type.name).lower()
                else:
                    exchange_str = str(bot.exchange_type).lower()
                    
                if 'bybit' in exchange_str:
                    return 'bybit'
            except Exception as e:
                logger.warning(f"Error parsing exchange_type: {e}, defaulting to binance")
        
        # Default to binance
        return 'binance'
    
    async def _on_binance_price_update(self, symbol: str, price: float, timestamp: int):
        """Called when price update received from Binance WebSocket"""
        await self._handle_price_update('binance', symbol, price, timestamp)
    
    async def _on_bybit_price_update(self, symbol: str, price: float, timestamp: int):
        """Called when price update received from Bybit WebSocket"""
        await self._handle_price_update('bybit', symbol, price, timestamp)
    
    async def _handle_price_update(self, exchange: str, symbol: str, price: float, timestamp: int):
        """
        Handle price update from any exchange
        
        Process:
        1. Query active trigger_zones for this symbol
        2. Check if price is in any zone range
        3. Check if zone was triggered in current candle (debounce)
        4. Fetch latest indicators
        5. Call llm_service.analyze_market() for final confirmation
        6. If confirmed, execute trade via bot.setup_position()
        7. Update zone status to 'triggered'
        """
        if not self.running:
            return
        
        try:
            # Periodic reload of subscriptions mapping (every 5 minutes)
            # This allows new subscriptions to be picked up without restart
            now = datetime.utcnow()
            if self.last_subscriptions_reload is None or (now - self.last_subscriptions_reload).total_seconds() > 300:
                await self._reload_subscriptions_mapping()
                self.last_subscriptions_reload = now
            
            # Get subscription IDs for this symbol (try with and without "/")
            subscription_ids = self.subscriptions.get(symbol, [])
            
            # If not found, try normalized versions
            if not subscription_ids:
                # Try adding "/" for common pairs (BTCUSDT -> BTC/USDT)
                if len(symbol) >= 6 and "/" not in symbol:
                    symbol_with_slash = f"{symbol[:3]}/{symbol[3:]}"
                    subscription_ids = self.subscriptions.get(symbol_with_slash, [])
                # Try removing "/" (BTC/USDT -> BTCUSDT)
                elif "/" in symbol:
                    symbol_no_slash = symbol.replace("/", "")
                    subscription_ids = self.subscriptions.get(symbol_no_slash, [])
            
            if not subscription_ids:
                return
            
            # Query active trigger zones for this symbol
            from core.database import SessionLocal
            from core import models
            
            db = SessionLocal()
            
            try:
                # Normalize symbol for comparison (both BTC/USDT and BTCUSDT formats)
                symbol_normalized = symbol.replace("/", "")
                symbol_with_slash = f"{symbol[:3]}/{symbol[3:]}" if "/" not in symbol else symbol
                
                zones = db.query(models.TriggerZone).filter(
                    models.TriggerZone.subscription_id.in_(subscription_ids),
                    models.TriggerZone.status == 'active',
                    models.TriggerZone.expires_at > datetime.utcnow()
                ).filter(
                    (models.TriggerZone.symbol == symbol) | 
                    (models.TriggerZone.symbol == symbol_normalized) |
                    (models.TriggerZone.symbol == symbol_with_slash)
                ).all()
                
                if not zones:
                    return
                
                logger.info(f"💹 {exchange.upper()} {symbol} @ ${price:,.2f} | {len(zones)} active zones")
                
                # Sort zones by confidence (highest first) to prioritize best opportunities
                zones_sorted = sorted(zones, key=lambda z: z.confidence, reverse=True)
                
                # Check each zone - stop after first successful trigger to avoid multiple entries
                for zone in zones_sorted:
                    # Check if price is in this zone
                    if not (float(zone.price_min) <= price <= float(zone.price_max)):
                        continue
                    
                    # Attempt to trigger this zone
                    if await self._check_and_trigger_zone(zone, price, exchange, db):
                        logger.info(f"🎯 Zone {zone.id} (confidence {zone.confidence}%) triggered for {symbol} at ${price:.2f}")
                        # Stop after first successful trigger
                        break
                    else:
                        logger.debug(f"  ⏭️  Zone {zone.id} in range but trigger blocked (debounce or execution failed)")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error handling price update for {symbol}: {e}")
    
    async def _check_and_trigger_zone(self, zone, current_price: float, exchange: str, db) -> bool:
        """
        Check if zone should trigger (debounce check) and execute trade
        
        Note: Price range check is done in caller
        
        Returns:
            True if zone was successfully triggered and executed, False otherwise
        """
        zone_id = zone.id
        now = datetime.utcnow()
        
        # Debounce: Check if zone was triggered recently (within last 1 minute)
        if zone_id in self.last_trigger_check:
            last_check = self.last_trigger_check[zone_id]
            if now - last_check < timedelta(minutes=1):
                logger.debug(f"    ⏭️  Zone {zone_id} recently checked, skipping (debounce)")
                return False
        
        # Update last check time
        self.last_trigger_check[zone_id] = now
        
        logger.info(f"    🎯 ZONE TRIGGER: {zone.zone_type} zone #{zone_id} (confidence {zone.confidence}%) @ ${current_price:.2f}")
        logger.info(f"    📍 Zone range: ${float(zone.price_min):,.2f} - ${float(zone.price_max):,.2f}")
        
        # Execute zone trade (calls LLM for confirmation)
        success = await self._execute_zone_trade(zone, current_price, exchange, db)
        
        if success:
            # Mark zone as triggered (won't trigger again)
            zone.status = 'triggered'
            zone.last_triggered_at = now
            db.commit()
            
            logger.info(f"    ✅ Zone {zone_id} executed and marked as triggered")
            return True
        else:
            logger.warning(f"    ❌ Zone {zone_id} execution failed or LLM rejected")
        
        return False
    
    async def _execute_zone_trade(self, zone, current_price: float, exchange: str, db) -> bool:
        """
        Execute trade when zone is triggered
        
        Process:
        1. Fetch latest indicators (call bot.analyze_data())
        2. Call LLM for final confirmation
        3. If approved (action = BUY/SELL), call bot.setup_position()
        4. Log execution
        
        Returns:
            True if trade was executed, False otherwise
        """
        try:
            from core.tasks import initialize_bot
            from services.llm_integration import LLMIntegrationService
            from core import models
            
            logger.info(f"    🤖 Executing zone trade for subscription {zone.subscription_id}...")
            
            # Get subscription object
            subscription = db.query(models.Subscription).filter(
                models.Subscription.id == zone.subscription_id
            ).first()
            
            if not subscription:
                logger.error(f"    ❌ Subscription {zone.subscription_id} not found")
                return False
            
            # Initialize bot instance
            bot_instance = initialize_bot(subscription)
            if not bot_instance:
                logger.error(f"    ❌ Failed to initialize bot")
                return False
            
            # Fetch latest indicators
            logger.info("    📊 Fetching latest indicators...")
            multi_timeframe_data = bot_instance.crawl_data()
            analysis = bot_instance.analyze_data(multi_timeframe_data)
            
            if not analysis or 'multi_timeframe' not in analysis:
                logger.error("    ❌ Failed to get indicators")
                return False
            
            # Extract indicators
            # multi_timeframe directly contains timeframe data (e.g., '1h', '4h', '2h')
            multi_timeframe = analysis.get('multi_timeframe', {})
            indicators_analysis = multi_timeframe  # This IS the indicators by timeframe
            
            # Debug logging
            logger.info(f"    🔍 Available timeframes: {list(multi_timeframe.keys())}")
            if not multi_timeframe:
                logger.error(f"    ❌ No timeframe data found in analysis")
                return False
            
            # Call LLM for final confirmation
            llm_service = LLMIntegrationService()
            bot_db = db.query(models.Bot).filter(models.Bot.id == zone.bot_id).first()
            llm_model = getattr(bot_db, 'llm_provider', None) or 'openai' if bot_db else 'openai'
            
            logger.info(f"    🧠 Calling {llm_model} LLM for zone confirmation...")
            
            # Prepare zone data for confirmation
            zone_data = {
                'type': zone.zone_type,
                'price_min': float(zone.price_min),
                'price_max': float(zone.price_max),
                'confidence': zone.confidence,
                'reasoning': zone.reasoning or 'Pre-identified trigger zone'
            }
            
            # Call LLM with zone-specific confirmation prompt
            llm_result = await llm_service.confirm_zone_trade(
                zone=zone_data,
                current_price=current_price,
                indicators_analysis=indicators_analysis,
                symbol=zone.symbol,
                bot_id=zone.bot_id,
                model=llm_model
            )
            
            if 'error' in llm_result:
                logger.error(f"    ❌ LLM analysis failed: {llm_result['error']}")
                return False
            
            # Check LLM recommendation
            recommendation = llm_result.get('recommendation', {})
            action = recommendation.get('action', 'HOLD')
            reasoning = recommendation.get('reasoning', 'No reasoning provided')
            confidence = recommendation.get('confidence', 0)
            
            logger.info(f"    📝 LLM Recommendation: {action} (confidence: {confidence}%)")
            logger.info(f"    💭 Reasoning: {reasoning}")
            
            # If LLM says HOLD, don't execute
            if action == 'HOLD':
                logger.info(f"    ⏸️  LLM recommended HOLD, not executing")
                return False
            
            # Check if action matches zone type
            if action != zone.zone_type:
                logger.warning(f"    ⚠️  LLM action ({action}) doesn't match zone type ({zone.zone_type})")
                # Still execute if confidence is high
                if recommendation.get('confidence', 0) < 70:
                    return False
            
            # Execute trade via bot
            logger.info(f"    💰 Executing {action} trade at ${current_price:.2f}...")
            
            # Call bot's position setup method
            if hasattr(bot_instance, 'setup_position'):
                position_result = bot_instance.setup_position(llm_result, current_price)
                
                if position_result and position_result.get('status') == 'success':
                    logger.info(f"    ✅ Trade executed successfully")
                    return True
                else:
                    logger.error(f"    ❌ Trade execution failed: {position_result}")
                    return False
            else:
                logger.error(f"    ❌ Bot doesn't have setup_position method")
                return False
            
        except Exception as e:
            logger.error(f"    ❌ Zone trade execution error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


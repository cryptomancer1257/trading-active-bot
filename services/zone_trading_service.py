"""
Zone Trading Service

Main orchestrator for WebSocket-based zone trading
Coordinates WebSocket connections, zone monitoring, and trade execution
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class ZoneTradingService:
    """
    Main service that coordinates zone trading
    
    Responsibilities:
    - Manage WebSocket connections to exchanges
    - Monitor trigger zones
    - Execute trades when zones are triggered
    - Handle service lifecycle
    """
    
    def __init__(self):
        self.ws_manager = WebSocketManager()
        self.running = False
        self.reload_interval = 300  # Reload subscriptions every 5 minutes
        
    async def start(self):
        """
        Start zone trading service
        
        Process:
        1. Load active subscriptions with zone trading enabled
        2. Start WebSocket manager
        3. Monitor for new/removed subscriptions (reload periodically)
        """
        try:
            logger.info("=" * 70)
            logger.info("🚀 ZONE TRADING SERVICE STARTING")
            logger.info("=" * 70)
            
            self.running = True
            
            # Start WebSocket manager
            ws_task = asyncio.create_task(self.ws_manager.start())
            
            # Start subscription reload task
            reload_task = asyncio.create_task(self._reload_subscriptions_periodically())
            
            # Wait for both tasks
            await asyncio.gather(ws_task, reload_task)
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ Received shutdown signal")
            await self.stop()
        except Exception as e:
            logger.error(f"❌ Zone Trading Service error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self.stop()
    
    async def stop(self):
        """Stop zone trading service"""
        logger.info("🛑 Stopping Zone Trading Service...")
        self.running = False
        
        # Stop WebSocket manager
        await self.ws_manager.stop()
        
        logger.info("✅ Zone Trading Service stopped")
    
    async def _reload_subscriptions_periodically(self):
        """
        Periodically reload subscriptions to pick up new/removed bots
        
        NOTE: WebSocketManager already has built-in _reload_subscriptions_mapping()
        that runs every 5 minutes WITHOUT restarting connections.
        This task is just a keep-alive monitor.
        """
        while self.running:
            try:
                await asyncio.sleep(self.reload_interval)
                
                if not self.running:
                    break
                
                # Just log status - WebSocketManager handles reload internally
                logger.info("✅ Zone Trading Service running (WebSocket auto-reloading subscriptions)")
                
            except Exception as e:
                logger.error(f"Error in reload monitor: {e}")
                await asyncio.sleep(60)
    
    def get_active_trigger_zones(self, symbol: str, subscription_ids: List[int] = None) -> List:
        """
        Query active, non-expired zones from database
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            subscription_ids: Optional list of subscription IDs to filter by
            
        Returns:
            List of active TriggerZone objects
        """
        from core.database import SessionLocal
        from core import models
        
        db = SessionLocal()
        
        try:
            query = db.query(models.TriggerZone).filter(
                models.TriggerZone.symbol == symbol,
                models.TriggerZone.status == 'active',
                models.TriggerZone.expires_at > datetime.utcnow()
            )
            
            if subscription_ids:
                query = query.filter(models.TriggerZone.subscription_id.in_(subscription_ids))
            
            zones = query.all()
            return zones
            
        finally:
            db.close()
    
    async def check_zone_trigger(self, zone, current_price: float) -> bool:
        """
        Check if price is in zone and should trigger
        
        Args:
            zone: TriggerZone model instance
            current_price: Current market price
            
        Returns:
            True if zone should trigger, False otherwise
        """
        # Check if price is in zone range
        if not (float(zone.price_min) <= current_price <= float(zone.price_max)):
            return False
        
        # Check if zone was recently triggered (debounce)
        if zone.last_triggered_at:
            time_since_trigger = datetime.utcnow() - zone.last_triggered_at
            if time_since_trigger < timedelta(minutes=1):
                return False
        
        return True
    
    async def execute_zone_trade(self, zone, current_price: float):
        """
        Execute trade when zone is triggered
        
        This is a high-level wrapper that delegates to WebSocketManager
        
        Args:
            zone: TriggerZone model instance
            current_price: Current market price at trigger
            
        Returns:
            Result of trade execution
        """
        from core.database import SessionLocal
        
        db = SessionLocal()
        
        try:
            # The actual execution logic is in WebSocketManager._execute_zone_trade
            # This method can be used for manual triggers or testing
            success = await self.ws_manager._execute_zone_trade(zone, current_price, 'manual', db)
            
            if success:
                # Mark zone as triggered
                zone.status = 'triggered'
                zone.last_triggered_at = datetime.utcnow()
                db.commit()
            
            return success
            
        finally:
            db.close()
    
    def get_service_status(self) -> dict:
        """
        Get current status of zone trading service
        
        Returns:
            {
                'running': bool,
                'websocket_connected': bool,
                'active_subscriptions': int,
                'active_zones': int
            }
        """
        from core.database import SessionLocal
        from core import models
        
        db = SessionLocal()
        
        try:
            # Count active subscriptions with zone trading
            active_subs = db.query(models.Subscription).join(
                models.Bot,
                models.Subscription.bot_id == models.Bot.id
            ).filter(
                models.Subscription.status == 'active',
                models.Bot.zone_trading_enabled == True
            ).count()
            
            # Count active zones
            active_zones = db.query(models.TriggerZone).filter(
                models.TriggerZone.status == 'active',
                models.TriggerZone.expires_at > datetime.utcnow()
            ).count()
            
            return {
                'running': self.running,
                'websocket_connected': self.ws_manager.running,
                'active_subscriptions': active_subs,
                'active_zones': active_zones,
                'reload_interval': self.reload_interval
            }
            
        finally:
            db.close()
    
    async def cleanup_expired_zones(self):
        """
        Cleanup expired trigger zones
        Marks zones past their expiry time as 'expired'
        """
        from core.database import SessionLocal
        from core import models
        
        db = SessionLocal()
        
        try:
            expired_count = db.query(models.TriggerZone).filter(
                models.TriggerZone.status == 'active',
                models.TriggerZone.expires_at < datetime.utcnow()
            ).update({'status': 'expired'})
            
            db.commit()
            
            if expired_count > 0:
                logger.info(f"🧹 Cleaned up {expired_count} expired zones")
            
            return expired_count
            
        finally:
            db.close()
    
    async def get_zone_stats(self) -> dict:
        """
        Get statistics about trigger zones
        
        Returns:
            {
                'total_active': int,
                'buy_zones': int,
                'sell_zones': int,
                'triggered_today': int,
                'expired_today': int,
                'by_symbol': {symbol: count}
            }
        """
        from core.database import SessionLocal
        from core import models
        from sqlalchemy import func
        
        db = SessionLocal()
        
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Total active zones
            total_active = db.query(models.TriggerZone).filter(
                models.TriggerZone.status == 'active',
                models.TriggerZone.expires_at > now
            ).count()
            
            # Buy vs Sell zones
            buy_zones = db.query(models.TriggerZone).filter(
                models.TriggerZone.status == 'active',
                models.TriggerZone.zone_type == 'BUY',
                models.TriggerZone.expires_at > now
            ).count()
            
            sell_zones = db.query(models.TriggerZone).filter(
                models.TriggerZone.status == 'active',
                models.TriggerZone.zone_type == 'SELL',
                models.TriggerZone.expires_at > now
            ).count()
            
            # Triggered today
            triggered_today = db.query(models.TriggerZone).filter(
                models.TriggerZone.status == 'triggered',
                models.TriggerZone.last_triggered_at >= today_start
            ).count()
            
            # Expired today
            expired_today = db.query(models.TriggerZone).filter(
                models.TriggerZone.status == 'expired',
                models.TriggerZone.expires_at >= today_start,
                models.TriggerZone.expires_at < now
            ).count()
            
            # By symbol
            by_symbol = {}
            symbol_counts = db.query(
                models.TriggerZone.symbol,
                func.count(models.TriggerZone.id)
            ).filter(
                models.TriggerZone.status == 'active',
                models.TriggerZone.expires_at > now
            ).group_by(models.TriggerZone.symbol).all()
            
            for symbol, count in symbol_counts:
                by_symbol[symbol] = count
            
            return {
                'total_active': total_active,
                'buy_zones': buy_zones,
                'sell_zones': sell_zones,
                'triggered_today': triggered_today,
                'expired_today': expired_today,
                'by_symbol': by_symbol
            }
            
        finally:
            db.close()


async def main():
    """
    Main entry point for zone trading service
    Can be run standalone for testing
    """
    service = ZoneTradingService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Shutdown requested")
    finally:
        await service.stop()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run service
    asyncio.run(main())


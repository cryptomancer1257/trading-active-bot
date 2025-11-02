#!/usr/bin/env python3
"""
WebSocket Service Startup Script

Runs the WebSocket-based Zone Trading Service as a standalone process
Monitors real-time prices and triggers zone-based trades
"""

import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.zone_trading_service import ZoneTradingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/websocket_service.log')
    ]
)

logger = logging.getLogger(__name__)


def check_prerequisites():
    """Check if all prerequisites are met before starting"""
    logger.info("🔍 Checking prerequisites...")
    
    # Check database connection
    try:
        from core.database import SessionLocal
        db = SessionLocal()
        db.close()
        logger.info("  ✅ Database connection OK")
    except Exception as e:
        logger.error(f"  ❌ Database connection failed: {e}")
        return False
    
    # Check if TriggerZone table exists
    try:
        from core import models
        db = SessionLocal()
        db.query(models.TriggerZone).limit(1).all()
        db.close()
        logger.info("  ✅ TriggerZone table exists")
    except Exception as e:
        logger.error(f"  ❌ TriggerZone table not found: {e}")
        logger.error("     Run migration: python migrations/versions/062_add_trigger_zones_table.py")
        return False
    
    # Check if zone_trading_enabled column exists
    try:
        db = SessionLocal()
        bot = db.query(models.Bot).first()
        if bot:
            _ = bot.zone_trading_enabled
        db.close()
        logger.info("  ✅ zone_trading_enabled column exists")
    except Exception as e:
        logger.error(f"  ❌ zone_trading_enabled column not found: {e}")
        logger.error("     Run migration: python migrations/versions/063_add_zone_trading_columns.py")
        return False
    
    logger.info("✅ All prerequisites met\n")
    return True


async def main():
    """Main entry point for WebSocket service"""
    
    # Print banner
    print("=" * 70)
    print("🚀 WEBSOCKET ZONE TRADING SERVICE")
    print("=" * 70)
    print(f"📍 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔗 Database: {os.getenv('DB_NAME', 'bot_marketplace')}")
    print(f"📊 Redis: {os.getenv('REDIS_URL', 'redis://localhost:6379/0')}")
    print("=" * 70)
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("❌ Prerequisites check failed. Exiting...")
        sys.exit(1)
    
    # Create and start zone trading service
    service = ZoneTradingService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Shutdown signal received")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        await service.stop()
        logger.info("👋 WebSocket service terminated")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


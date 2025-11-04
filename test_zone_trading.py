#!/usr/bin/env python3
"""
Script to test Zone Trading functionality

This script helps you:
1. Enable zone trading for a bot
2. Manually trigger zone finding
3. Create test zones
4. Manually trigger zone execution
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core import models
from core.tasks import find_trigger_zones_task
from datetime import datetime, timedelta
from decimal import Decimal


def enable_zone_trading_for_bot(bot_id: int):
    """Enable zone trading for a specific bot"""
    db = SessionLocal()
    
    try:
        bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
        if not bot:
            print(f"❌ Bot {bot_id} not found")
            return False
        
        bot.zone_trading_enabled = True
        bot.zone_update_frequency = 60
        db.commit()
        
        print(f"✅ Enabled zone trading for bot {bot_id} ({bot.name})")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def get_active_subscription(bot_id: int):
    """Get first active subscription for a bot"""
    db = SessionLocal()
    
    try:
        subscription = db.query(models.Subscription).filter(
            models.Subscription.bot_id == bot_id,
            models.Subscription.status == 'active'
        ).first()
        
        if subscription:
            print(f"✅ Found active subscription: {subscription.id} for {subscription.trading_pair}")
            return subscription
        else:
            print(f"⚠️  No active subscription found for bot {bot_id}")
            return None
            
    finally:
        db.close()


def manually_trigger_zone_finding(subscription_id: int):
    """Manually trigger the zone finding Celery task"""
    print(f"\n🎯 Triggering zone finding for subscription {subscription_id}...")
    
    try:
        # Call the task synchronously for testing
        result = find_trigger_zones_task(subscription_id)
        
        print(f"✅ Zone finding completed:")
        print(f"   Status: {result.get('status')}")
        print(f"   Zones found: {result.get('zones_found', 0)}")
        print(f"   Zones expired: {result.get('zones_expired', 0)}")
        
        if result.get('zones'):
            print(f"\n📊 Zones created:")
            for zone in result['zones']:
                print(f"   • {zone['type']} zone: ${zone['range'][0]:,.2f} - ${zone['range'][1]:,.2f} (confidence: {zone['confidence']}%)")
        
        if result.get('reasoning'):
            print(f"\n💭 Reasoning: {result['reasoning']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error triggering zone finding: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_test_zone(bot_id: int, subscription_id: int, symbol: str = "BTCUSDT"):
    """Create a test trigger zone manually using REAL current price from exchange"""
    db = SessionLocal()
    
    try:
        # Fetch REAL current price from testnet
        subscription = db.query(models.Subscription).filter_by(id=subscription_id).first()
        if not subscription:
            print(f"❌ Subscription {subscription_id} not found")
            return None
        
        bot_db = subscription.bot
        if not bot_db:
            print(f"❌ Bot not found for subscription {subscription_id}")
            return None
        
        print(f"🔄 Fetching real price from {bot_db.exchange_type} testnet...")
        
        # Fetch current price directly from Bybit testnet API
        import requests
        try:
            # Bybit testnet ticker endpoint
            url = "https://api-testnet.bybit.com/v5/market/tickers"
            params = {
                "category": "linear",
                "symbol": symbol.replace("/", "")  # Remove slash if present
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('retCode') != 0:
                print(f"❌ Bybit API error: {data.get('retMsg')}")
                return None
            
            ticker_list = data.get('result', {}).get('list', [])
            if not ticker_list:
                print(f"❌ No ticker data found for {symbol}")
                return None
            
            current_price = float(ticker_list[0].get('lastPrice', 0))
            
        except Exception as e:
            print(f"❌ Error fetching price from Bybit API: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        if current_price <= 0:
            print(f"❌ Invalid price from exchange: {current_price}")
            return None
        
        print(f"✅ Real testnet price: ${current_price:,.2f}")
        
        # Create zone around current price (±5% range for testing)
        range_percent = 0.05  # 5%
        price_min = current_price * (1 - range_percent)
        price_max = current_price * (1 + range_percent)
        
        zone = models.TriggerZone(
            bot_id=bot_id,
            subscription_id=subscription_id,
            symbol=symbol,
            zone_type='BUY',
            price_min=Decimal(str(price_min)),
            price_max=Decimal(str(price_max)),
            confidence=85,
            reasoning=f'Test zone created around real testnet price ${current_price:,.2f}',
            status='active',
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        db.add(zone)
        db.commit()
        
        print(f"\n✅ Test zone created with REAL price:")
        print(f"   Zone ID: {zone.id}")
        print(f"   Type: {zone.zone_type}")
        print(f"   Symbol: {zone.symbol}")
        print(f"   Current Price: ${current_price:,.2f}")
        print(f"   Zone Range: ${float(zone.price_min):,.2f} - ${float(zone.price_max):,.2f}")
        print(f"   Coverage: ±{range_percent*100}% of current price")
        print(f"   Expires: {zone.expires_at}")
        
        return zone
        
    except Exception as e:
        print(f"❌ Error creating test zone: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def list_active_zones(bot_id: int):
    """List all active zones for a bot"""
    db = SessionLocal()
    
    try:
        zones = db.query(models.TriggerZone).filter(
            models.TriggerZone.bot_id == bot_id,
            models.TriggerZone.status == 'active',
            models.TriggerZone.expires_at > datetime.utcnow()
        ).order_by(models.TriggerZone.created_at.desc()).all()
        
        if not zones:
            print(f"⚠️  No active zones found for bot {bot_id}")
            return []
        
        print(f"\n📊 Active zones for bot {bot_id}:")
        print(f"   Total: {len(zones)} zones\n")
        
        for zone in zones:
            print(f"   Zone #{zone.id}:")
            print(f"      Type: {zone.zone_type}")
            print(f"      Symbol: {zone.symbol}")
            print(f"      Range: ${float(zone.price_min):,.2f} - ${float(zone.price_max):,.2f}")
            print(f"      Confidence: {zone.confidence}%")
            print(f"      Status: {zone.status}")
            print(f"      Expires: {zone.expires_at}")
            if zone.last_triggered_at:
                print(f"      Last triggered: {zone.last_triggered_at}")
            print()
        
        return zones
        
    finally:
        db.close()


def simulate_price_in_zone(zone_id: int, price: float):
    """
    Simulate a price update that triggers a zone
    
    This simulates what happens when WebSocket receives a price update
    """
    print(f"\n💹 Simulating price update: ${price:,.2f}")
    
    db = SessionLocal()
    
    try:
        zone = db.query(models.TriggerZone).filter(
            models.TriggerZone.id == zone_id
        ).first()
        
        if not zone:
            print(f"❌ Zone {zone_id} not found")
            return
        
        if zone.status != 'active':
            print(f"⚠️  Zone {zone_id} is not active (status: {zone.status})")
            return
        
        # Check if price is in zone
        if not (float(zone.price_min) <= price <= float(zone.price_max)):
            print(f"❌ Price ${price:,.2f} is NOT in zone range (${float(zone.price_min):,.2f} - ${float(zone.price_max):,.2f})")
            return
        
        print(f"✅ Price ${price:,.2f} is IN zone range!")
        print(f"   Zone: {zone.zone_type} zone #{zone.id}")
        print(f"   Range: ${float(zone.price_min):,.2f} - ${float(zone.price_max):,.2f}")
        
        # Note: Actual trade execution happens in WebSocketManager._execute_zone_trade()
        # This just simulates the check
        print(f"\n⚠️  To actually trigger the trade, the WebSocket service must be running")
        print(f"   and receive a real price update from Binance/Bybit")
        print(f"   OR you can call the execute method directly from code")
        
    finally:
        db.close()


async def execute_zone_trade(zone_id: int):
    """Execute trade for a specific zone with current real price"""
    db = SessionLocal()
    
    try:
        # Get zone
        zone = db.query(models.TriggerZone).filter_by(id=zone_id).first()
        if not zone:
            print(f"❌ Zone {zone_id} not found")
            return
        
        print(f"\n🎯 Executing trade for Zone #{zone_id}:")
        print(f"   Type: {zone.zone_type}")
        print(f"   Symbol: {zone.symbol}")
        print(f"   Range: ${float(zone.price_min):,.2f} - ${float(zone.price_max):,.2f}")
        print(f"   Status: {zone.status}")
        
        if zone.status != 'active':
            print(f"⚠️  Zone is not active (status: {zone.status})")
            return
        
        # Fetch current real price from Bybit testnet
        import requests
        print(f"\n🔄 Fetching current price from Bybit testnet...")
        
        try:
            url = "https://api-testnet.bybit.com/v5/market/tickers"
            params = {
                "category": "linear",
                "symbol": zone.symbol.replace("/", "")
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('retCode') != 0:
                print(f"❌ Bybit API error: {data.get('retMsg')}")
                return
            
            ticker_list = data.get('result', {}).get('list', [])
            if not ticker_list:
                print(f"❌ No ticker data found for {zone.symbol}")
                return
            
            current_price = float(ticker_list[0].get('lastPrice', 0))
            print(f"✅ Current testnet price: ${current_price:,.2f}")
            
        except Exception as e:
            print(f"❌ Error fetching price: {e}")
            return
        
        # Check if price is in zone
        if not (float(zone.price_min) <= current_price <= float(zone.price_max)):
            print(f"\n⚠️  Price ${current_price:,.2f} is NOT in zone range!")
            print(f"   Zone Range: ${float(zone.price_min):,.2f} - ${float(zone.price_max):,.2f}")
            print(f"\n💡 You can either:")
            print(f"   1. Wait for price to enter zone")
            print(f"   2. Create a new zone around current price: python test_zone_trading.py create {zone.bot_id} {zone.subscription_id}")
            return
        
        print(f"✅ Price is IN zone range!")
        
        # Import WebSocket manager and execute trade
        print(f"\n🚀 Executing trade via WebSocket manager...")
        
        from services.websocket_manager import WebSocketManager
        
        # Get subscription to determine exchange
        subscription = db.query(models.Subscription).filter_by(id=zone.subscription_id).first()
        if not subscription:
            print(f"❌ Subscription {zone.subscription_id} not found")
            return
        
        # Determine exchange type
        exchange = subscription.bot.exchange_type.value if hasattr(subscription.bot.exchange_type, 'value') else str(subscription.bot.exchange_type).lower()
        
        # Create manager instance
        manager = WebSocketManager()
        
        print(f"🤖 Calling LLM for trade confirmation...")
        print(f"   Exchange: {exchange}")
        
        # Call the execute method directly
        success = await manager._execute_zone_trade(
            zone=zone,
            current_price=current_price,
            exchange=exchange,
            db=db
        )
        
        print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Trade execution {'completed' if success else 'failed'}")
        
        # Refresh zone to see updates
        db.refresh(zone)
        print(f"\n📊 Zone status after execution:")
        print(f"   Status: {zone.status}")
        print(f"   Last triggered: {zone.last_triggered_at}")
        
        print(f"\n✅ Trade execution completed!")
        print(f"\n📝 Check results:")
        print(f"   1. Database - transactions table")
        print(f"   2. Exchange - open positions")
        print(f"   3. Logs - websocket.log or terminal output")
        
    except Exception as e:
        print(f"❌ Error executing trade: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """Main test menu"""
    print("=" * 70)
    print("🧪 ZONE TRADING TEST SCRIPT")
    print("=" * 70)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python test_zone_trading.py <command> [args]")
        print("\nCommands:")
        print("  1. enable <bot_id>                  - Enable zone trading for bot")
        print("  2. trigger <bot_id>                 - Trigger zone finding for bot")
        print("  3. find <subscription_id>           - Manually trigger zone finding (by sub ID)")
        print("  4. create <bot_id> <sub_id>         - Create test zone")
        print("  5. list <bot_id>                    - List active zones")
        print("  6. execute <zone_id>                - Execute trade for zone (TEST)")
        print("  7. simulate <zone_id> <price>       - Simulate price trigger (info only)")
        print("  8. full-test <bot_id>               - Run full test sequence")
        print("\nExamples:")
        print("  python test_zone_trading.py trigger 140")
        print("  python test_zone_trading.py execute 8")
        print("  python test_zone_trading.py full-test 140")
        return
    
    command = sys.argv[1]
    
    if command == "enable":
        if len(sys.argv) < 3:
            print("❌ Usage: python test_zone_trading.py enable <bot_id>")
            return
        bot_id = int(sys.argv[2])
        enable_zone_trading_for_bot(bot_id)
    
    elif command == "trigger":
        # Convenience command: trigger by bot_id (auto-finds active subscription)
        if len(sys.argv) < 3:
            print("❌ Usage: python test_zone_trading.py trigger <bot_id>")
            return
        bot_id = int(sys.argv[2])
        subscription = get_active_subscription(bot_id)
        if subscription:
            manually_trigger_zone_finding(subscription.id)
        
    elif command == "find":
        # Direct command: trigger by subscription_id
        if len(sys.argv) < 3:
            print("❌ Usage: python test_zone_trading.py find <subscription_id>")
            return
        subscription_id = int(sys.argv[2])
        manually_trigger_zone_finding(subscription_id)
        
    elif command == "create":
        if len(sys.argv) < 4:
            print("❌ Usage: python test_zone_trading.py create <bot_id> <subscription_id>")
            return
        bot_id = int(sys.argv[2])
        subscription_id = int(sys.argv[3])
        create_test_zone(bot_id, subscription_id)
        
    elif command == "list":
        if len(sys.argv) < 3:
            print("❌ Usage: python test_zone_trading.py list <bot_id>")
            return
        bot_id = int(sys.argv[2])
        list_active_zones(bot_id)
    
    elif command == "execute":
        if len(sys.argv) < 3:
            print("❌ Usage: python test_zone_trading.py execute <zone_id>")
            return
        zone_id = int(sys.argv[2])
        asyncio.run(execute_zone_trade(zone_id))
        
    elif command == "simulate":
        if len(sys.argv) < 4:
            print("❌ Usage: python test_zone_trading.py simulate <zone_id> <price>")
            return
        zone_id = int(sys.argv[2])
        price = float(sys.argv[3])
        simulate_price_in_zone(zone_id, price)
        
    elif command == "full-test":
        if len(sys.argv) < 3:
            print("❌ Usage: python test_zone_trading.py full-test <bot_id>")
            return
        bot_id = int(sys.argv[2])
        
        print(f"\n🚀 Running full test for bot {bot_id}...\n")
        
        # Step 1: Enable zone trading
        print("Step 1: Enabling zone trading...")
        if not enable_zone_trading_for_bot(bot_id):
            return
        
        # Step 2: Get subscription
        print("\nStep 2: Finding active subscription...")
        subscription = get_active_subscription(bot_id)
        if not subscription:
            print("❌ Cannot proceed without active subscription")
            return
        
        # Step 3: Trigger zone finding
        print("\nStep 3: Triggering zone finding...")
        result = manually_trigger_zone_finding(subscription.id)
        
        # Step 4: List zones
        print("\nStep 4: Listing created zones...")
        zones = list_active_zones(bot_id)
        
        if zones:
            # Step 5: Simulate price trigger for first zone
            print("\nStep 5: Simulating price trigger...")
            first_zone = zones[0]
            mid_price = (float(first_zone.price_min) + float(first_zone.price_max)) / 2
            simulate_price_in_zone(first_zone.id, mid_price)
        
        print("\n✅ Full test completed!")
        print("\n📝 Next steps:")
        print("   1. Start WebSocket service: python run_websocket_service.py")
        print("   2. Monitor logs for zone triggers")
        print("   3. Check transactions table for executed trades")
        
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()


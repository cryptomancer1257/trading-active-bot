#!/usr/bin/env python3
"""
Debug enum issue
"""

from sqlalchemy import text
from core.database import engine
from core import models

def debug_enum():
    """Debug enum values"""
    print("🔍 Debugging enum issue...")
    
    # Check Python enum values
    print("\n📋 Python enum values:")
    print(f"   NetworkType.TESTNET = '{models.NetworkType.TESTNET.value}'")
    print(f"   NetworkType.MAINNET = '{models.NetworkType.MAINNET.value}'")
    print(f"   TradeMode.SPOT = '{models.TradeMode.SPOT.value}'")
    print(f"   TradeMode.MARGIN = '{models.TradeMode.MARGIN.value}'")
    print(f"   TradeMode.FUTURES = '{models.TradeMode.FUTURES.value}'")
    
    # Check database schema
    try:
        with engine.connect() as connection:
            print("\n📋 Database enum constraints:")
            result = connection.execute(text("""
                SELECT COLUMN_NAME, COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'subscriptions' 
                AND COLUMN_NAME IN ('network_type', 'trade_mode')
            """))
            
            for row in result:
                print(f"   {row[0]}: {row[1]}")
                
            # Try to insert test values
            print("\n🧪 Testing direct insert...")
            
            # Test network_type values
            for test_val in ['testnet', 'mainnet', 'TESTNET', 'MAINNET']:
                try:
                    connection.execute(text(f"SELECT '{test_val}' WHERE '{test_val}' IN ('testnet', 'mainnet')"))
                    print(f"   ✅ '{test_val}' is valid for network_type")
                except Exception as e:
                    print(f"   ❌ '{test_val}' failed: {e}")
            
            # Test trade_mode values  
            for test_val in ['Spot', 'Margin', 'Futures', 'SPOT', 'MARGIN', 'FUTURES']:
                try:
                    connection.execute(text(f"SELECT '{test_val}' WHERE '{test_val}' IN ('Spot', 'Margin', 'Futures')"))
                    print(f"   ✅ '{test_val}' is valid for trade_mode")
                except Exception as e:
                    print(f"   ❌ '{test_val}' failed: {e}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_enum()

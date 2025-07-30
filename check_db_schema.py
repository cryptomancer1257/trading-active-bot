#!/usr/bin/env python3
"""
Check database schema for subscriptions table
"""

from sqlalchemy import text
from core.database import engine

def check_schema():
    """Check the actual database schema"""
    try:
        with engine.connect() as connection:
            # Check subscriptions table structure
            print("📋 Checking subscriptions table structure...")
            result = connection.execute(text("DESCRIBE subscriptions"))
            
            for row in result:
                field_name = row[0]
                field_type = row[1]
                if field_name in ['network_type', 'trade_mode']:
                    print(f"   {field_name}: {field_type}")
            
            # Check specific enum values
            print("\n📋 Checking enum constraints...")
            result = connection.execute(text("""
                SELECT COLUMN_NAME, COLUMN_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'subscriptions' 
                AND COLUMN_NAME IN ('network_type', 'trade_mode')
            """))
            
            for row in result:
                print(f"   {row[0]}: {row[1]}")
                
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == "__main__":
    check_schema()

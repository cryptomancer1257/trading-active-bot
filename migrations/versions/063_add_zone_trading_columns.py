#!/usr/bin/env python3
"""
Migration 063: Add zone trading configuration columns to bots table
Allows bots to enable WebSocket-based zone trading
"""

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            AND COLUMN_NAME = %s
    """, (table_name, column_name))
    return cursor.fetchone()[0] > 0

def migrate(connection):
    """Run migration"""
    cursor = connection.cursor()
    
    try:
        print("📊 Starting Zone Trading Configuration Migration...")
        
        # 1. Add zone_trading_enabled column
        if not column_exists(cursor, 'bots', 'zone_trading_enabled'):
            print("  1. Adding zone_trading_enabled...")
            cursor.execute("""
                ALTER TABLE bots 
                ADD COLUMN zone_trading_enabled BOOLEAN DEFAULT FALSE 
                COMMENT 'Enable WebSocket-based zone trading'
            """)
        else:
            print("  1. ⏭️  zone_trading_enabled already exists")
        
        # 2. Add zone_update_frequency column
        if not column_exists(cursor, 'bots', 'zone_update_frequency'):
            print("  2. Adding zone_update_frequency...")
            cursor.execute("""
                ALTER TABLE bots 
                ADD COLUMN zone_update_frequency INT DEFAULT 60 
                COMMENT 'How often to recalculate zones (in minutes)'
            """)
        else:
            print("  2. ⏭️  zone_update_frequency already exists")
        
        connection.commit()
        print("✅ Migration 063 completed successfully!")
        print("\n📊 Zone Trading Feature Summary:")
        print("   • Bots can now enable WebSocket-based zone trading")
        print("   • Zones auto-refresh every 60 minutes by default")
        print("   • Celery task finds trigger zones using LLM")
        print("   • WebSocket service monitors prices and executes trades")
        print("\n🚀 Next Steps:")
        print("   1. Restart backend server to load new model columns")
        print("   2. Start WebSocket service: python run_websocket_service.py")
        print("   3. Enable feature in bot configuration")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()

def rollback(connection):
    """Rollback migration"""
    cursor = connection.cursor()
    
    try:
        print("🔄 Rolling back Zone Trading Configuration Migration...")
        
        # Remove columns
        print("  1. Dropping zone_update_frequency column...")
        cursor.execute("ALTER TABLE bots DROP COLUMN IF EXISTS zone_update_frequency")
        
        print("  2. Dropping zone_trading_enabled column...")
        cursor.execute("ALTER TABLE bots DROP COLUMN IF EXISTS zone_trading_enabled")
        
        connection.commit()
        print("✅ Migration 063 rolled back successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()

if __name__ == "__main__":
    """
    Run migration standalone for testing
    Usage:
        python migrations/versions/063_add_zone_trading_columns.py
        python migrations/versions/063_add_zone_trading_columns.py rollback
    """
    import pymysql
    import sys
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Connect to database
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '3306')),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'bot_marketplace'),
        autocommit=False
    )
    
    try:
        # Check if rollback requested
        if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
            rollback(conn)
        else:
            migrate(conn)
    except Exception as e:
        print(f"\n💥 Error: {e}")
        sys.exit(1)
    finally:
        conn.close()


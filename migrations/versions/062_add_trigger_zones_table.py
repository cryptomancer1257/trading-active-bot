#!/usr/bin/env python3
"""
Migration 062: Add trigger_zones table for WebSocket-based zone trading
Allows bots to identify and monitor price zones for automated trade execution
"""

def table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
    """, (table_name,))
    return cursor.fetchone()[0] > 0

def index_exists(cursor, table_name, index_name):
    """Check if an index exists in a table"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            AND INDEX_NAME = %s
    """, (table_name, index_name))
    return cursor.fetchone()[0] > 0

def migrate(connection):
    """Run migration"""
    cursor = connection.cursor()
    
    try:
        print("📊 Starting Trigger Zones Table Migration...")
        
        # 1. Create trigger_zones table
        if not table_exists(cursor, 'trigger_zones'):
            print("  1. Creating trigger_zones table...")
            cursor.execute("""
                CREATE TABLE trigger_zones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    bot_id INT NOT NULL,
                    subscription_id INT NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    zone_type VARCHAR(10) NOT NULL COMMENT 'BUY or SELL',
                    price_min DECIMAL(20, 8) NOT NULL,
                    price_max DECIMAL(20, 8) NOT NULL,
                    confidence INT NOT NULL,
                    reasoning TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active, triggered, expired',
                    last_triggered_at DATETIME NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL COMMENT 'Auto-expire after 1 hour',
                    
                    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
                    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
                    
                    INDEX idx_trigger_zones_bot_id (bot_id),
                    INDEX idx_trigger_zones_subscription_id (subscription_id),
                    INDEX idx_trigger_zones_symbol (symbol),
                    INDEX idx_trigger_zones_status (status),
                    INDEX idx_trigger_zones_bot_symbol_status (bot_id, symbol, status),
                    INDEX idx_trigger_zones_expires_at (expires_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                  COMMENT='Trigger zones for WebSocket-based zone trading';
            """)
            print("     ✅ trigger_zones table created")
        else:
            print("  1. ⏭️  trigger_zones table already exists")
        
        connection.commit()
        print("✅ Migration 062 completed successfully!")
        print("\n📊 Trigger Zones Feature Summary:")
        print("   • New table for storing BUY/SELL trigger zones")
        print("   • WebSocket service will monitor prices and trigger trades")
        print("   • Zones auto-expire after 1 hour")
        print("   • Optimized indexes for fast zone lookups by bot and symbol")
        print("\n🚀 Next Steps:")
        print("   1. Restart backend server to load new TriggerZone model")
        print("   2. Start WebSocket service: python run_websocket_service.py")
        print("   3. Enable Celery beat for zone finder task")
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
        print("🔄 Rolling back Trigger Zones Table Migration...")
        
        # Drop trigger_zones table (cascade will handle foreign keys)
        print("  1. Dropping trigger_zones table...")
        cursor.execute("DROP TABLE IF EXISTS trigger_zones")
        
        connection.commit()
        print("✅ Migration 062 rolled back successfully!")
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
        python migrations/versions/062_add_trigger_zones_table.py
        python migrations/versions/062_add_trigger_zones_table.py rollback
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


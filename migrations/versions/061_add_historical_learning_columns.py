#!/usr/bin/env python3
"""
Migration 061: Add historical learning configuration columns to bots table
Allows bots to learn from past transactions to improve decision-making
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
        print("🧠 Starting Historical Learning Configuration Migration...")
        
        # 1. Add historical_learning_enabled column
        if not column_exists(cursor, 'bots', 'historical_learning_enabled'):
            print("  1. Adding historical_learning_enabled...")
            cursor.execute("""
                ALTER TABLE bots 
                ADD COLUMN historical_learning_enabled BOOLEAN DEFAULT FALSE 
                COMMENT 'Enable LLM to learn from past transactions'
            """)
        else:
            print("  1. ⏭️  historical_learning_enabled already exists")
        
        # 2. Add historical_transaction_limit column
        if not column_exists(cursor, 'bots', 'historical_transaction_limit'):
            print("  2. Adding historical_transaction_limit...")
            cursor.execute("""
                ALTER TABLE bots 
                ADD COLUMN historical_transaction_limit INT DEFAULT 25 
                COMMENT 'Number of historical transactions to analyze (10, 25, or 50)'
            """)
        else:
            print("  2. ⏭️  historical_transaction_limit already exists")
        
        # 3. Add include_failed_trades column
        if not column_exists(cursor, 'bots', 'include_failed_trades'):
            print("  3. Adding include_failed_trades...")
            cursor.execute("""
                ALTER TABLE bots 
                ADD COLUMN include_failed_trades BOOLEAN DEFAULT TRUE 
                COMMENT 'Include losing trades for learning'
            """)
        else:
            print("  3. ⏭️  include_failed_trades already exists")
        
        # 4. Add learning_mode column
        if not column_exists(cursor, 'bots', 'learning_mode'):
            print("  4. Adding learning_mode...")
            cursor.execute("""
                ALTER TABLE bots 
                ADD COLUMN learning_mode VARCHAR(20) DEFAULT 'recent' 
                COMMENT 'Learning strategy: recent, best_performance, or mixed'
            """)
        else:
            print("  4. ⏭️  learning_mode already exists")
        
        # 5. Add constraint for historical_transaction_limit
        print("  5. Adding check constraint for transaction_limit...")
        cursor.execute("""
            ALTER TABLE bots 
            ADD CONSTRAINT chk_historical_transaction_limit 
            CHECK (historical_transaction_limit IN (10, 25, 50))
        """)
        print("     (Note: If constraint already exists, MySQL will skip)")
        
        # 6. Add constraint for learning_mode
        print("  6. Adding check constraint for learning_mode...")
        cursor.execute("""
            ALTER TABLE bots 
            ADD CONSTRAINT chk_learning_mode 
            CHECK (learning_mode IN ('recent', 'best_performance', 'mixed'))
        """)
        print("     (Note: If constraint already exists, MySQL will skip)")
        
        # 7. Add index on transactions table for faster queries
        if not index_exists(cursor, 'transactions', 'idx_transactions_subscription_exit'):
            print("  7. Adding index on transactions for historical queries...")
            cursor.execute("""
                CREATE INDEX idx_transactions_subscription_exit 
                ON transactions(subscription_id, exit_price, status, exit_time DESC)
            """)
        else:
            print("  7. ⏭️  Index idx_transactions_subscription_exit already exists")
        
        # 8. Add index on subscriptions for bot_id lookups
        if not index_exists(cursor, 'subscriptions', 'idx_subscriptions_bot_id'):
            print("  8. Adding index on subscriptions for bot lookups...")
            cursor.execute("""
                CREATE INDEX idx_subscriptions_bot_id 
                ON subscriptions(bot_id, status)
            """)
        else:
            print("  8. ⏭️  Index idx_subscriptions_bot_id already exists")
        
        connection.commit()
        print("✅ Migration 061 completed successfully!")
        print("\n📊 Historical Learning Feature Summary:")
        print("   • Bots can now learn from past transaction performance")
        print("   • Configurable transaction limit: 10, 25, or 50 transactions")
        print("   • Learning modes: recent, best_performance, mixed")
        print("   • Optimized indexes for fast historical data queries")
        print("\n🚀 Next Steps:")
        print("   1. Restart backend server to load new model columns")
        print("   2. Enable feature in UI: Strategies tab → Historical Learning")
        print("   3. Bots will automatically pass historical data to LLM")
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
        print("🔄 Rolling back Historical Learning Configuration Migration...")
        
        # Remove indexes first
        print("  1. Dropping index idx_subscriptions_bot_id...")
        cursor.execute("DROP INDEX IF EXISTS idx_subscriptions_bot_id ON subscriptions")
        
        print("  2. Dropping index idx_transactions_subscription_exit...")
        cursor.execute("DROP INDEX IF EXISTS idx_transactions_subscription_exit ON transactions")
        
        # Remove constraints
        print("  3. Dropping constraints...")
        cursor.execute("ALTER TABLE bots DROP CONSTRAINT IF EXISTS chk_learning_mode")
        cursor.execute("ALTER TABLE bots DROP CONSTRAINT IF EXISTS chk_historical_transaction_limit")
        
        # Remove columns
        print("  4. Dropping learning_mode column...")
        cursor.execute("ALTER TABLE bots DROP COLUMN IF EXISTS learning_mode")
        
        print("  5. Dropping include_failed_trades column...")
        cursor.execute("ALTER TABLE bots DROP COLUMN IF EXISTS include_failed_trades")
        
        print("  6. Dropping historical_transaction_limit column...")
        cursor.execute("ALTER TABLE bots DROP COLUMN IF EXISTS historical_transaction_limit")
        
        print("  7. Dropping historical_learning_enabled column...")
        cursor.execute("ALTER TABLE bots DROP COLUMN IF EXISTS historical_learning_enabled")
        
        connection.commit()
        print("✅ Migration 061 rolled back successfully!")
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
        python migrations/versions/061_add_historical_learning_columns.py
        python migrations/versions/061_add_historical_learning_columns.py rollback
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


#!/usr/bin/env python3
"""
Migration 027: Enhance transactions table for comprehensive performance tracking
This is a Python-based migration to handle conditional column additions
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

def constraint_exists(cursor, table_name, constraint_name):
    """Check if a foreign key constraint exists"""
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            AND CONSTRAINT_NAME = %s
    """, (table_name, constraint_name))
    return cursor.fetchone()[0] > 0

def migrate(connection):
    """Run migration"""
    cursor = connection.cursor()
    
    try:
        print("📊 Starting Transaction Table Enhancement Migration...")
        
        # 1. Make user_id nullable
        print("  1. Making user_id nullable...")
        cursor.execute("ALTER TABLE transactions MODIFY COLUMN user_id INT NULL")
        
        # 2. Add user_principal_id
        if not column_exists(cursor, 'transactions', 'user_principal_id'):
            print("  2. Adding user_principal_id...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN user_principal_id VARCHAR(255) NULL AFTER user_id")
        else:
            print("  2. ⏭️  user_principal_id already exists")
        
        # 3. Add prompt_id
        if not column_exists(cursor, 'transactions', 'prompt_id'):
            print("  3. Adding prompt_id...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN prompt_id INT NULL AFTER subscription_id")
        else:
            print("  3. ⏭️  prompt_id already exists")
        
        # 4. Add entry_time
        if not column_exists(cursor, 'transactions', 'entry_time'):
            print("  4. Adding entry_time...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN entry_time DATETIME NULL AFTER entry_price")
        else:
            print("  4. ⏭️  entry_time already exists")
        
        # 5. Add position_side
        if not column_exists(cursor, 'transactions', 'position_side'):
            print("  5. Adding position_side...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN position_side ENUM('LONG', 'SHORT') NULL AFTER action")
        else:
            print("  5. ⏭️  position_side already exists")
        
        # 6-8. Add exit information
        if not column_exists(cursor, 'transactions', 'exit_price'):
            print("  6. Adding exit_price...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN exit_price DECIMAL(20, 8) NULL AFTER take_profit")
        else:
            print("  6. ⏭️  exit_price already exists")
            
        if not column_exists(cursor, 'transactions', 'exit_time'):
            print("  7. Adding exit_time...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN exit_time DATETIME NULL AFTER exit_price")
        else:
            print("  7. ⏭️  exit_time already exists")
            
        if not column_exists(cursor, 'transactions', 'exit_reason'):
            print("  8. Adding exit_reason...")
            cursor.execute("""
                ALTER TABLE transactions ADD COLUMN exit_reason 
                ENUM('TP_HIT', 'SL_HIT', 'MANUAL', 'TIMEOUT', 'LIQUIDATION', 'TRAILING_STOP') 
                NULL AFTER exit_time
            """)
        else:
            print("  8. ⏭️  exit_reason already exists")
        
        # 9-13. Add P&L fields
        if not column_exists(cursor, 'transactions', 'pnl_usd'):
            print("  9. Adding pnl_usd...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN pnl_usd DECIMAL(20, 8) NULL AFTER exit_reason")
        else:
            print("  9. ⏭️  pnl_usd already exists")
            
        if not column_exists(cursor, 'transactions', 'pnl_percentage'):
            print(" 10. Adding pnl_percentage...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN pnl_percentage DECIMAL(10, 4) NULL AFTER pnl_usd")
        else:
            print(" 10. ⏭️  pnl_percentage already exists")
            
        if not column_exists(cursor, 'transactions', 'is_winning'):
            print(" 11. Adding is_winning...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN is_winning BOOLEAN NULL AFTER pnl_percentage")
        else:
            print(" 11. ⏭️  is_winning already exists")
            
        if not column_exists(cursor, 'transactions', 'realized_pnl'):
            print(" 12. Adding realized_pnl...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN realized_pnl DECIMAL(20, 8) NULL AFTER is_winning")
        else:
            print(" 12. ⏭️  realized_pnl already exists")
            
        if not column_exists(cursor, 'transactions', 'unrealized_pnl'):
            print(" 13. Adding unrealized_pnl...")
            cursor.execute("""
                ALTER TABLE transactions ADD COLUMN unrealized_pnl DECIMAL(20, 8) NULL 
                COMMENT 'Current unrealized P&L for open positions' AFTER realized_pnl
            """)
        else:
            print(" 13. ⏭️  unrealized_pnl already exists")
        
        # 14-15. Add risk-reward ratios
        if not column_exists(cursor, 'transactions', 'risk_reward_ratio'):
            print(" 14. Adding risk_reward_ratio...")
            cursor.execute("""
                ALTER TABLE transactions ADD COLUMN risk_reward_ratio DECIMAL(10, 4) NULL 
                COMMENT 'Planned RR ratio (e.g., 3.0 for 1:3)' AFTER unrealized_pnl
            """)
        else:
            print(" 14. ⏭️  risk_reward_ratio already exists")
            
        if not column_exists(cursor, 'transactions', 'actual_rr_ratio'):
            print(" 15. Adding actual_rr_ratio...")
            cursor.execute("""
                ALTER TABLE transactions ADD COLUMN actual_rr_ratio DECIMAL(10, 4) NULL 
                COMMENT 'Actual RR achieved' AFTER risk_reward_ratio
            """)
        else:
            print(" 15. ⏭️  actual_rr_ratio already exists")
        
        # 16. Add strategy information
        if not column_exists(cursor, 'transactions', 'strategy_used'):
            print(" 16. Adding strategy_used...")
            cursor.execute("""
                ALTER TABLE transactions ADD COLUMN strategy_used VARCHAR(100) NULL 
                COMMENT 'Trading strategy from LLM' AFTER actual_rr_ratio
            """)
        else:
            print(" 16. ⏭️  strategy_used already exists")
        
        # 17-18. Add trading fees and slippage
        if not column_exists(cursor, 'transactions', 'fees_paid'):
            print(" 17. Adding fees_paid...")
            cursor.execute("""
                ALTER TABLE transactions ADD COLUMN fees_paid DECIMAL(20, 8) NULL DEFAULT 0 
                COMMENT 'Trading fees in USD' AFTER strategy_used
            """)
        else:
            print(" 17. ⏭️  fees_paid already exists")
            
        if not column_exists(cursor, 'transactions', 'slippage'):
            print(" 18. Adding slippage...")
            cursor.execute("""
                ALTER TABLE transactions ADD COLUMN slippage DECIMAL(10, 4) NULL 
                COMMENT 'Price slippage percentage' AFTER fees_paid
            """)
        else:
            print(" 18. ⏭️  slippage already exists")
        
        # 19. Add trade duration
        if not column_exists(cursor, 'transactions', 'trade_duration_minutes'):
            print(" 19. Adding trade_duration_minutes...")
            cursor.execute("""
                ALTER TABLE transactions ADD COLUMN trade_duration_minutes INT NULL 
                COMMENT 'Duration position was held' AFTER slippage
            """)
        else:
            print(" 19. ⏭️  trade_duration_minutes already exists")
        
        # 20. Add last_updated_price
        if not column_exists(cursor, 'transactions', 'last_updated_price'):
            print(" 20. Adding last_updated_price...")
            cursor.execute("""
                ALTER TABLE transactions ADD COLUMN last_updated_price DECIMAL(20, 8) NULL 
                COMMENT 'Last known market price for open positions' AFTER trade_duration_minutes
            """)
        else:
            print(" 20. ⏭️  last_updated_price already exists")
        
        # 21. Update status enum
        print(" 21. Updating status enum...")
        cursor.execute("""
            ALTER TABLE transactions MODIFY COLUMN status ENUM(
                'PENDING',
                'EXECUTED', 
                'OPEN',
                'CLOSED',
                'STOPPED_OUT',
                'FAILED',
                'CANCELLED'
            ) DEFAULT 'PENDING'
        """)
        
        # 22. Add foreign key for prompt_id
        if not constraint_exists(cursor, 'transactions', 'fk_transactions_prompt_id'):
            print(" 22. Adding foreign key for prompt_id...")
            cursor.execute("""
                ALTER TABLE transactions 
                ADD CONSTRAINT fk_transactions_prompt_id 
                FOREIGN KEY (prompt_id) REFERENCES llm_prompt_templates(id) ON DELETE SET NULL
            """)
        else:
            print(" 22. ⏭️  Foreign key fk_transactions_prompt_id already exists")
        
        # 23-29. Add indexes
        indexes = [
            ('idx_transactions_user_principal_id', 'user_principal_id'),
            ('idx_transactions_prompt_id', 'prompt_id'),
            ('idx_transactions_status', 'status'),
            ('idx_transactions_entry_time', 'entry_time'),
            ('idx_transactions_exit_time', 'exit_time'),
            ('idx_transactions_is_winning', 'is_winning'),
            ('idx_transactions_bot_status', 'bot_id, status'),
        ]
        
        for i, (index_name, columns) in enumerate(indexes, start=23):
            if not index_exists(cursor, 'transactions', index_name):
                print(f" {i}. Adding index {index_name}...")
                cursor.execute(f"ALTER TABLE transactions ADD INDEX {index_name} ({columns})")
            else:
                print(f" {i}. ⏭️  Index {index_name} already exists")
        
        # 30. Add table comment
        print(" 30. Adding table comment...")
        cursor.execute("""
            ALTER TABLE transactions 
            COMMENT = 'Enhanced transactions table with comprehensive trade performance tracking'
        """)
        
        connection.commit()
        print("✅ Migration 027 completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()

if __name__ == "__main__":
    # This allows the migration to be run standalone for testing
    import pymysql
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '3306')),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'bot_marketplace')
    )
    
    try:
        migrate(conn)
    finally:
        conn.close()


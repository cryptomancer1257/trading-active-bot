#!/usr/bin/env python3
"""
Run database migration for bot registration features (fixed version)
"""

from sqlalchemy import text
from core.database import engine

def run_migration():
    """Execute the migration SQL with proper error handling"""
    print("🔄 Running database migration...")
    
    try:
        with engine.connect() as connection:
            # Execute statements one by one with proper error handling
            
            # 1. Add new columns to subscriptions table (main migration)
            try:
                print("Adding new columns to subscriptions table...")
                connection.execute(text("""
                    ALTER TABLE subscriptions 
                    ADD COLUMN user_principal_id VARCHAR(255) COMMENT 'ICP Principal ID của user',
                    ADD COLUMN timeframes JSON COMMENT 'List of timeframes ["1h", "2h", "4h"]',
                    ADD COLUMN trade_evaluation_period INT COMMENT 'Minutes for bot analysis period',
                    ADD COLUMN network_type ENUM('testnet', 'mainnet') DEFAULT 'testnet' COMMENT 'Network type',
                    ADD COLUMN trade_mode ENUM('Spot', 'Margin', 'Futures') DEFAULT 'Spot' COMMENT 'Trading mode'
                """))
                connection.commit()
                print("✅ New columns added to subscriptions table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("⚠️ Columns already exist in subscriptions table")
                else:
                    raise
            
            # 2. Add indexes
            try:
                print("Adding indexes...")
                connection.execute(text("CREATE INDEX idx_subscriptions_principal_id ON subscriptions(user_principal_id)"))
                connection.commit()
                print("✅ Index idx_subscriptions_principal_id created")
            except Exception as e:
                if "already exists" in str(e) or "Duplicate key name" in str(e):
                    print("⚠️ Index idx_subscriptions_principal_id already exists")
                else:
                    print(f"⚠️ Index creation warning: {e}")
            
            try:
                connection.execute(text("CREATE INDEX idx_subscriptions_principal_bot ON subscriptions(user_principal_id, bot_id)"))
                connection.commit()
                print("✅ Index idx_subscriptions_principal_bot created")
            except Exception as e:
                if "already exists" in str(e) or "Duplicate key name" in str(e):
                    print("⚠️ Index idx_subscriptions_principal_bot already exists")
                else:
                    print(f"⚠️ Index creation warning: {e}")
            
            # 3. Check if api_key column exists in users table
            try:
                result = connection.execute(text("DESCRIBE users"))
                columns = [row[0] for row in result]
                
                if 'api_key' not in columns:
                    print("Adding api_key column to users table...")
                    connection.execute(text("ALTER TABLE users ADD COLUMN api_key VARCHAR(255) UNIQUE COMMENT 'API key for marketplace authentication'"))
                    connection.commit()
                    print("✅ api_key column added to users table")
                else:
                    print("⚠️ api_key column already exists in users table")
                    
            except Exception as e:
                print(f"⚠️ Error with api_key column: {e}")
            
            # 4. Add api_key index
            try:
                connection.execute(text("CREATE INDEX idx_users_api_key ON users(api_key)"))
                connection.commit()
                print("✅ Index idx_users_api_key created")
            except Exception as e:
                if "already exists" in str(e) or "Duplicate key name" in str(e):
                    print("⚠️ Index idx_users_api_key already exists")
                else:
                    print(f"⚠️ Index creation warning: {e}")
        
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    run_migration()

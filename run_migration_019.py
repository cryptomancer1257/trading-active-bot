#!/usr/bin/env python3

"""
Run migration 019: Create developer_exchange_credentials table
"""

import sys
import os
from sqlalchemy import create_engine, text
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the exchange credentials table migration"""
    
    # Database connection
    DATABASE_URL = "sqlite:///./trade_bot_marketplace.db"
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Read migration file
        migration_file = "migrations/versions/019_create_exchange_credentials_table.sql"
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Convert MySQL syntax to SQLite
        migration_sql_sqlite = migration_sql.replace(
            "INTEGER PRIMARY KEY AUTO_INCREMENT",
            "INTEGER PRIMARY KEY AUTOINCREMENT"
        ).replace(
            "ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI')",
            "VARCHAR(20) CHECK(exchange_type IN ('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI'))"
        ).replace(
            "ENUM('SPOT', 'FUTURES', 'MARGIN')",
            "VARCHAR(20) CHECK(credential_type IN ('SPOT', 'FUTURES', 'MARGIN'))"
        ).replace(
            "ENUM('TESTNET', 'MAINNET')",
            "VARCHAR(20) CHECK(network_type IN ('TESTNET', 'MAINNET'))"
        ).replace(
            "ON UPDATE CURRENT_TIMESTAMP",
            ""
        )
        
        with engine.connect() as connection:
            # Execute migration
            logger.info("🔄 Running migration 019...")
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql_sqlite.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement and not statement.startswith('--'):
                    logger.info(f"Executing: {statement[:100]}...")
                    connection.execute(text(statement))
            
            connection.commit()
            logger.info("✅ Migration 019 completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        sys.exit(1)

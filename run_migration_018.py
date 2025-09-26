#!/usr/bin/env python3
"""
Run migration 018: Add BYBIT and HUOBI exchange types
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/docker.env')

def run_migration():
    try:
        # Database connection
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'), 
            password=os.getenv('DB_PASSWORD', 'password'),
            database=os.getenv('DB_NAME', 'trading_bot_db')
        )
        
        cursor = conn.cursor()
        
        print('🔄 Running migration 018: Add BYBIT and HUOBI exchange types...')
        
        # Migration statements
        statements = [
            "ALTER TABLE bots MODIFY COLUMN exchange_type ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') DEFAULT 'BINANCE'",
            "ALTER TABLE exchange_credentials MODIFY COLUMN exchange ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') NOT NULL"
        ]
        
        for stmt in statements:
            print(f'📡 Executing: {stmt[:80]}...')
            cursor.execute(stmt)
            
        conn.commit()
        cursor.close()
        conn.close()
        
        print('✅ Migration 018 completed successfully!')
        
    except mysql.connector.Error as e:
        print(f'❌ Database error: {e}')
        return False
    except Exception as e:
        print(f'❌ Error: {e}')
        return False
        
    return True

if __name__ == '__main__':
    run_migration()

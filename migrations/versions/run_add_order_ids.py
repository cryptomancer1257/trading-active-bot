#!/usr/bin/env python3
"""
Migration: Add order tracking columns to transactions table
Run this script to add sl_order_ids and tp_order_ids columns
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import text
from core.database import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the migration to add order tracking columns"""
    
    logger.info("🚀 Starting migration: Add order tracking columns")
    
    db = SessionLocal()
    
    try:
        # Check if columns already exist
        check_query = text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'transactions' 
            AND COLUMN_NAME IN ('sl_order_ids', 'tp_order_ids')
        """)
        
        result = db.execute(check_query)
        existing_columns = [row[0] for row in result]
        
        if 'sl_order_ids' in existing_columns and 'tp_order_ids' in existing_columns:
            logger.info("✅ Columns already exist, skipping migration")
            return True
        
        # Add columns
        logger.info("📝 Adding sl_order_ids and tp_order_ids columns...")
        
        if 'sl_order_ids' not in existing_columns:
            add_sl_query = text("""
                ALTER TABLE transactions 
                ADD COLUMN sl_order_ids JSON COMMENT 'Stop Loss order IDs (array)'
            """)
            db.execute(add_sl_query)
            logger.info("✅ Added sl_order_ids column")
        
        if 'tp_order_ids' not in existing_columns:
            add_tp_query = text("""
                ALTER TABLE transactions 
                ADD COLUMN tp_order_ids JSON COMMENT 'Take Profit order IDs (array)'
            """)
            db.execute(add_tp_query)
            logger.info("✅ Added tp_order_ids column")
        
        # Add index for faster queries
        logger.info("📝 Adding index for status and symbol...")
        try:
            add_index_query = text("""
                CREATE INDEX IF NOT EXISTS idx_transactions_status_symbol 
                ON transactions(status, symbol)
            """)
            db.execute(add_index_query)
            logger.info("✅ Added index")
        except Exception as e:
            logger.warning(f"⚠️ Index might already exist: {e}")
        
        db.commit()
        
        # Verify columns were added
        verify_query = text("""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                COLUMN_COMMENT 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'transactions' 
            AND COLUMN_NAME IN ('sl_order_ids', 'tp_order_ids')
        """)
        
        result = db.execute(verify_query)
        columns = result.fetchall()
        
        logger.info("✅ Migration completed successfully!")
        logger.info("📋 Added columns:")
        for col in columns:
            logger.info(f"   - {col[0]} ({col[1]}): {col[2]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)


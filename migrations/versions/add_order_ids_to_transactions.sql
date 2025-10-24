-- Migration: Add order tracking columns to transactions table
-- Purpose: Track SL/TP order IDs to enable proper cleanup when position closes
-- Date: 2025-10-24

-- Add columns for tracking order IDs (only if they don't exist)
-- Check and add sl_order_ids
SET @col_exists = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'transactions' 
    AND COLUMN_NAME = 'sl_order_ids'
);

SET @sql_add_sl = IF(@col_exists = 0, 
    'ALTER TABLE transactions ADD COLUMN sl_order_ids JSON COMMENT ''Stop Loss order IDs (array)''',
    'SELECT ''Column sl_order_ids already exists'' as message'
);
PREPARE stmt FROM @sql_add_sl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check and add tp_order_ids
SET @col_exists = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'transactions' 
    AND COLUMN_NAME = 'tp_order_ids'
);

SET @sql_add_tp = IF(@col_exists = 0, 
    'ALTER TABLE transactions ADD COLUMN tp_order_ids JSON COMMENT ''Take Profit order IDs (array)''',
    'SELECT ''Column tp_order_ids already exists'' as message'
);
PREPARE stmt FROM @sql_add_tp;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add index for faster queries (only if it doesn't exist)
SET @index_exists = (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'transactions' 
    AND INDEX_NAME = 'idx_transactions_status_symbol'
);

SET @sql_add_index = IF(@index_exists = 0, 
    'CREATE INDEX idx_transactions_status_symbol ON transactions(status, symbol)',
    'SELECT ''Index idx_transactions_status_symbol already exists'' as message'
);
PREPARE stmt FROM @sql_add_index;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verify columns were added
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'transactions' 
AND COLUMN_NAME IN ('sl_order_ids', 'tp_order_ids');


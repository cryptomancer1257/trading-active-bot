-- Migration: Add order tracking columns to transactions table
-- Purpose: Track SL/TP order IDs to enable proper cleanup when position closes
-- Date: 2025-10-24

-- Add columns for tracking order IDs
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS sl_order_ids JSON COMMENT 'Stop Loss order IDs (array)',
ADD COLUMN IF NOT EXISTS tp_order_ids JSON COMMENT 'Take Profit order IDs (array)';

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_transactions_status_symbol 
ON transactions(status, symbol);

-- Verify columns were added
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    COLUMN_COMMENT 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'transactions' 
AND COLUMN_NAME IN ('sl_order_ids', 'tp_order_ids');


-- Add secondary_trading_pairs column to subscriptions table
-- Migration: 030_add_secondary_trading_pairs.sql
-- Date: 2025-10-11

ALTER TABLE subscriptions 
ADD COLUMN secondary_trading_pairs JSON DEFAULT NULL 
COMMENT 'List of secondary trading pairs to monitor (priority order)';

-- Update existing subscriptions to have empty list for secondary pairs
UPDATE subscriptions 
SET secondary_trading_pairs = '[]' 
WHERE secondary_trading_pairs IS NULL;

-- Example data structure:
-- secondary_trading_pairs = ["ETH/USDT", "BNB/USDT", "SOL/USDT"]


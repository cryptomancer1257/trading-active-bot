-- Add trading_pairs to bots table (Simplified version - MySQL 8.0 compatible)
-- This allows developers to configure multiple trading pairs that the bot supports

-- Check if column exists, if not add it
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = DATABASE() 
    AND table_name = 'bots' 
    AND column_name = 'trading_pairs'
);

-- Only add column if it doesn't exist
SET @sql = IF(@col_exists = 0,
    'ALTER TABLE bots ADD COLUMN trading_pairs JSON DEFAULT NULL COMMENT ''List of trading pairs supported by this bot (e.g., ["BTC/USDT", "ETH/USDT"])''',
    'SELECT "Column trading_pairs already exists" as status'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Migrate existing data: trading_pair -> trading_pairs array
UPDATE bots 
SET trading_pairs = JSON_ARRAY(trading_pair) 
WHERE trading_pairs IS NULL AND trading_pair IS NOT NULL;


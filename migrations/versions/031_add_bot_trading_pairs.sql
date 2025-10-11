-- Add trading_pairs to bots table
-- This allows developers to configure multiple trading pairs that the bot supports
-- Users can then select primary + secondary pairs from this list

-- Check if column exists before adding
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = DATABASE() 
    AND table_name = 'bots' 
    AND column_name = 'trading_pairs'
);

-- Add trading_pairs column (JSON array of supported pairs)
SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE bots ADD COLUMN trading_pairs JSON DEFAULT NULL COMMENT ''List of trading pairs supported by this bot (e.g., ["BTC/USDT", "ETH/USDT"])''',
    'SELECT "Column trading_pairs already exists, skipping..." as status'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- For existing bots, migrate trading_pair to trading_pairs array
UPDATE bots 
SET trading_pairs = JSON_ARRAY(trading_pair) 
WHERE trading_pairs IS NULL AND trading_pair IS NOT NULL;



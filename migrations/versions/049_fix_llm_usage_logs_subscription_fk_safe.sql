-- Fix foreign key constraint for llm_usage_logs.subscription_id (SAFE VERSION)
-- It should reference subscriptions.id, not developer_llm_subscriptions.id

-- First, check if the table exists and has the column
SET @table_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'llm_usage_logs'
);

SET @column_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'llm_usage_logs' 
    AND COLUMN_NAME = 'subscription_id'
);

-- Only proceed if table and column exist
SET @sql = IF(@table_exists > 0 AND @column_exists > 0,
    'SELECT ''Table and column exist, proceeding with foreign key fix'' AS message',
    'SELECT ''Table or column does not exist, skipping'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check if any foreign key exists on subscription_id column
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'llm_usage_logs' 
    AND COLUMN_NAME = 'subscription_id'
    AND REFERENCED_TABLE_NAME IS NOT NULL
);

-- Drop any existing foreign key on subscription_id if it exists
SET @sql = IF(@fk_exists > 0,
    CONCAT('ALTER TABLE llm_usage_logs DROP FOREIGN KEY ',
           (SELECT CONSTRAINT_NAME 
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'llm_usage_logs' 
            AND COLUMN_NAME = 'subscription_id'
            AND REFERENCED_TABLE_NAME IS NOT NULL
            LIMIT 1)),
    'SELECT ''No foreign key found on subscription_id'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check if the correct foreign key constraint already exists
SET @correct_fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'llm_usage_logs' 
    AND CONSTRAINT_NAME = 'llm_usage_logs_subscription_fk'
    AND REFERENCED_TABLE_NAME = 'subscriptions'
);

-- Add the correct foreign key constraint (only if table and column exist AND constraint doesn't exist)
SET @sql = IF(@table_exists > 0 AND @column_exists > 0 AND @correct_fk_exists = 0,
    'ALTER TABLE llm_usage_logs ADD CONSTRAINT llm_usage_logs_subscription_fk FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL',
    'SELECT ''Skipping foreign key creation - table/column missing or constraint already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add index for better query performance (check if exists first)
SET @index_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'llm_usage_logs' 
    AND INDEX_NAME = 'idx_llm_usage_logs_subscription_id'
);

SET @sql = IF(@index_exists = 0 AND @table_exists > 0 AND @column_exists > 0,
    'CREATE INDEX idx_llm_usage_logs_subscription_id ON llm_usage_logs(subscription_id)',
    'SELECT ''Index already exists or table/column missing'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

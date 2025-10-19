-- Fix foreign key constraint for llm_usage_logs.subscription_id
-- It should reference subscriptions.id, not developer_llm_subscriptions.id

-- Check if the foreign key exists before dropping it
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'llm_usage_logs' 
    AND CONSTRAINT_NAME = 'llm_usage_logs_ibfk_2'
);

-- Drop the incorrect foreign key constraint if it exists
SET @sql = IF(@fk_exists > 0,
    'ALTER TABLE llm_usage_logs DROP FOREIGN KEY llm_usage_logs_ibfk_2',
    'SELECT ''Foreign key llm_usage_logs_ibfk_2 does not exist'' AS message'
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

-- Add the correct foreign key constraint only if it doesn't exist
SET @sql = IF(@correct_fk_exists = 0,
    'ALTER TABLE llm_usage_logs ADD CONSTRAINT llm_usage_logs_subscription_fk FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL',
    'SELECT ''Foreign key llm_usage_logs_subscription_fk already exists'' AS message'
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

SET @sql = IF(@index_exists = 0,
    'CREATE INDEX idx_llm_usage_logs_subscription_id ON llm_usage_logs(subscription_id)',
    'SELECT ''Index already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

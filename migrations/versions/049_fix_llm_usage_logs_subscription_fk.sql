-- Fix foreign key constraint for llm_usage_logs.subscription_id
-- It should reference subscriptions.id, not developer_llm_subscriptions.id

-- Drop the incorrect foreign key constraint
ALTER TABLE llm_usage_logs DROP FOREIGN KEY llm_usage_logs_ibfk_2;

-- Add the correct foreign key constraint
ALTER TABLE llm_usage_logs 
ADD CONSTRAINT llm_usage_logs_subscription_fk 
FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL;

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

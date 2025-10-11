-- Fix migration 017 conflict
-- Run this in PyCharm Database Tool or MySQL client

USE trade_bot_marketplace;

-- Mark migration 017 as completed
INSERT INTO migration_history (filename, applied_at)
SELECT '017_add_bot_risk_config.sql', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM migration_history 
    WHERE filename = '017_add_bot_risk_config.sql'
);

-- Verify
SELECT filename, applied_at 
FROM migration_history 
ORDER BY applied_at DESC 
LIMIT 10;

-- Show pending migrations will be 030

-- Check migration status
SELECT * FROM migration_history 
WHERE filename IN ('017_add_bot_risk_config.sql', '030_add_secondary_trading_pairs.sql')
ORDER BY applied_at DESC;

-- Check if column exists
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    IS_NULLABLE, 
    COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'trade_bot_marketplace'
AND TABLE_NAME = 'subscriptions'
AND COLUMN_NAME = 'secondary_trading_pairs';

-- Check subscription 688
SELECT 
    id, 
    trading_pair, 
    secondary_trading_pairs,
    created_at
FROM subscriptions
WHERE id = 688;

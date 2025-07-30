-- Migration script for Bot Registration Marketplace features
-- Add new fields to subscriptions table for marketplace bot registration

-- Add new columns to subscriptions table
ALTER TABLE subscriptions 
ADD COLUMN user_principal_id VARCHAR(255) COMMENT 'ICP Principal ID của user',
ADD COLUMN timeframes JSON COMMENT 'List of timeframes ["1h", "2h", "4h"]',
ADD COLUMN trade_evaluation_period INT COMMENT 'Minutes for bot analysis period',
ADD COLUMN network_type ENUM('testnet', 'mainnet') DEFAULT 'testnet' COMMENT 'Network type',
ADD COLUMN trade_mode ENUM('Spot', 'Margin', 'Futures') DEFAULT 'Spot' COMMENT 'Trading mode';

-- Add index for efficient querying by principal_id
CREATE INDEX idx_subscriptions_principal_id ON subscriptions(user_principal_id);

-- Add composite index for unique principal_id + bot_id combination
CREATE INDEX idx_subscriptions_principal_bot ON subscriptions(user_principal_id, bot_id);

-- Update exchange_credentials table to include more exchanges if needed
ALTER TABLE exchange_credentials 
MODIFY COLUMN exchange ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') NOT NULL;

-- Update subscriptions table exchange_type to match
ALTER TABLE subscriptions 
MODIFY COLUMN exchange_type ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') DEFAULT 'BINANCE';

-- Ensure users table has api_key field for marketplace authentication
-- (This might already exist, but we add it if it doesn't)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS api_key VARCHAR(255) UNIQUE COMMENT 'API key for marketplace authentication';

-- Add index on api_key for efficient authentication
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);

-- Optional: Create a view for marketplace bot registrations
CREATE OR REPLACE VIEW marketplace_bot_registrations AS
SELECT 
    s.id as subscription_id,
    s.user_principal_id,
    s.bot_id,
    b.name as bot_name,
    s.trading_pair as symbol,
    s.timeframes,
    s.trade_evaluation_period,
    s.started_at as starttime,
    s.expires_at as endtime,
    s.exchange_type as exchange_name,
    s.network_type,
    s.trade_mode,
    s.status,
    s.created_at,
    s.updated_at
FROM subscriptions s
JOIN bots b ON s.bot_id = b.id
WHERE s.user_principal_id IS NOT NULL;
-- Migration: Bot Registration Marketplace features
-- Add new fields to subscriptions table for marketplace bot registration
-- Date: 2024-12-19

-- Simple approach: Add columns directly (will error if exists, but that's OK for existing deployments)

-- Add new columns to subscriptions table
ALTER TABLE subscriptions ADD COLUMN user_principal_id VARCHAR(255) COMMENT 'ICP Principal ID';
ALTER TABLE subscriptions ADD COLUMN timeframes JSON COMMENT 'List of timeframes';
ALTER TABLE subscriptions ADD COLUMN trade_evaluation_period INT COMMENT 'Minutes for bot analysis';
ALTER TABLE subscriptions ADD COLUMN network_type ENUM('testnet', 'mainnet') DEFAULT 'testnet';
ALTER TABLE subscriptions ADD COLUMN trade_mode ENUM('Spot', 'Margin', 'Futures') DEFAULT 'Spot';

-- Add indexes
CREATE INDEX idx_subscriptions_principal_id ON subscriptions(user_principal_id);
CREATE INDEX idx_subscriptions_principal_bot ON subscriptions(user_principal_id, bot_id);

-- Update exchange_credentials table
ALTER TABLE exchange_credentials 
MODIFY COLUMN exchange ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') NOT NULL;

-- Update subscriptions table exchange_type
ALTER TABLE subscriptions 
MODIFY COLUMN exchange_type ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') DEFAULT 'BINANCE';

-- Add api_key to users table
-- ALTER TABLE users ADD COLUMN api_key VARCHAR(255) UNIQUE COMMENT 'API key for marketplace auth';

-- Add index on api_key
CREATE INDEX idx_users_api_key ON users(api_key);

-- Create view for marketplace bot registrations
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
    s.status
FROM subscriptions s
JOIN bots b ON s.bot_id = b.id
WHERE s.user_principal_id IS NOT NULL;

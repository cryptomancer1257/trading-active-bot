-- Migration: Bot Registration Marketplace features
-- Add new fields to subscriptions table for marketplace bot registration
-- Date: 2024-12-19

-- Simple approach: Add columns directly (will error if exists, but that's OK for existing deployments)

-- Add new columns to subscriptions table (safe)
-- user_principal_id
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'user_principal_id';
SET @sql = IF(@exists = 0, 'ALTER TABLE subscriptions ADD COLUMN user_principal_id VARCHAR(255) COMMENT "ICP Principal ID"', 'SELECT "user_principal_id exists"');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- timeframes
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'timeframes';
SET @sql = IF(@exists = 0, 'ALTER TABLE subscriptions ADD COLUMN timeframes JSON COMMENT "List of timeframes"', 'SELECT "timeframes exists"');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- trade_evaluation_period
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'trade_evaluation_period';
SET @sql = IF(@exists = 0, 'ALTER TABLE subscriptions ADD COLUMN trade_evaluation_period INT COMMENT "Minutes for bot analysis"', 'SELECT "trade_evaluation_period exists"');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- network_type
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'network_type';
SET @sql = IF(@exists = 0, 'ALTER TABLE subscriptions ADD COLUMN network_type ENUM("testnet", "mainnet") DEFAULT "testnet"', 'SELECT "network_type exists"');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- trade_mode
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'trade_mode';
SET @sql = IF(@exists = 0, 'ALTER TABLE subscriptions ADD COLUMN trade_mode ENUM("Spot", "Margin", "Futures") DEFAULT "Spot"', 'SELECT "trade_mode exists"');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add indexes (safe)
SELECT COUNT(*) INTO @index_exists FROM INFORMATION_SCHEMA.STATISTICS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND index_name = 'idx_subscriptions_principal_id';
SET @sql = IF(@index_exists = 0, 'CREATE INDEX idx_subscriptions_principal_id ON subscriptions(user_principal_id)', 'SELECT "idx_subscriptions_principal_id exists"');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT COUNT(*) INTO @index_exists FROM INFORMATION_SCHEMA.STATISTICS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND index_name = 'idx_subscriptions_principal_bot';
SET @sql = IF(@index_exists = 0, 'CREATE INDEX idx_subscriptions_principal_bot ON subscriptions(user_principal_id, bot_id)', 'SELECT "idx_subscriptions_principal_bot exists"');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Update exchange_credentials table
ALTER TABLE exchange_credentials 
MODIFY COLUMN exchange ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') NOT NULL;

-- Update subscriptions table exchange_type
ALTER TABLE subscriptions 
MODIFY COLUMN exchange_type ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') DEFAULT 'BINANCE';

-- Add api_key to users table
ALTER TABLE users ADD COLUMN api_key VARCHAR(255) UNIQUE COMMENT 'API key for marketplace auth';

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
    s.status,
    s.created_at,
    s.updated_at
FROM subscriptions s
JOIN bots b ON s.bot_id = b.id
WHERE s.user_principal_id IS NOT NULL;

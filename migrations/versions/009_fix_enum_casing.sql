-- Migration: Fix enum casing to match application enums
-- Align ENUM values to uppercase TESTNET/MAINNET and SPOT/MARGIN/FUTURES

USE bot_marketplace;

-- Update network_type enum to uppercase values
ALTER TABLE subscriptions 
MODIFY COLUMN network_type ENUM('TESTNET', 'MAINNET') DEFAULT 'TESTNET' COMMENT 'Network type';

-- Map existing lowercase values to uppercase, if any
UPDATE subscriptions SET network_type = 'TESTNET' WHERE network_type = 'testnet';
UPDATE subscriptions SET network_type = 'MAINNET' WHERE network_type = 'mainnet';

-- Update trade_mode enum to uppercase values
ALTER TABLE subscriptions 
MODIFY COLUMN trade_mode ENUM('SPOT', 'MARGIN', 'FUTURES') DEFAULT 'SPOT' COMMENT 'Trade mode';

-- Map existing TitleCase values to uppercase, if any
UPDATE subscriptions SET trade_mode = 'SPOT' WHERE trade_mode = 'Spot';
UPDATE subscriptions SET trade_mode = 'MARGIN' WHERE trade_mode = 'Margin';
UPDATE subscriptions SET trade_mode = 'FUTURES' WHERE trade_mode = 'Futures';

COMMIT; 
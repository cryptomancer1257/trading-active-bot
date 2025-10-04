-- Migration: Update exchange_type enum to support new exchanges
-- Version: 028
-- Created: 2025-10-04
-- Description: Remove COINBASE, add OKX, BITGET, MULTI to exchange_type enum

-- Update bots table exchange_type enum
ALTER TABLE bots 
MODIFY COLUMN exchange_type ENUM(
  'BINANCE',
  'BYBIT',
  'OKX',
  'BITGET',
  'HUOBI',
  'KRAKEN',
  'MULTI'
) DEFAULT 'BINANCE';

-- Update developer_exchange_credentials table exchange_type enum
ALTER TABLE developer_exchange_credentials 
MODIFY COLUMN exchange_type ENUM(
  'BINANCE',
  'BYBIT',
  'OKX',
  'BITGET',
  'HUOBI',
  'KRAKEN',
  'MULTI'
) NOT NULL;

-- Update subscriptions table if exchange_type exists there
-- (Run this only if the column exists, otherwise comment out)
-- ALTER TABLE subscriptions 
-- MODIFY COLUMN exchange_type ENUM(
--   'BINANCE',
--   'BYBIT',
--   'OKX',
--   'BITGET',
--   'HUOBI',
--   'KRAKEN',
--   'MULTI'
-- );

-- Verify the change
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    COLUMN_TYPE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'bot_marketplace'
  AND COLUMN_NAME = 'exchange_type'
  AND TABLE_NAME IN ('bots', 'developer_exchange_credentials', 'subscriptions');


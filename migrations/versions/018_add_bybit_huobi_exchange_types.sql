-- Add BYBIT and HUOBI to ExchangeType enum
-- Migration: 018_add_bybit_huobi_exchange_types.sql

-- For MySQL: Add new enum values to existing enum columns
ALTER TABLE bots MODIFY COLUMN exchange_type ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') DEFAULT 'BINANCE';
ALTER TABLE exchange_credentials MODIFY COLUMN exchange ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') NOT NULL;

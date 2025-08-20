-- Migration: Remove columns from Subscription
ALTER TABLE subscriptions DROP COLUMN timeframe;
ALTER TABLE subscriptions DROP COLUMN timeframes;
ALTER TABLE subscriptions DROP COLUMN exchange_type;
ALTER TABLE subscriptions DROP COLUMN trading_pair;
ALTER TABLE subscriptions DROP COLUMN strategy_config;
ALTER TABLE subscriptions DROP COLUMN trade_mode;

-- Migration: Add columns to Bot
ALTER TABLE bots ADD COLUMN timeframe VARCHAR(10) NOT NULL DEFAULT '1h' COMMENT 'Timeframe for the bot, e.g., 1h, 4h, 1d';
ALTER TABLE bots ADD COLUMN timeframes JSON NULL COMMENT 'List of timeframes for the bot';
ALTER TABLE bots ADD COLUMN exchange_type VARCHAR(10) NOT NULL DEFAULT 'BINANCE' COMMENT 'Exchange type for the bot';
ALTER TABLE bots ADD COLUMN trading_pair VARCHAR(20) NOT NULL DEFAULT 'BTC/USDT' COMMENT 'Trading pair for the bot';
ALTER TABLE bots ADD COLUMN strategy_config JSON NULL COMMENT 'Strategy configuration for the bot';
ALTER TABLE bots ADD COLUMN bot_mode VARCHAR(20) NOT NULL DEFAULT 'PASSIVE' COMMENT 'Bot mode (e.g., PASSIVE, AGGRESSIVE)';
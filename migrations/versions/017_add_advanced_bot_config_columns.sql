-- Add advanced trading and AI configuration columns to bots table
-- Migration: 017_add_advanced_bot_config_columns.sql

-- Add advanced trading configuration columns
ALTER TABLE bots ADD COLUMN leverage INTEGER DEFAULT 10;
ALTER TABLE bots ADD COLUMN risk_percentage FLOAT DEFAULT 2.0;
ALTER TABLE bots ADD COLUMN stop_loss_percentage FLOAT DEFAULT 5.0;
ALTER TABLE bots ADD COLUMN take_profit_percentage FLOAT DEFAULT 10.0;

-- Add AI/LLM configuration columns
ALTER TABLE bots ADD COLUMN llm_provider VARCHAR(50) DEFAULT NULL;
ALTER TABLE bots ADD COLUMN enable_image_analysis BOOLEAN DEFAULT FALSE;
ALTER TABLE bots ADD COLUMN enable_sentiment_analysis BOOLEAN DEFAULT FALSE;

-- Update existing bots with default values (optional, as DEFAULT should handle this)
UPDATE bots SET 
    leverage = 10,
    risk_percentage = 2.0,
    stop_loss_percentage = 5.0,
    take_profit_percentage = 10.0,
    enable_image_analysis = FALSE,
    enable_sentiment_analysis = FALSE
WHERE leverage IS NULL;

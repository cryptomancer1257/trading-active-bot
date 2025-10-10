-- Add risk management fields to bots table for default bot-level configuration
-- Migration: 017_add_bot_risk_config
-- Date: 2025-10-09

ALTER TABLE bots 
ADD COLUMN risk_config JSON DEFAULT NULL
COMMENT 'Default risk configuration for bot (used by all subscriptions unless overridden)';

ALTER TABLE bots
ADD COLUMN risk_management_mode VARCHAR(20) DEFAULT 'DEFAULT'
COMMENT 'Default risk management mode: DEFAULT or AI_PROMPT';

-- Create index for risk management mode
CREATE INDEX idx_bots_risk_mode ON bots(risk_management_mode);


-- Enhanced Risk Management System
-- Add support for DEFAULT and AI_PROMPT modes

-- Description: Enhance risk_config JSON column structure to support:
-- 1. DEFAULT mode: Human-configured risk parameters
-- 2. AI_PROMPT mode: LLM-based dynamic risk management
-- 3. Advanced features: Trailing stops, trading windows, cooldowns

-- Note: Since risk_config is already a JSON column in subscriptions table,
-- we don't need to alter the table structure. The new schema will be
-- enforced at the application level via Pydantic models.

-- However, we should add some helper columns for quick queries

-- Add risk management mode column
ALTER TABLE subscriptions 
ADD COLUMN risk_management_mode VARCHAR(20) DEFAULT 'DEFAULT' 
COMMENT 'Risk management mode: DEFAULT or AI_PROMPT';

-- Add daily loss tracking
ALTER TABLE subscriptions
ADD COLUMN daily_loss_amount DECIMAL(20, 8) DEFAULT 0 
COMMENT 'Accumulated loss for the day (for daily loss limit tracking)';

-- Add last loss reset date
ALTER TABLE subscriptions
ADD COLUMN last_loss_reset_date DATE DEFAULT NULL
COMMENT 'Last date when daily loss was reset';

-- Add cooldown timestamp
ALTER TABLE subscriptions
ADD COLUMN cooldown_until TIMESTAMP NULL DEFAULT NULL
COMMENT 'Timestamp until which trading is paused due to cooldown';

-- Add consecutive losses counter
ALTER TABLE subscriptions
ADD COLUMN consecutive_losses INTEGER DEFAULT 0
COMMENT 'Current count of consecutive losses';

-- Create index for quick lookup of active trading subscriptions within trading windows
CREATE INDEX idx_subscriptions_risk_mode 
ON subscriptions(risk_management_mode, status);

-- Create index for cooldown expiry checks
CREATE INDEX idx_subscriptions_cooldown 
ON subscriptions(cooldown_until);

-- Migration completed
-- The existing risk_config JSON column will now support the enhanced schema
-- defined in core/schemas.py (RiskConfig, TrailingStopConfig, TradingWindowConfig, CooldownConfig)


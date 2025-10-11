-- Add risk management fields to bots table for default bot-level configuration
-- Migration: 017_add_bot_risk_config
-- Date: 2025-10-09
-- Updated: 2025-10-11 (Added IF NOT EXISTS checks)

-- Add risk_config column if not exists
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = DATABASE() 
    AND table_name = 'bots' 
    AND column_name = 'risk_config'
);

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE bots ADD COLUMN risk_config JSON DEFAULT NULL COMMENT ''Default risk configuration for bot (used by all subscriptions unless overridden)''',
    'SELECT "Column risk_config already exists, skipping..." as status'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add risk_management_mode column if not exists
SET @col_exists = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = DATABASE() 
    AND table_name = 'bots' 
    AND column_name = 'risk_management_mode'
);

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE bots ADD COLUMN risk_management_mode VARCHAR(20) DEFAULT ''DEFAULT'' COMMENT ''Default risk management mode: DEFAULT or AI_PROMPT''',
    'SELECT "Column risk_management_mode already exists, skipping..." as status'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Create index if not exists
SET @index_exists = (
    SELECT COUNT(*) 
    FROM information_schema.statistics 
    WHERE table_schema = DATABASE() 
    AND table_name = 'bots' 
    AND index_name = 'idx_bots_risk_mode'
);

SET @sql = IF(@index_exists = 0, 
    'CREATE INDEX idx_bots_risk_mode ON bots(risk_management_mode)',
    'SELECT "Index idx_bots_risk_mode already exists, skipping..." as status'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


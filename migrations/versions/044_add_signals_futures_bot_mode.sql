-- Migration 044: Add SIGNALS_FUTURES bot_mode
-- Purpose: Add new bot mode for signals-only futures bots
-- Date: 2025-10-18

-- Add SIGNALS_FUTURES to bot_mode enum
ALTER TABLE bots MODIFY COLUMN bot_mode ENUM('PASSIVE', 'ACTIVE', 'SIGNALS_FUTURES', 'MULTI_TIMEFRAME') DEFAULT 'ACTIVE';

-- Update existing universal_futures_signals_bot bots to SIGNALS_FUTURES mode
UPDATE bots 
SET bot_mode = 'SIGNALS_FUTURES' 
WHERE code_path LIKE '%universal_futures_signals_bot%'
  AND bot_mode != 'SIGNALS_FUTURES';

-- Log completion
SELECT 'Migration 044 completed: Added SIGNALS_FUTURES bot_mode' AS status;

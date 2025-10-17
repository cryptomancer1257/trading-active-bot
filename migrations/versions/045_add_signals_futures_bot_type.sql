-- Migration 045: Add SIGNALS_FUTURES bot_type
-- Purpose: Add new bot type for signals-only futures bots
-- Date: 2025-10-18

-- Add SIGNALS_FUTURES to bot_type enum
ALTER TABLE bots MODIFY COLUMN bot_type VARCHAR(50) DEFAULT 'TECHNICAL';

-- Update bot 121 to use SIGNALS_FUTURES type
UPDATE bots 
SET bot_type = 'SIGNALS_FUTURES'
WHERE id = 121;

-- Update any other universal_futures_signals_bot bots
UPDATE bots 
SET bot_type = 'SIGNALS_FUTURES' 
WHERE code_path LIKE '%universal_futures_signals_bot%'
  AND bot_type != 'SIGNALS_FUTURES';

-- Log completion
SELECT 'Migration 045 completed: Added SIGNALS_FUTURES bot_type' AS status;

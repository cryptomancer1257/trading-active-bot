-- Add metadata column to bots table for storing performance metrics and other bot information
-- Migration: 033_add_bot_metadata_column.sql
-- Date: 2025-10-13
-- Note: Column named 'metadata' in DB, mapped to 'bot_metadata' in Python code (SQLAlchemy reserved word)

ALTER TABLE bots 
ADD COLUMN metadata JSON DEFAULT NULL 
COMMENT 'General metadata for storing additional bot information like performance stats';

-- Update existing bots to have empty dict for metadata
UPDATE bots 
SET metadata = '{}' 
WHERE metadata IS NULL;

-- Example data structure:
-- metadata = {
--   "performance": {
--     "total_trades": 100,
--     "winning_trades": 60,
--     "losing_trades": 40,
--     "win_rate": 60.0,
--     "total_pnl": 1500.50,
--     "avg_pnl": 15.01,
--     "avg_win": 50.25,
--     "avg_loss": -30.15,
--     "profit_factor": 2.0,
--     "last_updated": "2025-10-13T12:00:00"
--   }
-- }


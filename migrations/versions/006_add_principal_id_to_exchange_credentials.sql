-- Migration 006: Add principal_id support to exchange_credentials table
-- This allows marketplace users to store credentials without studio account

-- Add principal_id column to exchange_credentials (safe)
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'exchange_credentials' AND column_name = 'principal_id';
SET @sql = IF(@exists = 0, 'ALTER TABLE exchange_credentials ADD COLUMN principal_id VARCHAR(255) DEFAULT NULL AFTER user_id', 'SELECT "principal_id exists"');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add index for principal_id queries (safe)
SELECT COUNT(*) INTO @index_exists FROM INFORMATION_SCHEMA.STATISTICS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'exchange_credentials' AND index_name = 'idx_exchange_credentials_principal_id';
SET @sql = IF(@index_exists = 0, 'CREATE INDEX idx_exchange_credentials_principal_id ON exchange_credentials(principal_id)', 'SELECT "idx_exchange_credentials_principal_id exists"');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Create composite index for principal_id + exchange + is_testnet (safe)
SELECT COUNT(*) INTO @index_exists FROM INFORMATION_SCHEMA.STATISTICS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'exchange_credentials' AND index_name = 'idx_exchange_credentials_principal_exchange_testnet';
SET @sql = IF(@index_exists = 0, 'CREATE INDEX idx_exchange_credentials_principal_exchange_testnet ON exchange_credentials(principal_id, exchange, is_testnet)', 'SELECT "idx_exchange_credentials_principal_exchange_testnet exists"');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Make user_id nullable (marketplace users don't have studio accounts)
ALTER TABLE exchange_credentials 
MODIFY COLUMN user_id INT NULL;

-- Add constraint: either user_id OR principal_id must be set (not both null) (safe)
SELECT COUNT(*) INTO @constraint_exists FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'exchange_credentials' AND constraint_name = 'chk_user_or_principal';
SET @sql = IF(@constraint_exists = 0, 
    'ALTER TABLE exchange_credentials ADD CONSTRAINT chk_user_or_principal CHECK ((user_id IS NOT NULL AND principal_id IS NULL) OR (user_id IS NULL AND principal_id IS NOT NULL))',
    'SELECT "chk_user_or_principal constraint already exists" as status');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Comments (MySQL doesn't support COMMENT ON COLUMN, comments are in column definition above)
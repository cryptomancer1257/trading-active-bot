-- MySQL Migration 006: Add principal_id support to exchange_credentials table
-- Allows marketplace users to store credentials without studio account

USE bot_marketplace;

-- Add principal_id column
ALTER TABLE exchange_credentials 
ADD COLUMN principal_id VARCHAR(255) DEFAULT NULL AFTER user_id;

-- Add index for principal_id
CREATE INDEX idx_exchange_credentials_principal_id ON exchange_credentials(principal_id);

-- Composite index for principal_id + exchange + is_testnet
CREATE INDEX idx_exchange_credentials_principal_exchange_testnet 
ON exchange_credentials(principal_id, exchange, is_testnet);

-- Make user_id nullable
ALTER TABLE exchange_credentials 
MODIFY COLUMN user_id INT NULL;

-- MySQL does not enforce CHECK constraints by default, so this is for documentation only:
-- Either user_id OR principal_id must be set (not both null)
-- (You must enforce this logic in application code or with triggers if needed)

-- Add column comments (MySQL syntax)
ALTER TABLE exchange_credentials 
MODIFY COLUMN principal_id VARCHAR(255) DEFAULT NULL COMMENT 'ICP Principal ID for marketplace users without studio accounts';
ALTER TABLE exchange_credentials 
MODIFY COLUMN user_id INT NULL COMMENT 'Studio user ID (nullable for marketplace-only users)';

COMMIT;

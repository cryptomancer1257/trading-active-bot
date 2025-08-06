-- Migration 006: Add principal_id support to exchange_credentials table
-- This allows marketplace users to store credentials without studio account

-- Add principal_id column to exchange_credentials
ALTER TABLE exchange_credentials 
ADD COLUMN principal_id VARCHAR(255) DEFAULT NULL AFTER user_id;

-- Add index for principal_id queries
CREATE INDEX idx_exchange_credentials_principal_id ON exchange_credentials(principal_id);

-- Create composite index for principal_id + exchange + is_testnet
CREATE INDEX idx_exchange_credentials_principal_exchange_testnet 
ON exchange_credentials(principal_id, exchange, is_testnet);

-- Make user_id nullable (marketplace users don't have studio accounts)
ALTER TABLE exchange_credentials 
MODIFY COLUMN user_id INT NULL;

-- Add constraint: either user_id OR principal_id must be set (not both null)
ALTER TABLE exchange_credentials 
ADD CONSTRAINT chk_user_or_principal 
CHECK ((user_id IS NOT NULL AND principal_id IS NULL) OR 
       (user_id IS NULL AND principal_id IS NOT NULL));

-- Comments
COMMENT ON COLUMN exchange_credentials.principal_id IS 'ICP Principal ID for marketplace users without studio accounts';
COMMENT ON COLUMN exchange_credentials.user_id IS 'Studio user ID (nullable for marketplace-only users)';
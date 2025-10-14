-- Add credential_type column to exchange_credentials table to support SPOT/FUTURES trading
-- Migration: 034_add_credential_type_to_exchange_credentials.sql
-- Date: 2025-10-14

ALTER TABLE exchange_credentials 
ADD COLUMN credential_type ENUM('SPOT', 'FUTURES', 'MARGIN') DEFAULT 'SPOT' 
COMMENT 'Trading mode: SPOT, FUTURES, or MARGIN';

-- Set default to SPOT for existing records
UPDATE exchange_credentials 
SET credential_type = 'SPOT' 
WHERE credential_type IS NULL;


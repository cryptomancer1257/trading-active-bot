-- Migration: Add exchange_credentials table for multi-exchange API support
-- Run this script to add the new table

-- Create exchange_credentials table
CREATE TABLE exchange_credentials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    exchange ENUM('BINANCE', 'COINBASE', 'KRAKEN') NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    api_passphrase VARCHAR(255) NULL,
    is_testnet BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_validated TIMESTAMP NULL,
    validation_status VARCHAR(50) DEFAULT 'pending',
    
    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Unique constraint: one credential set per user per exchange per testnet/mainnet
    UNIQUE KEY idx_unique_user_exchange_testnet (user_id, exchange, is_testnet)
);

-- Add indexes for better performance
CREATE INDEX idx_exchange_credentials_user_id ON exchange_credentials(user_id);
CREATE INDEX idx_exchange_credentials_exchange ON exchange_credentials(exchange);
CREATE INDEX idx_exchange_credentials_validation_status ON exchange_credentials(validation_status);
CREATE INDEX idx_exchange_credentials_is_testnet ON exchange_credentials(is_testnet);

-- Add comments
ALTER TABLE exchange_credentials 
MODIFY COLUMN user_id INT NOT NULL COMMENT 'Reference to users table',
MODIFY COLUMN exchange ENUM('BINANCE', 'COINBASE', 'KRAKEN') NOT NULL COMMENT 'Exchange name',
MODIFY COLUMN api_key VARCHAR(255) NOT NULL COMMENT 'Exchange API key',
MODIFY COLUMN api_secret VARCHAR(255) NOT NULL COMMENT 'Exchange API secret',
MODIFY COLUMN api_passphrase VARCHAR(255) NULL COMMENT 'Exchange API passphrase (for Coinbase)',
MODIFY COLUMN is_testnet BOOLEAN DEFAULT TRUE COMMENT 'Whether credentials are for testnet (TRUE) or mainnet (FALSE)',
MODIFY COLUMN is_active BOOLEAN DEFAULT TRUE COMMENT 'Whether credentials are active',
MODIFY COLUMN validation_status VARCHAR(50) DEFAULT 'pending' COMMENT 'Validation status: pending, valid, invalid';

-- Sample query to check the table
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'bot_marketplace' 
AND TABLE_NAME = 'exchange_credentials'
ORDER BY ORDINAL_POSITION; 
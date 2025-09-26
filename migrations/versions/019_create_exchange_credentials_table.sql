-- Migration: Create developer_exchange_credentials table
-- This table stores encrypted API credentials for developers to connect to exchanges

CREATE TABLE IF NOT EXISTS developer_exchange_credentials (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    exchange_type ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') NOT NULL,
    credential_type ENUM('SPOT', 'FUTURES', 'MARGIN') NOT NULL,
    network_type ENUM('TESTNET', 'MAINNET') NOT NULL,
    
    name VARCHAR(100) NOT NULL,
    api_key TEXT NOT NULL,
    api_secret TEXT NOT NULL,
    passphrase VARCHAR(255) NULL,
    
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    last_used_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_user_exchange_type_network (user_id, exchange_type, credential_type, network_type),
    INDEX idx_user_default_credentials (user_id, is_default),
    
    UNIQUE KEY unique_user_default (user_id, exchange_type, credential_type, network_type, is_default)
);

-- Add constraint to ensure only one default credential per user/exchange/type/network combo
-- This is handled by the unique key above with is_default column

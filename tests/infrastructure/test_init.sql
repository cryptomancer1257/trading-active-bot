-- Simple schema for testing API key storage
-- Only create essential tables

USE trading_bot;

-- Create exchange_credentials table for API key storage
CREATE TABLE IF NOT EXISTS exchange_credentials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    principal_id VARCHAR(255) NOT NULL,
    exchange ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_secret_encrypted TEXT NOT NULL,
    is_testnet BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_principal_exchange_testnet (principal_id, exchange, is_testnet)
);

-- Simple users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simple migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert baseline migration
INSERT IGNORE INTO schema_migrations (version) VALUES ('001_initial_schema');
INSERT IGNORE INTO schema_migrations (version) VALUES ('test_baseline');

SELECT 'Test schema created successfully' as status;
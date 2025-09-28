-- Migration: Create transactions table for trading activities
-- Version: 023
-- Created: 2025-09-28

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    bot_id INT NULL,
    subscription_id INT NULL,
    
    -- Transaction details
    action VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity FLOAT NOT NULL,
    entry_price FLOAT NOT NULL,
    leverage INT DEFAULT 1,
    stop_loss FLOAT NULL,
    take_profit FLOAT NULL,
    order_id VARCHAR(100) NULL,
    confidence FLOAT NULL,
    reason TEXT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE SET NULL,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
    
    -- Indexes for better performance
    INDEX idx_transactions_user_id (user_id),
    INDEX idx_transactions_bot_id (bot_id),
    INDEX idx_transactions_subscription_id (subscription_id),
    INDEX idx_transactions_symbol (symbol),
    INDEX idx_transactions_created_at (created_at)
);

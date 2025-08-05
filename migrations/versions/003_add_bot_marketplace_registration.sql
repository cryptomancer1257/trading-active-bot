-- Migration: Add bot marketplace registration table
-- New marketplace registration system for developers
-- Date: 2024-12-19

CREATE TABLE IF NOT EXISTS register_bot (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_principal_id VARCHAR(255) NOT NULL,
    bot_id INT NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED') DEFAULT 'APPROVED',
    
    -- Marketplace details
    marketplace_name VARCHAR(255),
    marketplace_description TEXT,
    price_on_marketplace DECIMAL(10, 2),
    commission_rate FLOAT DEFAULT 0.10,
    
    -- Status tracking
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Marketplace settings
    is_featured BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    
    INDEX idx_user_principal_id (user_principal_id),
    INDEX idx_bot_id (bot_id),
    INDEX idx_status (status)
);

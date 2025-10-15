-- Migration: 037_create_user_plans_table.sql
-- Date: 2025-10-15
-- Description: Create user_plans table for managing Free and Pro subscriptions

CREATE TABLE IF NOT EXISTS user_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    
    -- Plan details
    plan_name ENUM('free', 'pro') NOT NULL DEFAULT 'free',
    price_usd DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    
    -- Limits
    max_bots INT NOT NULL DEFAULT 5,
    max_subscriptions_per_bot INT NOT NULL DEFAULT 5,
    allowed_environment ENUM('testnet', 'mainnet') NOT NULL DEFAULT 'testnet',
    publish_marketplace BOOLEAN NOT NULL DEFAULT 0,
    subscription_expiry_days INT NOT NULL DEFAULT 3,
    compute_quota_per_day INT NOT NULL DEFAULT 1000,
    
    -- Revenue share (percentage for developer)
    revenue_share_percentage DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    
    -- Plan status
    status ENUM('active', 'paused', 'expired') NOT NULL DEFAULT 'active',
    expiry_date DATETIME NULL,
    auto_renew BOOLEAN NOT NULL DEFAULT 0,
    
    -- Payment details
    payment_method ENUM('paypal', 'stripe', 'crypto') NULL,
    paypal_subscription_id VARCHAR(255) NULL,
    last_payment_id VARCHAR(255) NULL,
    last_payment_date DATETIME NULL,
    next_billing_date DATETIME NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_plan_name (plan_name),
    INDEX idx_status (status),
    INDEX idx_expiry_date (expiry_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create default Free plans for existing users
INSERT INTO user_plans (
    user_id, 
    plan_name, 
    price_usd, 
    max_bots, 
    max_subscriptions_per_bot,
    allowed_environment,
    publish_marketplace,
    subscription_expiry_days,
    compute_quota_per_day,
    revenue_share_percentage,
    status,
    auto_renew
)
SELECT 
    id,
    'free',
    0.00,
    5,
    5,
    'testnet',
    0,
    3,
    1000,
    0.00,
    'active',
    0
FROM users
WHERE NOT EXISTS (
    SELECT 1 FROM user_plans WHERE user_plans.user_id = users.id
);

-- Create plan_history table for tracking upgrades/downgrades
CREATE TABLE IF NOT EXISTS plan_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    plan_name ENUM('free', 'pro') NOT NULL,
    action ENUM('upgrade', 'downgrade', 'renew', 'cancel') NOT NULL,
    payment_id VARCHAR(255) NULL,
    amount_usd DECIMAL(10, 2) NULL,
    reason TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


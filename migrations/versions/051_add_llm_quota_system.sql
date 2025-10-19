-- Migration 051: Add LLM Quota System
-- Date: 2025-10-19
-- Purpose: Implement monthly quota system instead of daily quota

-- Add new quota fields to user_plans table
ALTER TABLE user_plans
ADD COLUMN llm_quota_total INT NOT NULL DEFAULT 720 COMMENT 'Total LLM API calls for subscription period',
ADD COLUMN llm_quota_used INT NOT NULL DEFAULT 0 COMMENT 'Used LLM API calls',
ADD COLUMN llm_quota_reset_at DATETIME NULL COMMENT 'When quota resets (subscription renewal)';

-- Create quota_topups table for additional quota purchases
CREATE TABLE IF NOT EXISTS quota_topups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    quota_amount INT NOT NULL COMMENT 'Number of API calls added',
    price_usd DECIMAL(10, 2) NOT NULL COMMENT 'Price paid',
    payment_method ENUM('paypal', 'stripe', 'crypto') NOT NULL,
    payment_id VARCHAR(255) NULL COMMENT 'PayPal order ID',
    payment_status VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT 'pending, completed, failed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    applied_at DATETIME NULL COMMENT 'When quota was added to user plan',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_quota_topups_user_id (user_id),
    INDEX idx_quota_topups_created_at (created_at),
    INDEX idx_quota_topups_payment_id (payment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Update existing plans with new quota values based on plan type
-- FREE: 24 calls/day * 30 days = 720
UPDATE user_plans SET llm_quota_total = 720, llm_quota_used = 0 WHERE plan_name = 'free';

-- PRO: 24 calls/day * 30 days = 720 (same as FREE)
UPDATE user_plans SET llm_quota_total = 720, llm_quota_used = 0 WHERE plan_name = 'pro';

-- ULTRA: 240 calls/day * 30 days = 7200
UPDATE user_plans SET llm_quota_total = 7200, llm_quota_used = 0 WHERE plan_name = 'ultra';

-- Set quota_reset_at to expiry_date or 30 days from now
UPDATE user_plans 
SET llm_quota_reset_at = COALESCE(expiry_date, DATE_ADD(NOW(), INTERVAL 30 DAY))
WHERE llm_quota_reset_at IS NULL;


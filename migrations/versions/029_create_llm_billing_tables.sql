-- =====================================================
-- Migration: Create LLM Billing and Subscription Tables
-- Version: 029
-- Description: Add support for Platform LLM subscriptions and BYOK (Bring Your Own Keys)
-- =====================================================

-- 1. Create llm_subscription_plans table
CREATE TABLE IF NOT EXISTS llm_subscription_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT 'Plan name: Free Trial, Starter, Pro, Enterprise',
    description TEXT COMMENT 'Plan description and features',
    
    -- Pricing
    price_per_month DECIMAL(10, 2) NOT NULL COMMENT 'Monthly subscription fee',
    currency VARCHAR(3) DEFAULT 'USD' COMMENT 'Currency code',
    
    -- Limits
    max_requests_per_month INT COMMENT 'Maximum LLM API calls per month',
    max_tokens_per_month BIGINT COMMENT 'Maximum tokens (input + output) per month',
    
    -- Features
    available_providers JSON COMMENT 'Available providers: ["openai", "claude", "gemini"]',
    available_models JSON COMMENT 'Available models per provider: {"openai": ["gpt-4o-mini"], ...}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    display_order INT DEFAULT 0,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_active (is_active),
    INDEX idx_display (display_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LLM subscription plans offered by platform';

-- 2. Create developer_llm_subscriptions table
CREATE TABLE IF NOT EXISTS developer_llm_subscriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    developer_id INT NOT NULL COMMENT 'FK to users.id',
    plan_id INT NOT NULL COMMENT 'FK to llm_subscription_plans.id',
    
    -- Subscription period
    status ENUM('ACTIVE', 'EXPIRED', 'CANCELLED') DEFAULT 'ACTIVE',
    start_date DATETIME NOT NULL COMMENT 'Subscription start date',
    end_date DATETIME NOT NULL COMMENT 'Subscription expiry date',
    auto_renew BOOLEAN DEFAULT TRUE COMMENT 'Auto-renew on expiry',
    
    -- Usage tracking
    requests_used INT DEFAULT 0 COMMENT 'Number of API requests used this period',
    tokens_used BIGINT DEFAULT 0 COMMENT 'Number of tokens used this period',
    last_reset_at DATETIME COMMENT 'When usage counters were last reset',
    
    -- Payment
    payment_status ENUM('PENDING', 'PAID', 'FAILED') DEFAULT 'PENDING',
    payment_id VARCHAR(255) COMMENT 'PayPal/Stripe transaction ID',
    payment_method VARCHAR(50) COMMENT 'Payment method used',
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (developer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES llm_subscription_plans(id),
    
    INDEX idx_developer_active (developer_id, status),
    INDEX idx_expiry (end_date),
    INDEX idx_payment (payment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Developer LLM subscription records';

-- 3. Create llm_usage_logs table
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    developer_id INT NOT NULL COMMENT 'FK to users.id',
    subscription_id INT COMMENT 'FK to developer_llm_subscriptions.id (NULL if BYOK)',
    bot_id INT COMMENT 'FK to bots.id',
    
    -- Request details
    provider VARCHAR(50) COMMENT 'LLM provider: openai, claude, gemini',
    model VARCHAR(100) COMMENT 'Model used: gpt-4o-mini, claude-3-5-sonnet, etc',
    request_type VARCHAR(50) COMMENT 'Request type: chat, analysis, signal_generation',
    
    -- Usage metrics
    input_tokens INT COMMENT 'Number of input tokens',
    output_tokens INT COMMENT 'Number of output tokens',
    total_tokens INT COMMENT 'Total tokens (input + output)',
    
    -- Cost (if using platform models)
    cost_usd DECIMAL(10, 6) COMMENT 'Cost in USD',
    
    -- Source
    source_type ENUM('PLATFORM', 'USER_CONFIGURED') COMMENT 'Platform subscription or BYOK',
    user_provider_id INT COMMENT 'FK to llm_providers.id if BYOK',
    
    -- Metadata
    request_duration_ms INT COMMENT 'Request duration in milliseconds',
    success BOOLEAN DEFAULT TRUE COMMENT 'Request success status',
    error_message TEXT COMMENT 'Error message if failed',
    
    -- Timestamp
    request_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (developer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES developer_llm_subscriptions(id) ON DELETE SET NULL,
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE SET NULL,
    FOREIGN KEY (user_provider_id) REFERENCES llm_providers(id) ON DELETE SET NULL,
    
    INDEX idx_developer_date (developer_id, request_at),
    INDEX idx_subscription (subscription_id),
    INDEX idx_bot (bot_id),
    INDEX idx_provider (provider),
    INDEX idx_source (source_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LLM usage logs for billing and analytics';

-- 4. Update llm_providers table (add display_order if not exists)
-- Note: llm_providers already has is_default, only need to add display_order
SET @col_exists = 0;
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.columns 
WHERE table_schema = DATABASE() 
  AND table_name = 'llm_providers' 
  AND column_name = 'display_order';

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE llm_providers ADD COLUMN display_order INT DEFAULT 0 COMMENT "Display order (lower = higher priority)"',
    'SELECT "Column display_order already exists"');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5. Seed default subscription plans
INSERT INTO llm_subscription_plans (name, description, price_per_month, currency, max_requests_per_month, max_tokens_per_month, available_providers, available_models, display_order) VALUES
(
    'Free Trial',
    'Try platform LLMs for free with limited usage. Perfect for testing and prototyping.',
    0.00,
    'USD',
    100,
    50000,
    JSON_ARRAY('openai'),
    JSON_OBJECT('openai', JSON_ARRAY('gpt-4o-mini')),
    1
),
(
    'Starter',
    'Basic LLM access for small bots. Includes OpenAI and Claude models with moderate limits.',
    10.00,
    'USD',
    5000,
    1000000,
    JSON_ARRAY('openai', 'claude'),
    JSON_OBJECT(
        'openai', JSON_ARRAY('gpt-4o-mini', 'gpt-4o'),
        'claude', JSON_ARRAY('claude-3-5-sonnet-20241022')
    ),
    2
),
(
    'Pro',
    'Advanced LLM access for production bots. Full access to OpenAI, Claude, and Gemini models.',
    50.00,
    'USD',
    30000,
    10000000,
    JSON_ARRAY('openai', 'claude', 'gemini'),
    JSON_OBJECT(
        'openai', JSON_ARRAY('gpt-4o-mini', 'gpt-4o', 'o1-preview'),
        'claude', JSON_ARRAY('claude-3-5-sonnet-20241022'),
        'gemini', JSON_ARRAY('gemini-1.5-pro')
    ),
    3
),
(
    'Enterprise',
    'Unlimited LLM access for large-scale operations. All models with highest priority support.',
    200.00,
    'USD',
    999999,
    999999999,
    JSON_ARRAY('openai', 'claude', 'gemini'),
    JSON_OBJECT(
        'openai', JSON_ARRAY('gpt-4o-mini', 'gpt-4o', 'o1-preview', 'o1'),
        'claude', JSON_ARRAY('claude-3-5-sonnet-20241022', 'claude-opus-4-20250514'),
        'gemini', JSON_ARRAY('gemini-1.5-pro', 'gemini-2.0-flash-exp')
    ),
    4
)
ON DUPLICATE KEY UPDATE
    updated_at = CURRENT_TIMESTAMP;

-- =====================================================
-- Rollback Instructions (if needed):
-- =====================================================
-- DROP TABLE IF EXISTS llm_usage_logs;
-- DROP TABLE IF EXISTS developer_llm_subscriptions;
-- DROP TABLE IF EXISTS llm_subscription_plans;
-- ALTER TABLE llm_providers DROP COLUMN IF EXISTS display_order;
-- =====================================================


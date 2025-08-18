-- PayPal Integration Migration (Safe Version)
-- Version: 009
-- Description: Add PayPal payment support with guest checkout (handles existing tables)

-- Create PayPal payments table (if not exists)
CREATE TABLE IF NOT EXISTS paypal_payments (
    id VARCHAR(255) PRIMARY KEY,
    order_id VARCHAR(255) UNIQUE NOT NULL,
    user_principal_id VARCHAR(255) NOT NULL,
    bot_id INT NOT NULL,
    
    -- Rental configuration
    duration_days INT NOT NULL,
    pricing_tier VARCHAR(50) NOT NULL,
    
    -- Pricing information
    amount_usd DECIMAL(10,2) NOT NULL,
    amount_icp_equivalent DECIMAL(18,8) NOT NULL,
    exchange_rate_usd_to_icp DECIMAL(18,8) NOT NULL,
    
    -- PayPal specific fields
    status ENUM('PENDING', 'APPROVED', 'COMPLETED', 'CANCELLED', 'FAILED', 'COMPLETED_PENDING_RENTAL') DEFAULT 'PENDING',
    paypal_order_id VARCHAR(255),
    paypal_payment_id VARCHAR(255),
    paypal_payer_id VARCHAR(255),
    paypal_approval_url VARCHAR(500),
    
    -- Payer information (for guest checkout)
    payer_email VARCHAR(255),
    payer_name VARCHAR(255),
    payer_country_code VARCHAR(5),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Rental linking
    rental_id VARCHAR(255),
    
    -- Error handling
    error_message TEXT,
    retry_count INT DEFAULT 0,
    
    -- Indexes
    INDEX idx_user_principal (user_principal_id),
    INDEX idx_bot_id (bot_id),
    INDEX idx_status (status),
    INDEX idx_paypal_order (paypal_order_id),
    INDEX idx_created_at (created_at),
    
    -- Foreign key
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE
);

-- Create PayPal configuration table (if not exists)
CREATE TABLE IF NOT EXISTS paypal_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    environment ENUM('sandbox', 'live') DEFAULT 'sandbox',
    client_id VARCHAR(255) NOT NULL,
    client_secret VARCHAR(500) NOT NULL,
    webhook_id VARCHAR(255),
    webhook_secret VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create PayPal webhook events table (if not exists)
CREATE TABLE IF NOT EXISTS paypal_webhook_events (
    id VARCHAR(255) PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSON NOT NULL,
    payment_id VARCHAR(255),
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_event_type (event_type),
    INDEX idx_payment_id (payment_id),
    INDEX idx_processed (processed),
    
    FOREIGN KEY (payment_id) REFERENCES paypal_payments(id) ON DELETE SET NULL
);

-- Check if columns exist before adding them to subscriptions table
SET @sql = '';

-- Check if paypal_payment_id column exists in subscriptions
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.columns 
WHERE table_name = 'subscriptions' 
  AND column_name = 'paypal_payment_id' 
  AND table_schema = DATABASE();

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE subscriptions ADD COLUMN paypal_payment_id VARCHAR(255) NULL', 
    'SELECT "paypal_payment_id column already exists" as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check if payment_method column exists in subscriptions
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.columns 
WHERE table_name = 'subscriptions' 
  AND column_name = 'payment_method' 
  AND table_schema = DATABASE();

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE subscriptions ADD COLUMN payment_method ENUM("STRIPE", "PAYPAL") DEFAULT "STRIPE"', 
    'SELECT "payment_method column already exists" as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check if columns exist before adding them to subscription_invoices table
-- Check if paypal_payment_id column exists in subscription_invoices
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.columns 
WHERE table_name = 'subscription_invoices' 
  AND column_name = 'paypal_payment_id' 
  AND table_schema = DATABASE();

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE subscription_invoices ADD COLUMN paypal_payment_id VARCHAR(255) NULL', 
    'SELECT "paypal_payment_id column already exists in subscription_invoices" as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Check if payment_method column exists in subscription_invoices
SELECT COUNT(*) INTO @col_exists 
FROM information_schema.columns 
WHERE table_name = 'subscription_invoices' 
  AND column_name = 'payment_method' 
  AND table_schema = DATABASE();

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE subscription_invoices ADD COLUMN payment_method ENUM("STRIPE", "PAYPAL") DEFAULT "STRIPE"', 
    'SELECT "payment_method column already exists in subscription_invoices" as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Create or replace PayPal payment summary view
CREATE OR REPLACE VIEW paypal_payment_summary AS
SELECT 
    pp.id,
    pp.user_principal_id,
    b.name as bot_name,
    pp.amount_usd,
    pp.status,
    pp.created_at,
    pp.completed_at,
    pp.rental_id,
    CASE 
        WHEN pp.status = 'COMPLETED' AND pp.rental_id IS NOT NULL THEN 'SUCCESS'
        WHEN pp.status = 'COMPLETED_PENDING_RENTAL' THEN 'NEEDS_MANUAL_REVIEW'
        WHEN pp.status = 'FAILED' OR pp.status = 'CANCELLED' THEN 'FAILED'
        ELSE 'PENDING'
    END as overall_status
FROM paypal_payments pp
JOIN bots b ON pp.bot_id = b.id;

-- Insert default sandbox configuration if not exists
INSERT IGNORE INTO paypal_config (environment, client_id, client_secret, is_active) 
VALUES ('sandbox', 'REPLACE_WITH_SANDBOX_CLIENT_ID', 'REPLACE_WITH_SANDBOX_CLIENT_SECRET', TRUE);

-- Show completion message
SELECT 'PayPal integration migration completed successfully!' as message;

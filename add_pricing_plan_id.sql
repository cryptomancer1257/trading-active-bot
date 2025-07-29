-- Migration: Add pricing_plan_id column to subscriptions table
-- Date: 2025-07-29

-- Add pricing_plan_id column to subscriptions table
ALTER TABLE subscriptions 
ADD COLUMN pricing_plan_id INT NULL,
ADD CONSTRAINT fk_subscriptions_pricing_plan 
FOREIGN KEY (pricing_plan_id) REFERENCES bot_pricing_plans(id) ON DELETE SET NULL;

-- Add billing_cycle column if not exists
ALTER TABLE subscriptions 
ADD COLUMN billing_cycle VARCHAR(20) DEFAULT 'MONTHLY';

-- Add next_billing_date column if not exists  
ALTER TABLE subscriptions 
ADD COLUMN next_billing_date DATETIME NULL;

-- Add auto_renew column if not exists
ALTER TABLE subscriptions 
ADD COLUMN auto_renew BOOLEAN DEFAULT TRUE;

-- Update existing subscriptions to have default values
UPDATE subscriptions 
SET billing_cycle = 'MONTHLY', 
    auto_renew = TRUE 
WHERE billing_cycle IS NULL;

-- Create bot_pricing_plans table if not exists
CREATE TABLE IF NOT EXISTS bot_pricing_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bot_id INT NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    plan_description TEXT,
    price_per_month DECIMAL(10,2) DEFAULT 0.00,
    price_per_year DECIMAL(10,2) DEFAULT 0.00,
    price_per_quarter DECIMAL(10,2) DEFAULT 0.00,
    max_trading_pairs INT DEFAULT 1,
    max_daily_trades INT DEFAULT 10,
    max_position_size DECIMAL(5,2) DEFAULT 0.10,
    advanced_features JSON,
    trial_days INT DEFAULT 0,
    trial_trades_limit INT DEFAULT 5,
    is_active BOOLEAN DEFAULT TRUE,
    is_popular BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE
);

-- Create bot_promotions table if not exists
CREATE TABLE IF NOT EXISTS bot_promotions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bot_id INT NOT NULL,
    promotion_code VARCHAR(50) UNIQUE NOT NULL,
    promotion_name VARCHAR(100) NOT NULL,
    promotion_description TEXT,
    discount_type VARCHAR(20) NOT NULL,
    discount_value DECIMAL(10,2) NOT NULL,
    max_uses INT DEFAULT 100,
    used_count INT DEFAULT 0,
    valid_from DATETIME,
    valid_until DATETIME,
    min_subscription_months INT DEFAULT 1,
    applicable_plans JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create subscription_invoices table if not exists
CREATE TABLE IF NOT EXISTS subscription_invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subscription_id INT NOT NULL,
    user_id INT NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    base_price DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    final_amount DECIMAL(10,2) NOT NULL,
    billing_period_start DATETIME,
    billing_period_end DATETIME,
    status VARCHAR(20) DEFAULT 'PENDING',
    payment_method VARCHAR(50),
    payment_date DATETIME,
    promotion_code VARCHAR(50),
    promotion_discount DECIMAL(10,2) DEFAULT 0.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert default pricing plans for existing bots
INSERT INTO bot_pricing_plans (bot_id, plan_name, plan_description, price_per_month, is_active)
SELECT 
    id as bot_id,
    'Free Plan' as plan_name,
    'Basic trading features with limited functionality' as plan_description,
    0.00 as price_per_month,
    TRUE as is_active
FROM bots 
WHERE id NOT IN (SELECT DISTINCT bot_id FROM bot_pricing_plans);

-- Update existing subscriptions to use default pricing plan
UPDATE subscriptions s
JOIN bots b ON s.bot_id = b.id
JOIN bot_pricing_plans p ON b.id = p.bot_id AND p.plan_name = 'Free Plan'
SET s.pricing_plan_id = p.id
WHERE s.pricing_plan_id IS NULL;

-- Add indexes for better performance
CREATE INDEX idx_subscriptions_pricing_plan ON subscriptions(pricing_plan_id);
CREATE INDEX idx_bot_pricing_plans_bot_id ON bot_pricing_plans(bot_id);
CREATE INDEX idx_bot_promotions_bot_id ON bot_promotions(bot_id);
CREATE INDEX idx_subscription_invoices_subscription_id ON subscription_invoices(subscription_id); 
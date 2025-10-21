-- Migration 056: Create plan_pricing_templates table
-- Date: 2025-10-21
-- Description: Create table to manage pricing templates for each plan type

-- Create plan_pricing_templates table
CREATE TABLE IF NOT EXISTS plan_pricing_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_name ENUM('free', 'pro', 'ultra') NOT NULL UNIQUE,
    
    -- Pricing
    original_price_usd DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    discount_percentage DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    
    -- Campaign details
    campaign_name VARCHAR(255) NULL,
    campaign_active BOOLEAN NOT NULL DEFAULT TRUE,
    campaign_start_date TIMESTAMP NULL,
    campaign_end_date TIMESTAMP NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_plan_pricing_plan_name (plan_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default pricing templates with 50% Quantum Launch discount
INSERT INTO plan_pricing_templates (plan_name, original_price_usd, discount_percentage, campaign_name, campaign_active) VALUES
('free', 0.00, 0.00, NULL, TRUE),
('pro', 40.00, 50.00, 'Quantum Launch Campaign', TRUE),
('ultra', 100.00, 50.00, 'Quantum Launch Campaign', TRUE)
ON DUPLICATE KEY UPDATE plan_name=plan_name;


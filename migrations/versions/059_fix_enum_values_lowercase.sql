-- =====================================================
-- Production Migration: Fix Enum Values to Lowercase
-- Version: 059
-- Date: 2025-10-21
-- Description: Fix all enum values in database to match Python models.py (lowercase)
--              This resolves 500 Internal Server Errors caused by enum mismatch
-- =====================================================

USE bot_marketplace;

-- =====================================================
-- 1. FIX plan_pricing_templates TABLE
-- =====================================================

-- Add missing current_price_usd column
ALTER TABLE plan_pricing_templates 
ADD COLUMN IF NOT EXISTS current_price_usd DECIMAL(10,2) NOT NULL DEFAULT 0.00 
AFTER discount_percentage;

-- Update current_price_usd based on discount calculation
UPDATE plan_pricing_templates 
SET current_price_usd = original_price_usd * (1 - discount_percentage / 100);

-- Fix plan_name enum to lowercase
ALTER TABLE plan_pricing_templates 
MODIFY COLUMN plan_name ENUM('free', 'pro', 'ultra') NOT NULL;

-- Update existing data to lowercase
UPDATE plan_pricing_templates 
SET plan_name = LOWER(plan_name);

-- =====================================================
-- 2. FIX user_plans TABLE
-- =====================================================

-- Fix plan_name enum
ALTER TABLE user_plans 
MODIFY COLUMN plan_name ENUM('free', 'pro', 'ultra') NOT NULL DEFAULT 'free';

-- Fix status enum
ALTER TABLE user_plans 
MODIFY COLUMN status ENUM('active', 'paused', 'expired') NOT NULL;

-- Fix allowed_environment enum
ALTER TABLE user_plans 
MODIFY COLUMN allowed_environment ENUM('testnet', 'mainnet') NOT NULL;

-- Fix payment_method enum
ALTER TABLE user_plans 
MODIFY COLUMN payment_method ENUM('stripe', 'paypal', 'trial');

-- Update existing data to lowercase
UPDATE user_plans SET plan_name = LOWER(plan_name);
UPDATE user_plans SET status = LOWER(status);
UPDATE user_plans SET allowed_environment = LOWER(allowed_environment);
UPDATE user_plans SET payment_method = LOWER(payment_method) WHERE payment_method IS NOT NULL;

-- =====================================================
-- 3. FIX plan_history TABLE
-- =====================================================

-- Fix action enum
ALTER TABLE plan_history 
MODIFY COLUMN action ENUM('upgrade', 'downgrade', 'renew', 'cancel') NOT NULL;

-- Update existing data to lowercase
UPDATE plan_history SET action = LOWER(action);

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify plan_pricing_templates
SELECT 
    'plan_pricing_templates' as table_name,
    plan_name, 
    original_price_usd,
    discount_percentage,
    current_price_usd,
    campaign_name,
    campaign_active
FROM plan_pricing_templates
ORDER BY id;

-- Verify user_plans structure
SELECT 
    'user_plans' as table_name,
    COUNT(*) as total_plans,
    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_plans
FROM user_plans;

-- Success message
SELECT '✅ Migration completed successfully!' as status;

-- =====================================================
-- ROLLBACK (if needed)
-- =====================================================
-- To rollback to UPPERCASE enums, run:
-- 
-- ALTER TABLE plan_pricing_templates MODIFY COLUMN plan_name ENUM('FREE', 'PRO', 'ULTRA') NOT NULL;
-- UPDATE plan_pricing_templates SET plan_name = UPPER(plan_name);
-- 
-- ALTER TABLE user_plans MODIFY COLUMN plan_name ENUM('FREE', 'PRO', 'ULTRA') NOT NULL DEFAULT 'FREE';
-- ALTER TABLE user_plans MODIFY COLUMN status ENUM('ACTIVE', 'PAUSED', 'EXPIRED') NOT NULL;
-- ALTER TABLE user_plans MODIFY COLUMN allowed_environment ENUM('TESTNET', 'MAINNET') NOT NULL;
-- ALTER TABLE user_plans MODIFY COLUMN payment_method ENUM('STRIPE', 'PAYPAL', 'TRIAL');
-- UPDATE user_plans SET plan_name = UPPER(plan_name);
-- UPDATE user_plans SET status = UPPER(status);
-- UPDATE user_plans SET allowed_environment = UPPER(allowed_environment);
-- UPDATE user_plans SET payment_method = UPPER(payment_method) WHERE payment_method IS NOT NULL;
-- 
-- ALTER TABLE plan_history MODIFY COLUMN action ENUM('UPGRADE', 'DOWNGRADE', 'RENEW', 'CANCEL') NOT NULL;
-- UPDATE plan_history SET action = UPPER(action);
-- =====================================================

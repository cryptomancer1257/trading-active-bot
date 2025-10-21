-- Migration 055: Add pricing discount fields to user_plans table
-- Date: 2025-10-21
-- Description: Add original_price_usd and discount_percentage for special pricing campaigns

-- Add original_price_usd column
SET @col_exists = (SELECT COUNT(*) 
                   FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = DATABASE() 
                   AND TABLE_NAME = 'user_plans' 
                   AND COLUMN_NAME = 'original_price_usd');

SET @sql = IF(@col_exists = 0, 
              'ALTER TABLE user_plans ADD COLUMN original_price_usd DECIMAL(10, 2) NOT NULL DEFAULT 0.00 AFTER price_usd', 
              'SELECT "Column original_price_usd already exists" AS message');
              
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add discount_percentage column
SET @col_exists = (SELECT COUNT(*) 
                   FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = DATABASE() 
                   AND TABLE_NAME = 'user_plans' 
                   AND COLUMN_NAME = 'discount_percentage');

SET @sql = IF(@col_exists = 0, 
              'ALTER TABLE user_plans ADD COLUMN discount_percentage DECIMAL(5, 2) NOT NULL DEFAULT 0.00 AFTER original_price_usd', 
              'SELECT "Column discount_percentage already exists" AS message');
              
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Initialize original_price_usd with current price_usd for existing plans
UPDATE user_plans 
SET original_price_usd = price_usd
WHERE original_price_usd = 0.00;

-- Apply 50% discount for Quantum Launch Campaign
UPDATE user_plans 
SET discount_percentage = 50.00,
    original_price_usd = price_usd * 2,  -- Set original price to 2x current (since we're giving 50% off)
    price_usd = price_usd  -- Keep current discounted price
WHERE plan_name IN ('pro', 'ultra') AND discount_percentage = 0.00;


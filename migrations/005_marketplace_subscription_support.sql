-- Migration: Add marketplace user support to subscriptions
-- Description: Allow subscriptions without studio user account, store marketplace contact info

USE bot_marketplace;

-- Add marketplace contact fields to subscriptions table
ALTER TABLE subscriptions 
ADD COLUMN marketplace_user_email VARCHAR(255) NULL COMMENT 'Email from marketplace user',
ADD COLUMN marketplace_user_telegram VARCHAR(255) NULL COMMENT 'Telegram from marketplace user', 
ADD COLUMN marketplace_user_discord VARCHAR(255) NULL COMMENT 'Discord from marketplace user',
ADD COLUMN is_marketplace_subscription BOOLEAN DEFAULT FALSE COMMENT 'True if subscription from marketplace without studio account',
ADD COLUMN marketplace_subscription_start DATETIME NULL COMMENT 'Start time specified by marketplace',
ADD COLUMN marketplace_subscription_end DATETIME NULL COMMENT 'End time specified by marketplace';

-- Make user_id nullable for marketplace subscriptions
ALTER TABLE subscriptions 
MODIFY COLUMN user_id INT NULL COMMENT 'Studio user ID (NULL for marketplace-only subscriptions)';

-- Add index for marketplace subscriptions
ALTER TABLE subscriptions 
ADD INDEX idx_marketplace_subscription (is_marketplace_subscription, user_principal_id),
ADD INDEX idx_marketplace_email (marketplace_user_email);

-- Update existing subscriptions to mark them as non-marketplace
UPDATE subscriptions 
SET is_marketplace_subscription = FALSE 
WHERE user_id IS NOT NULL;

COMMIT;
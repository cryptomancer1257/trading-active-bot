-- Migration: Add marketplace user support to subscriptions (SAFE VERSION)
-- Description: Allow subscriptions without studio user account, store marketplace contact info

USE bot_marketplace;

-- Add marketplace contact fields one by one with error handling
-- Email field
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'marketplace_user_email';

SET @sql = IF(@exists = 0, 
    'ALTER TABLE subscriptions ADD COLUMN marketplace_user_email VARCHAR(255) NULL COMMENT "Email from marketplace user"',
    'SELECT "marketplace_user_email already exists" as status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Telegram field
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'marketplace_user_telegram';

SET @sql = IF(@exists = 0, 
    'ALTER TABLE subscriptions ADD COLUMN marketplace_user_telegram VARCHAR(255) NULL COMMENT "Telegram from marketplace user"',
    'SELECT "marketplace_user_telegram already exists" as status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Discord field
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'marketplace_user_discord';

SET @sql = IF(@exists = 0, 
    'ALTER TABLE subscriptions ADD COLUMN marketplace_user_discord VARCHAR(255) NULL COMMENT "Discord from marketplace user"',
    'SELECT "marketplace_user_discord already exists" as status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Marketplace subscription flag
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'is_marketplace_subscription';

SET @sql = IF(@exists = 0, 
    'ALTER TABLE subscriptions ADD COLUMN is_marketplace_subscription BOOLEAN DEFAULT FALSE COMMENT "True if subscription from marketplace without studio account"',
    'SELECT "is_marketplace_subscription already exists" as status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Start time field
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'marketplace_subscription_start';

SET @sql = IF(@exists = 0, 
    'ALTER TABLE subscriptions ADD COLUMN marketplace_subscription_start DATETIME NULL COMMENT "Start time specified by marketplace"',
    'SELECT "marketplace_subscription_start already exists" as status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- End time field
SELECT COUNT(*) INTO @exists FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'marketplace_subscription_end';

SET @sql = IF(@exists = 0, 
    'ALTER TABLE subscriptions ADD COLUMN marketplace_subscription_end DATETIME NULL COMMENT "End time specified by marketplace"',
    'SELECT "marketplace_subscription_end already exists" as status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Make user_id nullable for marketplace subscriptions (only if not already nullable)
SELECT IS_NULLABLE INTO @nullable FROM INFORMATION_SCHEMA.COLUMNS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND column_name = 'user_id';

SET @sql = IF(@nullable = 'NO', 
    'ALTER TABLE subscriptions MODIFY COLUMN user_id INT NULL COMMENT "Studio user ID (NULL for marketplace-only subscriptions)"',
    'SELECT "user_id already nullable" as status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add indexes (ignore if exists)
SET @sql = 'CREATE INDEX idx_marketplace_subscription ON subscriptions(is_marketplace_subscription, user_principal_id)';
SET @sql = CONCAT('CREATE INDEX IF NOT EXISTS idx_marketplace_subscription ON subscriptions(is_marketplace_subscription, user_principal_id)');

-- For MySQL, we need to check if index exists first
SELECT COUNT(*) INTO @index_exists FROM INFORMATION_SCHEMA.STATISTICS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND index_name = 'idx_marketplace_subscription';

SET @sql = IF(@index_exists = 0, 
    'CREATE INDEX idx_marketplace_subscription ON subscriptions(is_marketplace_subscription, user_principal_id)',
    'SELECT "idx_marketplace_subscription already exists" as status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Email index
SELECT COUNT(*) INTO @index_exists FROM INFORMATION_SCHEMA.STATISTICS 
WHERE table_schema = 'bot_marketplace' AND table_name = 'subscriptions' AND index_name = 'idx_marketplace_email';

SET @sql = IF(@index_exists = 0, 
    'CREATE INDEX idx_marketplace_email ON subscriptions(marketplace_user_email)',
    'SELECT "idx_marketplace_email already exists" as status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Update existing subscriptions to mark them as non-marketplace (safe update)
UPDATE subscriptions 
SET is_marketplace_subscription = COALESCE(is_marketplace_subscription, FALSE)
WHERE user_id IS NOT NULL AND (is_marketplace_subscription IS NULL OR is_marketplace_subscription = FALSE);

COMMIT;

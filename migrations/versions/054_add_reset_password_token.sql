-- Migration 054: Add password reset token fields to users table
-- Date: 2025-01-20

-- Check and add reset password token fields to users table
-- MySQL doesn't support IF NOT EXISTS in ALTER TABLE, so we use a different approach

-- Add reset_password_token column if it doesn't exist
SET @col_exists = (SELECT COUNT(*) 
                   FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = DATABASE() 
                   AND TABLE_NAME = 'users' 
                   AND COLUMN_NAME = 'reset_password_token');

SET @sql = IF(@col_exists = 0, 
              'ALTER TABLE users ADD COLUMN reset_password_token VARCHAR(255) NULL', 
              'SELECT "Column reset_password_token already exists" AS message');
              
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add reset_password_token_expires column if it doesn't exist
SET @col_exists = (SELECT COUNT(*) 
                   FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = DATABASE() 
                   AND TABLE_NAME = 'users' 
                   AND COLUMN_NAME = 'reset_password_token_expires');

SET @sql = IF(@col_exists = 0, 
              'ALTER TABLE users ADD COLUMN reset_password_token_expires TIMESTAMP NULL', 
              'SELECT "Column reset_password_token_expires already exists" AS message');
              
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add index on reset_password_token for faster lookups (if not exists)
SET @index_exists = (SELECT COUNT(*) 
                     FROM INFORMATION_SCHEMA.STATISTICS 
                     WHERE TABLE_SCHEMA = DATABASE() 
                     AND TABLE_NAME = 'users' 
                     AND INDEX_NAME = 'idx_users_reset_password_token');

SET @sql = IF(@index_exists = 0, 
              'CREATE INDEX idx_users_reset_password_token ON users(reset_password_token)', 
              'SELECT "Index idx_users_reset_password_token already exists" AS message');
              
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

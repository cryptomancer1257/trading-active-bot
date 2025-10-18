-- Migration: Add telegram_username and discord_username to users table
-- Date: 2025-10-18
-- Description: Allow developers to set their Telegram and Discord usernames for notifications

ALTER TABLE users 
ADD COLUMN telegram_username VARCHAR(255) NULL,
ADD COLUMN discord_username VARCHAR(255) NULL;

-- Add indexes for better performance
CREATE INDEX idx_users_telegram_username ON users(telegram_username);
CREATE INDEX idx_users_discord_username ON users(discord_username);

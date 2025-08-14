USE bot_marketplace;

ALTER TABLE user_settings
ADD COLUMN discord_user_id VARCHAR(255) COMMENT 'Discord user ID',
ADD COLUMN telegram_chat_id VARCHAR(255) COMMENT 'Telegram chat ID';

COMMIT;
-- Migration: Add Telegram and Discord IDs to user_settings
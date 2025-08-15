-- Migration: delete 3 column marketplace_user_email, marketplace_user_telegram, marketplace_user_discord from subscriptions (MySQL)
ALTER TABLE subscriptions DROP COLUMN marketplace_user_email;
ALTER TABLE subscriptions DROP COLUMN marketplace_user_telegram;
ALTER TABLE subscriptions DROP COLUMN marketplace_user_discord;
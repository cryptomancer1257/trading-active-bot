-- Migration: Fix payment_method column to support TRIAL value
-- Date: 2025-09-28
-- Description: Change payment_method from VARCHAR(6) to VARCHAR(12) to support 'TRIAL' value

-- For MySQL
ALTER TABLE subscriptions MODIFY COLUMN payment_method VARCHAR(12);

-- For SQLite (if needed)
-- ALTER TABLE subscriptions RENAME TO subscriptions_old;
-- CREATE TABLE subscriptions AS SELECT * FROM subscriptions_old;
-- DROP TABLE subscriptions_old;

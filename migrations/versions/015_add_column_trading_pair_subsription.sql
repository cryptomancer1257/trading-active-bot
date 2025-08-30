USE bot_marketplace;

ALTER TABLE subscriptions
ADD COLUMN trading_pair VARCHAR(25) COMMENT 'Discord user ID';
COMMIT;
-- Migration: Enforce uniqueness on register_bot
-- 1) Unique (user_principal_id, bot_id)
-- 2) Unique api_key

USE bot_marketplace;

ALTER TABLE register_bot
  ADD UNIQUE KEY uq_register_bot_principal_bot (user_principal_id, bot_id);

ALTER TABLE register_bot
  ADD UNIQUE KEY uq_register_bot_api_key (api_key);

COMMIT;



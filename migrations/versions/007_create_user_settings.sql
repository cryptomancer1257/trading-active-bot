-- Migration: Create user_settings table for Marketplace Settings
-- Description: Persist user contact, social channels, default signal channel,
--              and display preferences keyed by principal_id (unique)
-- Date: 2025-08-10

USE bot_marketplace;

CREATE TABLE IF NOT EXISTS user_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    principal_id VARCHAR(255) NOT NULL,

    -- Contact
    email VARCHAR(255),

    -- Social channels
    social_telegram VARCHAR(255),
    social_discord VARCHAR(255),
    social_twitter VARCHAR(255),
    social_whatsapp VARCHAR(255),

    -- Default signal channel
    default_channel VARCHAR(50) DEFAULT 'email',

    -- Display preferences
    display_dark_mode BOOLEAN DEFAULT FALSE,
    display_currency VARCHAR(10) DEFAULT 'ICP',
    display_language VARCHAR(10) DEFAULT 'en',
    display_timezone VARCHAR(64) DEFAULT 'UTC',

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_user_settings_principal (principal_id)
);

-- Optional supporting index (redundant with UNIQUE but explicit for clarity)
-- CREATE INDEX idx_user_settings_principal ON user_settings(principal_id);

COMMIT;



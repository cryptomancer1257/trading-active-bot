-- Migration: Create Feature Flags System
-- Description: Add feature flags table for controlling feature visibility
-- Created: 2025-01-20

-- Drop existing table if exists (to ensure clean schema)
DROP TABLE IF EXISTS feature_flags;

-- Create feature_flags table
CREATE TABLE feature_flags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flag_key VARCHAR(100) NOT NULL UNIQUE,
    flag_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_flag_key (flag_key),
    INDEX idx_is_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert initial feature flags
INSERT INTO feature_flags (flag_key, flag_name, description, is_enabled) VALUES
('marketplace_publish_bot', 'Marketplace Bot Publishing', 'Allow developers to publish bots to marketplace', TRUE),
('marketplace_republish_bot', 'Marketplace Bot Re-Publishing', 'Allow developers to re-publish/update bots in marketplace', TRUE),
('llm_quota_system', 'LLM Quota System', 'Enable LLM quota tracking and limits', TRUE),
('advanced_analytics', 'Advanced Analytics', 'Enable advanced analytics dashboard', FALSE),
('multi_exchange_trading', 'Multi-Exchange Trading', 'Allow trading across multiple exchanges simultaneously', FALSE)
ON DUPLICATE KEY UPDATE flag_key=flag_key;


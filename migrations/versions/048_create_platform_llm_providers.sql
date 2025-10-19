-- Migration: Create platform LLM providers table
-- Description: Add platform-managed LLM providers (admin-only)
-- Date: 2024-10-19

-- Create platform_llm_providers table
CREATE TABLE IF NOT EXISTS platform_llm_providers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provider_type ENUM('OPENAI', 'ANTHROPIC', 'GEMINI', 'GROQ', 'COHERE') NOT NULL,
    name VARCHAR(255) NOT NULL,
    api_key TEXT NOT NULL COMMENT 'Encrypted API key',
    base_url VARCHAR(500) DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT DEFAULT NULL COMMENT 'Admin user ID who created this',
    UNIQUE KEY unique_provider_name (name),
    INDEX idx_provider_type (provider_type),
    INDEX idx_is_active (is_active),
    INDEX idx_is_default (is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create platform_llm_models table
CREATE TABLE IF NOT EXISTS platform_llm_models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provider_id INT NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    max_tokens INT DEFAULT NULL,
    cost_per_1k_tokens DECIMAL(10, 6) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES platform_llm_providers(id) ON DELETE CASCADE,
    UNIQUE KEY unique_provider_model (provider_id, model_name),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default platform providers (admin should update API keys)
INSERT IGNORE INTO platform_llm_providers (provider_type, name, api_key, is_active, is_default) VALUES
('OPENAI', 'Platform OpenAI', 'REPLACE_WITH_REAL_API_KEY', TRUE, TRUE),
('ANTHROPIC', 'Platform Claude', 'REPLACE_WITH_REAL_API_KEY', FALSE, FALSE),
('GEMINI', 'Platform Gemini', 'REPLACE_WITH_REAL_API_KEY', FALSE, FALSE);

-- Insert default models for OpenAI
INSERT IGNORE INTO platform_llm_models (provider_id, model_name, display_name, is_active, max_tokens, cost_per_1k_tokens)
SELECT id, 'gpt-4o', 'GPT-4o', TRUE, 128000, 0.0025 FROM platform_llm_providers WHERE provider_type = 'OPENAI' LIMIT 1;

INSERT IGNORE INTO platform_llm_models (provider_id, model_name, display_name, is_active, max_tokens, cost_per_1k_tokens)
SELECT id, 'gpt-4o-mini', 'GPT-4o Mini', TRUE, 128000, 0.00015 FROM platform_llm_providers WHERE provider_type = 'OPENAI' LIMIT 1;

-- Add deprecated column to existing llm_providers table (if not exists)
-- Note: MySQL doesn't support IF NOT EXISTS for ADD COLUMN, so we check manually
SET @col_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'llm_providers' 
    AND COLUMN_NAME = 'deprecated'
);

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE llm_providers ADD COLUMN deprecated BOOLEAN DEFAULT FALSE COMMENT ''User-managed providers are deprecated, use platform providers instead''',
    'SELECT ''Column deprecated already exists'' AS message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Mark all existing user providers as deprecated
UPDATE llm_providers SET deprecated = TRUE WHERE 1=1;


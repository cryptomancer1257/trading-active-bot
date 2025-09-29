-- Create LLM Providers and Models tables
-- Migration: 025_create_llm_providers_tables.sql

-- Create llm_providers table
CREATE TABLE IF NOT EXISTS llm_providers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    provider_type VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    api_key TEXT NOT NULL,
    base_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create llm_models table
CREATE TABLE IF NOT EXISTS llm_models (
    id INT PRIMARY KEY AUTO_INCREMENT,
    provider_id INT NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    max_tokens INT,
    cost_per_1k_tokens DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES llm_providers (id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX idx_llm_providers_user_id ON llm_providers(user_id);
CREATE INDEX idx_llm_providers_provider_type ON llm_providers(provider_type);
CREATE INDEX idx_llm_providers_is_active ON llm_providers(is_active);
CREATE INDEX idx_llm_providers_is_default ON llm_providers(is_default);

CREATE INDEX idx_llm_models_provider_id ON llm_models(provider_id);
CREATE INDEX idx_llm_models_model_name ON llm_models(model_name);
CREATE INDEX idx_llm_models_is_active ON llm_models(is_active);

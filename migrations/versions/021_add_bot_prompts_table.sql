-- Migration: Add bot_prompts table for bot-prompt relationships
-- Version: 021
-- Created: 2024-01-XX

CREATE TABLE IF NOT EXISTS bot_prompts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bot_id INT NOT NULL,
    prompt_id INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0,
    custom_override TEXT,
    attached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    FOREIGN KEY (prompt_id) REFERENCES prompt_templates(id) ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate attachments
    UNIQUE(bot_id, prompt_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_bot_prompts_bot_id ON bot_prompts(bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_prompts_prompt_id ON bot_prompts(prompt_id);
CREATE INDEX IF NOT EXISTS idx_bot_prompts_active ON bot_prompts(is_active);
CREATE INDEX IF NOT EXISTS idx_bot_prompts_priority ON bot_prompts(priority);
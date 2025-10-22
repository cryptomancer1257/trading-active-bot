-- Migration: Fix bot_prompts foreign key to reference llm_prompt_templates
-- Version: 060
-- Created: 2025-01-21
-- Description: Fix foreign key constraint - should reference llm_prompt_templates, not prompt_templates

-- Drop existing foreign key constraint
ALTER TABLE bot_prompts 
DROP FOREIGN KEY bot_prompts_ibfk_2;

-- Add correct foreign key constraint pointing to llm_prompt_templates
ALTER TABLE bot_prompts 
ADD CONSTRAINT bot_prompts_ibfk_2 
FOREIGN KEY (prompt_id) REFERENCES llm_prompt_templates(id) ON DELETE CASCADE;

-- Verify the change
SHOW CREATE TABLE bot_prompts;


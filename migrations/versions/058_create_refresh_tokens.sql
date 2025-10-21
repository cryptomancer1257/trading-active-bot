-- Migration 058: Create refresh_tokens table
-- Date: 2025-10-21
-- Description: Add refresh tokens table for secure JWT authentication with token rotation

-- Create refresh_tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(500) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at DATETIME NULL,
    
    -- Device/session info for security
    user_agent VARCHAR(500) NULL,
    ip_address VARCHAR(45) NULL,
    
    -- Foreign key
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes for performance
    INDEX idx_refresh_tokens_user_id (user_id),
    INDEX idx_refresh_tokens_token (token),
    INDEX idx_refresh_tokens_expires_at (expires_at),
    INDEX idx_refresh_tokens_is_revoked (is_revoked)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add comment
ALTER TABLE refresh_tokens COMMENT = 'Stores refresh tokens for JWT authentication with token rotation';


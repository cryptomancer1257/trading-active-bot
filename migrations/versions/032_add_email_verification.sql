-- Migration: Add email verification fields to users table
-- Created: 2025-01-13

-- Add email verification columns
ALTER TABLE users 
ADD COLUMN email_verified BOOLEAN DEFAULT FALSE AFTER is_active,
ADD COLUMN verification_token VARCHAR(255) NULL AFTER email_verified,
ADD COLUMN verification_token_expires DATETIME NULL AFTER verification_token;

-- Create index on verification_token for faster lookups
CREATE INDEX idx_users_verification_token ON users(verification_token);

-- For existing users (especially those from Google OAuth), set email_verified to TRUE
-- This ensures backward compatibility
UPDATE users 
SET email_verified = TRUE 
WHERE email IS NOT NULL;

-- Note: New registrations via email/password will have email_verified = FALSE by default
-- Google OAuth users will be set to email_verified = TRUE upon creation


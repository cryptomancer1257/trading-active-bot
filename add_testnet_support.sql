-- Migration: Add testnet and trial support to subscriptions table
-- Run this script to update your database

-- Add new columns for testnet and trial support
ALTER TABLE subscriptions 
ADD COLUMN is_testnet BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN is_trial BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN trial_expires_at TIMESTAMP NULL;

-- Add indexes for better query performance
CREATE INDEX idx_subscriptions_is_testnet ON subscriptions(is_testnet);
CREATE INDEX idx_subscriptions_is_trial ON subscriptions(is_trial);
CREATE INDEX idx_subscriptions_trial_expires ON subscriptions(trial_expires_at);

-- Update existing subscriptions to use testnet by default (for safety)
UPDATE subscriptions SET is_testnet = TRUE WHERE is_testnet IS NULL OR is_testnet = FALSE;

COMMENT ON COLUMN subscriptions.is_testnet IS 'Whether this subscription runs on testnet (TRUE) or mainnet (FALSE)';
COMMENT ON COLUMN subscriptions.is_trial IS 'Whether this is a trial subscription with limited duration';
COMMENT ON COLUMN subscriptions.trial_expires_at IS 'Expiration time for trial subscriptions';

-- Check current subscriptions
SELECT 
    id,
    instance_name,
    is_testnet,
    is_trial,
    trial_expires_at,
    status
FROM subscriptions 
ORDER BY created_at DESC 
LIMIT 10; 
-- Cleanup: Drop existing airdrop tables if they exist with wrong schema
-- This should run BEFORE 059_create_airdrop_tables

DROP TABLE IF EXISTS airdrop_content_submissions;
DROP TABLE IF EXISTS telegram_verifications;
DROP TABLE IF EXISTS strategy_adoptions;
DROP TABLE IF EXISTS strategy_template_submissions;
DROP TABLE IF EXISTS airdrop_referrals;
DROP TABLE IF EXISTS referral_codes;
DROP TABLE IF EXISTS user_activity;
DROP TABLE IF EXISTS airdrop_claims;
DROP TABLE IF EXISTS airdrop_tasks;
DROP TABLE IF EXISTS airdrop_config;


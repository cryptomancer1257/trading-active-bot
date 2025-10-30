-- Migration: Create Airdrop System Tables
-- Version: 059
-- Date: 2025-10-29
-- Description: Complete airdrop system with tasks, claims, referrals, and trader contributions

-- ============================================
-- DROP EXISTING TABLES (if re-running migration)
-- ============================================

-- Uncomment these lines if you need to re-run the migration
-- DROP TABLE IF EXISTS airdrop_content_submissions;
-- DROP TABLE IF EXISTS telegram_verifications;
-- DROP TABLE IF EXISTS strategy_adoptions;
-- DROP TABLE IF EXISTS strategy_template_submissions;
-- DROP TABLE IF EXISTS airdrop_referrals;
-- DROP TABLE IF EXISTS referral_codes;
-- DROP TABLE IF EXISTS user_activity;
-- DROP TABLE IF EXISTS airdrop_claims;
-- DROP TABLE IF EXISTS airdrop_tasks;
-- DROP TABLE IF EXISTS airdrop_config;

-- ============================================
-- AIRDROP CONFIGURATION
-- ============================================

CREATE TABLE IF NOT EXISTS airdrop_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    is_active BOOLEAN DEFAULT TRUE,
    start_date DATETIME NOT NULL,
    end_date DATETIME,
    total_tokens BIGINT NOT NULL DEFAULT 50000000, -- 50M BOT
    tokens_per_point INT NOT NULL DEFAULT 10,
    max_claim_per_user BIGINT NOT NULL DEFAULT 1000000, -- 1M BOT max
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_airdrop_config_active (is_active)
);

-- ============================================
-- AIRDROP TASKS
-- ============================================

CREATE TABLE IF NOT EXISTS airdrop_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    points INT NOT NULL,
    category ENUM('platform_usage', 'community', 'sns', 'trader_contributions') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_airdrop_tasks_category (category),
    INDEX idx_airdrop_tasks_active (is_active)
);

-- ============================================
-- AIRDROP CLAIMS
-- ============================================

CREATE TABLE IF NOT EXISTS airdrop_claims (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    principal_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(100),
    points_earned INT NOT NULL DEFAULT 0,
    amount_claimed BIGINT,
    tasks_completed INT DEFAULT 0,
    proof_data JSON,
    ip_address VARCHAR(45),
    claimed_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_airdrop_claims_principal (principal_id),
    INDEX idx_airdrop_claims_task (task_id),
    INDEX idx_airdrop_claims_claimed_at (claimed_at),
    INDEX idx_airdrop_claims_ip_address (ip_address)
);

-- ============================================
-- USER ACTIVITY (for daily streak)
-- ============================================

CREATE TABLE IF NOT EXISTS user_activity (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    principal_id VARCHAR(255) NOT NULL,
    activity_type VARCHAR(50) NOT NULL, -- LOGIN, BOT_CREATE, TRADE, etc.
    activity_date DATETIME NOT NULL,
    activity_metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_activity_principal_date (principal_id, activity_date),
    INDEX idx_user_activity_type (activity_type)
);

-- ============================================
-- REFERRAL CODES
-- ============================================

CREATE TABLE IF NOT EXISTS referral_codes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    referrer_principal VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    referral_count INT DEFAULT 0,
    points_earned INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_referral_codes_referrer (referrer_principal),
    INDEX idx_referral_codes_code (code)
);

-- ============================================
-- AIRDROP REFERRALS
-- ============================================

CREATE TABLE IF NOT EXISTS airdrop_referrals (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    referrer_principal VARCHAR(255) NOT NULL,
    referee_principal VARCHAR(255) NOT NULL,
    referral_code_id INT NOT NULL,
    referral_code_value VARCHAR(50) NOT NULL,
    referrer_points_awarded BOOLEAN DEFAULT FALSE,
    referee_completed_first_task BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referral_code_id) REFERENCES referral_codes(id) ON DELETE CASCADE,
    INDEX idx_airdrop_referrals_referrer (referrer_principal),
    INDEX idx_airdrop_referrals_referee (referee_principal),
    INDEX idx_airdrop_referrals_code (referral_code_value)
);

-- ============================================
-- STRATEGY TEMPLATE SUBMISSIONS (Trader Contributions)
-- ============================================

CREATE TABLE IF NOT EXISTS strategy_template_submissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    principal_id VARCHAR(255) NOT NULL,
    bot_id INT NOT NULL,
    strategy_name VARCHAR(255) NOT NULL,
    description TEXT,
    strategy_config JSON NOT NULL,
    performance_metrics JSON,
    checks_passed BOOLEAN DEFAULT FALSE,
    status ENUM('pending_review', 'approved', 'rejected') DEFAULT 'pending_review',
    rejection_reason TEXT,
    adoption_count INT DEFAULT 0,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME,
    approved_by INT,
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_strategy_submissions_principal (principal_id),
    INDEX idx_strategy_submissions_status (status),
    INDEX idx_strategy_submissions_bot (bot_id)
);

-- ============================================
-- STRATEGY ADOPTIONS
-- ============================================

CREATE TABLE IF NOT EXISTS strategy_adoptions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    template_id INT NOT NULL,
    creator_principal VARCHAR(255) NOT NULL,
    adopter_principal VARCHAR(255) NOT NULL,
    adopter_bot_id INT NOT NULL,
    adopted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES strategy_template_submissions(id) ON DELETE CASCADE,
    FOREIGN KEY (adopter_bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    INDEX idx_strategy_adoptions_template (template_id),
    INDEX idx_strategy_adoptions_creator (creator_principal),
    INDEX idx_strategy_adoptions_adopter (adopter_principal)
);

-- ============================================
-- TELEGRAM VERIFICATION
-- ============================================

CREATE TABLE IF NOT EXISTS telegram_verifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    telegram_id VARCHAR(100) NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE,
    principal_id VARCHAR(255),
    used BOOLEAN DEFAULT FALSE,
    used_at DATETIME,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_telegram_verifications_telegram_id (telegram_id),
    INDEX idx_telegram_verifications_code (code),
    INDEX idx_telegram_verifications_principal (principal_id)
);

-- ============================================
-- CONTENT SUBMISSIONS
-- ============================================

CREATE TABLE IF NOT EXISTS airdrop_content_submissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    principal_id VARCHAR(255) NOT NULL,
    content_type ENUM('article', 'video', 'tutorial', 'guide') NOT NULL,
    content_url VARCHAR(500) NOT NULL,
    description TEXT,
    status ENUM('pending_review', 'approved', 'rejected') DEFAULT 'pending_review',
    points_awarded INT DEFAULT 0,
    rejection_reason TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME,
    reviewed_by INT,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_content_submissions_principal (principal_id),
    INDEX idx_content_submissions_status (status)
);

-- ============================================
-- SEED INITIAL DATA
-- ============================================

-- Check and insert default airdrop configuration only if table is empty
INSERT INTO airdrop_config (
    is_active, 
    start_date, 
    end_date, 
    total_tokens, 
    tokens_per_point, 
    max_claim_per_user
)
SELECT 
    TRUE,
    NOW(),
    DATE_ADD(NOW(), INTERVAL 90 DAY),
    50000000,
    10,
    1000000
WHERE NOT EXISTS (SELECT 1 FROM airdrop_config LIMIT 1);

-- Insert airdrop tasks (only if not exists)
INSERT IGNORE INTO airdrop_tasks (name, description, points, category, is_active) VALUES
-- Platform Usage (40% - 20M BOT)
('Create Trading Bot', 'Create your first trading bot on the platform', 100, 'platform_usage', TRUE),
('Complete First Trade', 'Execute your first successful trade', 200, 'platform_usage', TRUE),
('Trading Volume $100', 'Reach $100 in trading volume', 50, 'platform_usage', TRUE),
('Trading Volume $1,000', 'Reach $1,000 in trading volume', 200, 'platform_usage', TRUE),
('Trading Volume $10,000', 'Reach $10,000 in trading volume', 1000, 'platform_usage', TRUE),
('Profitable Bot', 'Have a bot with positive P&L', 500, 'platform_usage', TRUE),
('Daily Active Streak', '10 points per day of activity', 10, 'platform_usage', TRUE),

-- Community Engagement (30% - 15M BOT)
('Discord Member', 'Join and verify Discord membership', 50, 'community', TRUE),
('Telegram Member', 'Join and verify Telegram channel', 30, 'community', TRUE),
('Twitter Follow', 'Follow official Twitter account', 10, 'community', TRUE),
('Twitter Retweet', 'Retweet announcement tweet', 10, 'community', TRUE),
('Content Creation', 'Create blog, video, or tutorial', 100, 'community', TRUE),
('Referral Bonus', '50 points per successful referral', 50, 'community', TRUE),

-- SNS Participation (20% - 10M BOT)
('SNS Sale Participation', 'Participate in SNS token sale', 100, 'sns', TRUE),
('Governance Vote', '50 points per governance vote', 50, 'sns', TRUE),

-- Trader Contributions (10% - 5M BOT)
('Submit Strategy Template', 'Submit profitable strategy template', 1000, 'trader_contributions', TRUE),
('Strategy Adoption', '50 points per adoption of your strategy', 50, 'trader_contributions', TRUE),
('Monthly Top Performer', 'Rank in top 20 monthly leaderboard', 200, 'trader_contributions', TRUE);

-- ============================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================

-- DROP TABLE IF EXISTS airdrop_content_submissions;
-- DROP TABLE IF EXISTS telegram_verifications;
-- DROP TABLE IF EXISTS strategy_adoptions;
-- DROP TABLE IF EXISTS strategy_template_submissions;
-- DROP TABLE IF EXISTS airdrop_referrals;
-- DROP TABLE IF EXISTS referral_codes;
-- DROP TABLE IF EXISTS user_activity;
-- DROP TABLE IF EXISTS airdrop_claims;
-- DROP TABLE IF EXISTS airdrop_tasks;
-- DROP TABLE IF EXISTS airdrop_config;


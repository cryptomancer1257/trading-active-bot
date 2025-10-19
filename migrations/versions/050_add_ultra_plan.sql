-- Migration 050: Add ULTRA plan to PlanName enum
-- Date: 2025-10-19

-- Add 'ultra' to user_plans.plan_name enum
ALTER TABLE user_plans 
MODIFY COLUMN plan_name ENUM('free', 'pro', 'ultra') NOT NULL DEFAULT 'free';

-- Add 'ultra' to plan_history.plan_name enum
ALTER TABLE plan_history 
MODIFY COLUMN plan_name ENUM('free', 'pro', 'ultra') NOT NULL;


-- Fix plan_name enum case - Update lowercase to uppercase
-- This fixes the LookupError: 'free' is not among the defined enum values

-- Update user_plans table
UPDATE user_plans 
SET plan_name = 'FREE' 
WHERE LOWER(plan_name) = 'free';

UPDATE user_plans 
SET plan_name = 'PRO' 
WHERE LOWER(plan_name) = 'pro';

UPDATE user_plans 
SET plan_name = 'ULTRA' 
WHERE LOWER(plan_name) = 'ultra';

-- Update plan_history table
UPDATE plan_history 
SET plan_name = 'FREE' 
WHERE LOWER(plan_name) = 'free';

UPDATE plan_history 
SET plan_name = 'PRO' 
WHERE LOWER(plan_name) = 'pro';

UPDATE plan_history 
SET plan_name = 'ULTRA' 
WHERE LOWER(plan_name) = 'ultra';

-- Verify the changes
SELECT 'user_plans updated:' as message, COUNT(*) as count FROM user_plans WHERE plan_name IN ('FREE', 'PRO', 'ULTRA');
SELECT 'plan_history updated:' as message, COUNT(*) as count FROM plan_history WHERE plan_name IN ('FREE', 'PRO', 'ULTRA');

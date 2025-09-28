-- Migration: Add TRIAL to PaymentMethod enum
-- Date: 2025-09-28

-- Add TRIAL to payment_method_enum
ALTER TABLE subscriptions MODIFY COLUMN payment_method ENUM('STRIPE', 'PAYPAL', 'TRIAL') DEFAULT 'PAYPAL';

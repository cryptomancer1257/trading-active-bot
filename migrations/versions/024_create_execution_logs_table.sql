-- Migration: Create execution_logs table for bot execution logs
-- Version: 024
-- Created: 2025-09-28

CREATE TABLE IF NOT EXISTS execution_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bot_id INT NOT NULL,
    subscription_id INT NULL,
    task_id VARCHAR(100) NULL,
    
    -- Log details
    log_type VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    level VARCHAR(10) DEFAULT 'info',
    data JSON NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
    
    -- Indexes for better performance
    INDEX idx_execution_logs_bot_id (bot_id),
    INDEX idx_execution_logs_subscription_id (subscription_id),
    INDEX idx_execution_logs_task_id (task_id),
    INDEX idx_execution_logs_log_type (log_type),
    INDEX idx_execution_logs_created_at (created_at)
);

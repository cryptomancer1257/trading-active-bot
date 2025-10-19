-- Create feature_flags table for admin control
CREATE TABLE IF NOT EXISTS feature_flags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    feature_type ENUM('PLAN_PACKAGE', 'MARKETPLACE_PUBLISHING', 'BOT_CREATION') NOT NULL UNIQUE,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    disabled_from DATETIME NULL,
    disabled_until DATETIME NULL,
    reason TEXT NULL,
    created_by INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_feature_flags_type (feature_type),
    INDEX idx_feature_flags_enabled (is_enabled),
    INDEX idx_feature_flags_dates (disabled_from, disabled_until)
);

-- Insert default feature flags (ignore duplicates)
INSERT IGNORE INTO feature_flags (feature_type, is_enabled, reason) VALUES 
('PLAN_PACKAGE', TRUE, 'Default enabled'),
('MARKETPLACE_PUBLISHING', TRUE, 'Default enabled'),
('BOT_CREATION', TRUE, 'Default enabled');

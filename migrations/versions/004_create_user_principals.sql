-- MySQL Migration: Create user_principals table for mapping users to principal IDs
-- Allows 1 user to have multiple principal IDs, but 1 principal ID only belongs to 1 user

USE bot_marketplace;

CREATE TABLE IF NOT EXISTS user_principals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    principal_id VARCHAR(255) NOT NULL UNIQUE,
    status ENUM('ACTIVE', 'INACTIVE') DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_principal_id (principal_id),
    INDEX idx_principal_status (principal_id, status)
);

-- Sample data (adjust user_id as needed)
INSERT INTO user_principals (user_id, principal_id, status) VALUES 
(1, 'ok7jr-d6ktf-idahj-ucbcb-pg5tt-2ayc4-kjkjm-xm6qd-h4uxv-vbnrz-bqe', 'ACTIVE'),
(1, 'rdmx6-jaaaa-aaaah-qcaiq-cai', 'ACTIVE')
ON DUPLICATE KEY UPDATE status = VALUES(status);

COMMIT;

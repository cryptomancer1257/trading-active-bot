# 🗄️ Database Schema Documentation

## Overview

The Bot Trading Marketplace uses MySQL 8.0 as the primary database with a well-structured relational schema optimized for trading operations, user management, and marketplace functionality.

## 🏗️ Schema Architecture

### Entity Relationship Diagram

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│    users    │◄──►│exchange_credentials│    │    bots     │
└─────────────┘    └──────────────────┘    └─────────────┘
       │                                           │
       ▼                                           ▼
┌─────────────┐                           ┌─────────────┐
│subscriptions│◄─────────────────────────►│ bot_reviews │
└─────────────┘                           └─────────────┘
       │
       ▼
┌─────────────┐    ┌──────────────────┐    ┌─────────────┐
│   trades    │    │performance_logs  │    │bot_performance│
└─────────────┘    └──────────────────┘    └─────────────┘
```

---

## 📊 Core Tables

### 1. users

Stores user account information and profiles.

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('USER', 'DEVELOPER', 'ADMIN') DEFAULT 'USER',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Developer Information
    developer_name VARCHAR(255),
    developer_bio TEXT,
    developer_website VARCHAR(255),
    
    -- API Access
    api_key VARCHAR(255) UNIQUE COMMENT 'API key for marketplace auth',
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_email (email),
    INDEX idx_api_key (api_key),
    INDEX idx_role (role),
    INDEX idx_active (is_active)
);
```

**Relationships:**
- `1:N` with `exchange_credentials`
- `1:N` with `subscriptions`
- `1:N` with `bot_reviews`
- `1:N` with `bots` (as developer)

---

### 2. exchange_credentials

Stores encrypted API credentials for various exchanges.

```sql
CREATE TABLE exchange_credentials (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    principal_id VARCHAR(255) COMMENT 'ICP Principal ID for marketplace users',
    exchange ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') NOT NULL,
    
    -- Encrypted Credentials
    api_key_encrypted TEXT NOT NULL COMMENT 'Fernet encrypted API key',
    api_secret_encrypted TEXT NOT NULL COMMENT 'Fernet encrypted API secret',
    api_passphrase_encrypted TEXT COMMENT 'Encrypted passphrase for some exchanges',
    
    -- Configuration
    is_testnet BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Validation Status
    validation_status VARCHAR(50) DEFAULT 'pending' COMMENT 'pending, valid, invalid',
    last_validated DATETIME,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Unique Constraints
    UNIQUE KEY unique_user_exchange_testnet (user_id, exchange, is_testnet),
    UNIQUE KEY unique_principal_exchange_testnet (principal_id, exchange, is_testnet),
    
    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_principal_id (principal_id),
    INDEX idx_exchange (exchange),
    INDEX idx_validation_status (validation_status)
);
```

**Security Features:**
- All sensitive data encrypted with Fernet
- Principal ID isolation for marketplace users
- Unique constraints prevent duplicate credentials

---

### 3. bots

Catalog of available trading bots.

```sql
CREATE TABLE bots (
    id INT PRIMARY KEY AUTO_INCREMENT,
    developer_id INT NOT NULL,
    
    -- Bot Information
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0',
    category_id INT,
    
    -- Bot Type and Configuration
    bot_type ENUM('TECHNICAL', 'ML', 'DL', 'LLM') DEFAULT 'TECHNICAL',
    config_schema JSON COMMENT 'JSON schema for bot configuration',
    default_config JSON COMMENT 'Default configuration values',
    
    -- Pricing
    price_per_month DECIMAL(10, 2) DEFAULT 0.00,
    is_free BOOLEAN DEFAULT TRUE,
    
    -- Status and Approval
    status ENUM('PENDING', 'APPROVED', 'REJECTED', 'ARCHIVED') DEFAULT 'PENDING',
    approved_by INT,
    approved_at DATETIME,
    
    -- File Storage
    code_path VARCHAR(500) COMMENT 'S3 path to bot code',
    model_path VARCHAR(500) COMMENT 'S3 path to ML models',
    model_metadata JSON COMMENT 'ML model information',
    
    -- Statistics
    total_subscribers INT DEFAULT 0,
    average_rating DECIMAL(3, 2) DEFAULT 0.00,
    total_reviews INT DEFAULT 0,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (developer_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    
    -- Indexes
    INDEX idx_developer_id (developer_id),
    INDEX idx_status (status),
    INDEX idx_bot_type (bot_type),
    INDEX idx_category_id (category_id),
    INDEX idx_price (price_per_month),
    INDEX idx_rating (average_rating)
);
```

**Features:**
- Version management for bot updates
- JSON schema validation for configurations
- S3 integration for code storage
- Approval workflow for marketplace quality

---

### 4. subscriptions

User subscriptions to trading bots with marketplace integration.

```sql
CREATE TABLE subscriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    user_principal_id VARCHAR(255) COMMENT 'ICP Principal ID mapping',
    bot_id INT NOT NULL,
    
    -- Instance Configuration
    instance_name VARCHAR(255) NOT NULL,
    exchange_type ENUM('BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI') DEFAULT 'BINANCE',
    trading_pair VARCHAR(20) NOT NULL DEFAULT 'BTC/USDT',
    
    -- Trading Parameters
    timeframe VARCHAR(10) NOT NULL DEFAULT '1h' COMMENT '1m, 5m, 15m, 1h, 4h, 1d, etc.',
    timeframes JSON COMMENT 'Multiple timeframes for analysis',
    strategy_config JSON DEFAULT '{}',
    
    -- Execution Configuration
    execution_config JSON NOT NULL COMMENT 'Buy/sell order configuration',
    risk_config JSON NOT NULL COMMENT 'Stop loss, take profit, position sizing',
    
    -- Marketplace Features
    trade_evaluation_period INT COMMENT 'Minutes for bot analysis',
    network_type ENUM('testnet', 'mainnet') DEFAULT 'testnet',
    trade_mode ENUM('Spot', 'Margin', 'Futures') DEFAULT 'Spot',
    
    -- Status and Lifecycle
    status ENUM('ACTIVE', 'PAUSED', 'CANCELLED', 'EXPIRED', 'ERROR') DEFAULT 'ACTIVE',
    is_testnet BOOLEAN DEFAULT FALSE,
    is_trial BOOLEAN DEFAULT FALSE,
    
    -- Timing
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    trial_expires_at DATETIME,
    last_run_at DATETIME,
    next_run_at DATETIME,
    
    -- Performance Tracking
    total_trades INT DEFAULT 0,
    winning_trades INT DEFAULT 0,
    total_pnl DECIMAL(15, 8) DEFAULT 0.0,
    
    -- Foreign Keys
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (bot_id) REFERENCES bots(id),
    
    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_user_principal_id (user_principal_id),
    INDEX idx_bot_id (bot_id),
    INDEX idx_status (status),
    INDEX idx_exchange_type (exchange_type),
    INDEX idx_trading_pair (trading_pair),
    INDEX idx_expires_at (expires_at),
    INDEX idx_next_run_at (next_run_at)
);
```

**Key Features:**
- Principal ID mapping for ICP marketplace integration
- JSON configuration for flexible bot parameters
- Performance tracking built-in
- Trial and expiration management

---

### 5. trades

Individual trade records and execution history.

```sql
CREATE TABLE trades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    subscription_id INT NOT NULL,
    
    -- Trade Details
    side ENUM('BUY', 'SELL') NOT NULL,
    trading_pair VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    
    -- Pricing
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8),
    stop_loss_price DECIMAL(20, 8),
    take_profit_price DECIMAL(20, 8),
    
    -- Timing
    entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    exit_time DATETIME,
    
    -- Performance
    pnl DECIMAL(15, 8) COMMENT 'Profit/Loss in quote currency',
    pnl_percentage DECIMAL(8, 4) COMMENT 'P&L as percentage',
    
    -- Exchange Integration
    exchange_order_id VARCHAR(100) COMMENT 'Exchange order ID',
    exchange_trade_id VARCHAR(100) COMMENT 'Exchange trade ID',
    
    -- Status
    status ENUM('OPEN', 'CLOSED') DEFAULT 'OPEN',
    
    -- Foreign Keys
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_subscription_id (subscription_id),
    INDEX idx_trading_pair (trading_pair),
    INDEX idx_side (side),
    INDEX idx_status (status),
    INDEX idx_entry_time (entry_time),
    INDEX idx_pnl (pnl),
    INDEX idx_exchange_order_id (exchange_order_id)
);
```

**Features:**
- Complete trade lifecycle tracking
- Exchange order mapping
- P&L calculation and tracking
- Performance analytics support

---

### 6. performance_logs

Detailed logs of bot actions and market analysis.

```sql
CREATE TABLE performance_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    subscription_id INT NOT NULL,
    
    -- Action Details
    action ENUM('BUY', 'SELL', 'HOLD', 'STOP_LOSS', 'TAKE_PROFIT') NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Market Data
    price DECIMAL(20, 8) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    balance DECIMAL(20, 8) NOT NULL COMMENT 'Account balance after action',
    
    -- Signal Information
    signal_data JSON COMMENT 'Technical indicators, LLM analysis, etc.',
    
    -- Foreign Keys
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_subscription_id (subscription_id),
    INDEX idx_action (action),
    INDEX idx_timestamp (timestamp),
    INDEX idx_price (price)
);
```

---

### 7. bot_marketplace_registrations

Marketplace-specific bot registrations and API key management.

```sql
CREATE TABLE bot_marketplace_registrations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_principal_id VARCHAR(255) NOT NULL,
    bot_id INT NOT NULL,
    
    -- API Access
    api_key VARCHAR(255) NOT NULL UNIQUE COMMENT 'Generated API key for bot access',
    
    -- Marketplace Configuration
    status VARCHAR(50) DEFAULT 'approved',
    marketplace_name VARCHAR(255),
    marketplace_description TEXT,
    price_on_marketplace DECIMAL(10, 2),
    commission_rate DECIMAL(5, 4) DEFAULT 0.1000 COMMENT '10% default commission',
    
    -- Features
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (bot_id) REFERENCES bots(id),
    
    -- Indexes
    INDEX idx_user_principal_id (user_principal_id),
    INDEX idx_bot_id (bot_id),
    INDEX idx_api_key (api_key),
    INDEX idx_status (status),
    INDEX idx_is_active (is_active)
);
```

---

## 🔐 Security Considerations

### Data Encryption

1. **Exchange Credentials**: All API keys encrypted with Fernet symmetric encryption
2. **Principal ID Isolation**: Marketplace users isolated by principal ID
3. **API Key Generation**: Secure random generation for bot access
4. **Password Hashing**: bcrypt with salt for user passwords

### Access Control

```sql
-- Example security policies
CREATE VIEW user_secure_view AS
SELECT id, email, role, is_active, developer_name, created_at
FROM users;

-- Stored procedure for secure credential access
DELIMITER //
CREATE PROCEDURE GetUserCredentials(
    IN p_user_id INT,
    IN p_exchange VARCHAR(50)
)
BEGIN
    SELECT api_key_encrypted, api_secret_encrypted, is_testnet
    FROM exchange_credentials
    WHERE user_id = p_user_id 
    AND exchange = p_exchange 
    AND is_active = TRUE;
END //
DELIMITER ;
```

### Audit Trail

```sql
-- Audit table for sensitive operations
CREATE TABLE audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50),
    record_id INT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_timestamp (timestamp)
);
```

---

## 📈 Performance Optimizations

### Indexing Strategy

```sql
-- Composite indexes for common queries
CREATE INDEX idx_subscription_user_status ON subscriptions(user_id, status);
CREATE INDEX idx_trades_subscription_time ON trades(subscription_id, entry_time);
CREATE INDEX idx_performance_subscription_action ON performance_logs(subscription_id, action, timestamp);

-- Covering indexes for analytics
CREATE INDEX idx_subscription_performance_covering 
ON subscriptions(status, exchange_type, trading_pair, total_trades, winning_trades, total_pnl);
```

### Partitioning

```sql
-- Partition large tables by date
ALTER TABLE performance_logs 
PARTITION BY RANGE (YEAR(timestamp)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);

ALTER TABLE trades
PARTITION BY RANGE (YEAR(entry_time)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

---

## 🔄 Migration Strategy

### Version Control

```sql
-- Migration tracking table
CREATE TABLE schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Example migration
INSERT INTO schema_migrations (version) VALUES ('001_initial_schema');
INSERT INTO schema_migrations (version) VALUES ('002_bot_registration_features');
INSERT INTO schema_migrations (version) VALUES ('003_marketplace_integration');
```

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump --single-transaction --routines --triggers \
  -h localhost -u backup_user -p${MYSQL_PASSWORD} \
  bot_marketplace > /backups/bot_marketplace_${DATE}.sql

# Compress and upload to S3
gzip /backups/bot_marketplace_${DATE}.sql
aws s3 cp /backups/bot_marketplace_${DATE}.sql.gz \
  s3://bot-marketplace-backups/daily/
```

---

## 📊 Analytics Views

### User Performance View

```sql
CREATE VIEW user_performance_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.user_principal_id,
    COUNT(DISTINCT s.id) as active_subscriptions,
    COUNT(DISTINCT t.id) as total_trades,
    SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    ROUND(AVG(t.pnl), 2) as avg_pnl,
    ROUND(SUM(t.pnl), 2) as total_pnl,
    ROUND(100.0 * SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END) / COUNT(t.id), 2) as win_rate
FROM users u
LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'ACTIVE'
LEFT JOIN trades t ON s.id = t.subscription_id
GROUP BY u.id, u.email, u.user_principal_id;
```

### Bot Performance View

```sql
CREATE VIEW bot_performance_summary AS
SELECT 
    b.id as bot_id,
    b.name as bot_name,
    b.developer_id,
    COUNT(DISTINCT s.id) as total_subscriptions,
    COUNT(DISTINCT CASE WHEN s.status = 'ACTIVE' THEN s.id END) as active_subscriptions,
    COUNT(DISTINCT t.id) as total_trades,
    ROUND(AVG(t.pnl), 2) as avg_pnl_per_trade,
    ROUND(SUM(t.pnl), 2) as total_pnl,
    ROUND(100.0 * SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END) / COUNT(t.id), 2) as win_rate,
    MAX(t.entry_time) as last_trade_time
FROM bots b
LEFT JOIN subscriptions s ON b.id = s.bot_id
LEFT JOIN trades t ON s.id = t.subscription_id
WHERE b.status = 'APPROVED'
GROUP BY b.id, b.name, b.developer_id;
```

---

## 🛠️ Maintenance Procedures

### Regular Maintenance Tasks

```sql
-- Clean old performance logs (keep 90 days)
DELETE FROM performance_logs 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- Update bot statistics
UPDATE bots b SET 
    total_subscribers = (
        SELECT COUNT(*) FROM subscriptions s 
        WHERE s.bot_id = b.id AND s.status = 'ACTIVE'
    ),
    average_rating = (
        SELECT AVG(rating) FROM bot_reviews r 
        WHERE r.bot_id = b.id
    ),
    total_reviews = (
        SELECT COUNT(*) FROM bot_reviews r 
        WHERE r.bot_id = b.id
    );

-- Optimize tables
OPTIMIZE TABLE users, bots, subscriptions, trades, performance_logs;

-- Update table statistics
ANALYZE TABLE users, bots, subscriptions, trades, performance_logs;
```

---

## 📋 Schema Validation

### Data Integrity Checks

```sql
-- Check for orphaned records
SELECT 'Orphaned exchange_credentials' as issue, COUNT(*) as count
FROM exchange_credentials ec
LEFT JOIN users u ON ec.user_id = u.id
WHERE u.id IS NULL

UNION ALL

SELECT 'Orphaned subscriptions' as issue, COUNT(*) as count
FROM subscriptions s
LEFT JOIN users u ON s.user_id = u.id
WHERE u.id IS NULL

UNION ALL

SELECT 'Orphaned trades' as issue, COUNT(*) as count
FROM trades t
LEFT JOIN subscriptions s ON t.subscription_id = s.id
WHERE s.id IS NULL;
```

### Performance Monitoring

```sql
-- Slow query analysis
SELECT 
    query_time,
    lock_time,
    rows_examined,
    rows_sent,
    sql_text
FROM mysql.slow_log
WHERE start_time > DATE_SUB(NOW(), INTERVAL 1 DAY)
ORDER BY query_time DESC
LIMIT 10;
```

---

*This schema design ensures scalability, security, and performance for high-volume trading operations while maintaining data integrity and supporting complex marketplace functionality.*
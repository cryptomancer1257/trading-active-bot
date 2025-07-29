# Database Setup Guide

## 🗄️ Database Initialization

### **Option 1: Fresh Start (Recommended)**

```bash
# Reset database completely
chmod +x reset_database.sh
./reset_database.sh
```

### **Option 2: Manual Setup**

```bash
# Start containers
docker-compose up -d

# Wait for MySQL to be ready
sleep 30

# Run initialization script
docker-compose exec db mysql -u botuser -pbotpassword123 bot_marketplace < init.sql
```

### **Option 3: Manual Migration (if database exists)**

```bash
# Run migration to add missing columns
docker-compose exec db mysql -u botuser -pbotpassword123 bot_marketplace < add_pricing_plan_id.sql
```

## 📊 Database Schema

### **Core Tables:**
- `users` - User accounts and profiles
- `bots` - Trading bot definitions
- `subscriptions` - User bot subscriptions
- `trades` - Individual trade records
- `exchange_credentials` - API credentials for exchanges

### **Pricing System:**
- `bot_pricing_plans` - Bot pricing plans
- `bot_promotions` - Promotional offers
- `subscription_invoices` - Billing invoices

### **Performance Tracking:**
- `performance_logs` - Bot action logs
- `bot_performance` - Aggregate performance metrics
- `bot_reviews` - User reviews

## 🔐 Default Credentials

### **Admin User:**
- Email: `admin@botmarketplace.com`
- Password: `admin123`
- Role: `ADMIN`

### **System User:**
- Email: `system@botmarketplace.com`
- Password: `admin123`
- Role: `ADMIN`

## 🧪 Sample Data

### **Sample Bots:**
1. **Golden Cross Strategy** - Moving average crossover
2. **RSI Divergence Bot** - RSI divergence detection
3. **MACD Signal Bot** - MACD signal generation

### **Sample Subscriptions:**
- Test subscriptions with sample configurations
- Testnet mode enabled by default

## 🔧 Database Commands

### **Check Database Status:**
```bash
docker-compose exec db mysql -u botuser -pbotpassword123 -e "USE bot_marketplace; SHOW TABLES;"
```

### **View Sample Data:**
```bash
# View users
docker-compose exec db mysql -u botuser -pbotpassword123 -e "USE bot_marketplace; SELECT * FROM users;"

# View bots
docker-compose exec db mysql -u botuser -pbotpassword123 -e "USE bot_marketplace; SELECT * FROM bots;"

# View subscriptions
docker-compose exec db mysql -u botuser -pbotpassword123 -e "USE bot_marketplace; SELECT * FROM subscriptions;"
```

### **Reset Database:**
```bash
# Stop containers
docker-compose down

# Remove volume
docker volume rm bot_marketplace_mysql_data

# Start fresh
docker-compose up -d
```

## 🚨 Troubleshooting

### **MySQL Connection Issues:**
```bash
# Check if MySQL is running
docker-compose ps

# Check MySQL logs
docker-compose logs db

# Connect to MySQL manually
docker-compose exec db mysql -u botuser -pbotpassword123
```

### **Permission Issues:**
```bash
# Make script executable
chmod +x reset_database.sh

# Run with sudo if needed
sudo ./reset_database.sh
```

### **Port Conflicts:**
```bash
# Check if port 3307 is in use
lsof -i :3307

# Change port in docker-compose.yml if needed
ports:
  - "3308:3306"  # Change from 3307 to 3308
```

## 📈 Performance Tips

### **Database Optimization:**
- All tables have proper indexes
- Foreign key constraints are enabled
- JSON columns for flexible configuration

### **Backup Strategy:**
```bash
# Backup database
docker-compose exec db mysqldump -u botuser -pbotpassword123 bot_marketplace > backup.sql

# Restore database
docker-compose exec -T db mysql -u botuser -pbotpassword123 bot_marketplace < backup.sql
```

## 🔄 Migration History

### **Version 1.0:**
- Initial schema with basic tables
- User management and bot system
- Subscription and trade tracking

### **Version 1.1:**
- Added pricing system tables
- Enhanced subscription management
- Performance tracking improvements

### **Version 1.2:**
- Added exchange credentials table
- Improved security and validation
- Better error handling 
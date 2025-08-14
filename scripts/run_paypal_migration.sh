#!/bin/bash

# PayPal Integration Migration Runner
# Applies the PayPal database migration

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 PayPal Integration Migration Runner${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Check if migration file exists
MIGRATION_FILE="migrations/versions/009_paypal_integration.sql"
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}❌ Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi

# Load database configuration
if [ -f ".env" ]; then
    echo -e "${BLUE}📁 Loading environment variables from .env${NC}"
    source .env
else
    echo -e "${YELLOW}⚠️  No .env file found, using default values${NC}"
fi

# Set default database connection parameters
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-3306}
DB_USER=${DB_USER:-root}
DB_PASSWORD=${DB_PASSWORD:-password}
DB_NAME=${DB_NAME:-bot_marketplace}

echo -e "${BLUE}📊 Database Configuration:${NC}"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo "  Database: $DB_NAME"
echo ""

# Test database connection
echo -e "${BLUE}🔍 Testing database connection...${NC}"
mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" "$DB_NAME" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
    echo "Please check your database configuration and ensure MySQL is running."
    exit 1
fi

# Check if migration has already been applied
echo -e "${BLUE}🔍 Checking migration status...${NC}"
PAYPAL_TABLE_EXISTS=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -D"$DB_NAME" -s -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME' AND table_name='paypal_payments';" 2>/dev/null || echo "0")

if [ "$PAYPAL_TABLE_EXISTS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  PayPal tables already exist. Migration may have been applied before.${NC}"
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🚫 Migration cancelled by user${NC}"
        exit 0
    fi
fi

# Create backup
BACKUP_FILE="backup_before_paypal_migration_$(date +%Y%m%d_%H%M%S).sql"
echo -e "${BLUE}💾 Creating database backup: $BACKUP_FILE${NC}"

mysqldump -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    "$DB_NAME" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup created successfully${NC}"
else
    echo -e "${RED}❌ Backup creation failed${NC}"
    exit 1
fi

# Apply migration
echo -e "${BLUE}⚡ Applying PayPal integration migration...${NC}"
mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$MIGRATION_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PayPal migration applied successfully${NC}"
else
    echo -e "${RED}❌ Migration failed${NC}"
    echo -e "${YELLOW}🔄 Restoring from backup...${NC}"
    
    # Restore from backup
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database restored from backup${NC}"
    else
        echo -e "${RED}❌ Backup restoration failed - manual intervention required${NC}"
    fi
    
    exit 1
fi

# Verify migration
echo -e "${BLUE}🔍 Verifying migration...${NC}"

# Check for PayPal tables
TABLES_TO_CHECK=(
    "paypal_payments"
    "paypal_config"
    "paypal_webhook_events"
)

for table in "${TABLES_TO_CHECK[@]}"; do
    TABLE_EXISTS=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -D"$DB_NAME" -s -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME' AND table_name='$table';" 2>/dev/null || echo "0")
    
    if [ "$TABLE_EXISTS" -gt 0 ]; then
        echo -e "${GREEN}  ✅ Table '$table' created successfully${NC}"
    else
        echo -e "${RED}  ❌ Table '$table' not found${NC}"
    fi
done

# Check for view
VIEW_EXISTS=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -D"$DB_NAME" -s -N -e "SELECT COUNT(*) FROM information_schema.views WHERE table_schema='$DB_NAME' AND table_name='paypal_payment_summary';" 2>/dev/null || echo "0")

if [ "$VIEW_EXISTS" -gt 0 ]; then
    echo -e "${GREEN}  ✅ View 'paypal_payment_summary' created successfully${NC}"
else
    echo -e "${RED}  ❌ View 'paypal_payment_summary' not found${NC}"
fi

# Show table structures
echo ""
echo -e "${BLUE}📋 PayPal Tables Structure:${NC}"
for table in "${TABLES_TO_CHECK[@]}"; do
    echo -e "${YELLOW}Table: $table${NC}"
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -D"$DB_NAME" -e "DESCRIBE $table;" 2>/dev/null || echo "  Table not accessible"
    echo ""
done

echo -e "${GREEN}🎉 PayPal Integration Migration Completed Successfully!${NC}"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo "1. Install PayPal SDK: pip install paypalrestsdk==1.13.3"
echo "2. Configure PayPal environment variables in .env:"
echo "   PAYPAL_MODE=sandbox"
echo "   PAYPAL_CLIENT_ID=your_sandbox_client_id"
echo "   PAYPAL_CLIENT_SECRET=your_sandbox_client_secret"
echo "   PAYPAL_WEBHOOK_SECRET=your_webhook_secret"
echo "3. Restart your FastAPI application"
echo "4. Test PayPal integration endpoints"
echo ""
echo -e "${BLUE}💾 Backup file created: $BACKUP_FILE${NC}"
echo -e "${YELLOW}⚠️  Keep this backup safe in case rollback is needed${NC}"

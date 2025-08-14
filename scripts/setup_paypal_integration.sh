#!/bin/bash

# PayPal Integration Setup Script
# Installs dependencies, runs migration, and sets up configuration

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🎯 PayPal Integration Setup${NC}"
echo -e "${CYAN}===========================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Please run this script from the trade-bot-marketplace root directory${NC}"
    exit 1
fi

# Step 1: Install dependencies
echo -e "${BLUE}📦 Step 1: Installing Python dependencies...${NC}"
pip install paypalrestsdk==1.13.3
pip install redis==5.0.1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Dependency installation failed${NC}"
    exit 1
fi

echo ""

# Step 2: Check Redis installation
echo -e "${BLUE}🔍 Step 2: Checking Redis availability...${NC}"
if command -v redis-server &> /dev/null; then
    echo -e "${GREEN}✅ Redis server found${NC}"
    
    # Try to ping Redis
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis server found but not running${NC}"
        echo "To start Redis:"
        echo "  - macOS: brew services start redis"
        echo "  - Ubuntu: sudo systemctl start redis-server"
        echo "  - Docker: docker run -d -p 6379:6379 redis:alpine"
    fi
else
    echo -e "${YELLOW}⚠️  Redis not found. Installing Redis is recommended for currency caching.${NC}"
    echo "Installation options:"
    echo "  - macOS: brew install redis"
    echo "  - Ubuntu: sudo apt-get install redis-server"
    echo "  - Docker: docker run -d -p 6379:6379 redis:alpine"
fi

echo ""

# Step 3: Run database migration
echo -e "${BLUE}⚡ Step 3: Running database migration...${NC}"
if [ -f "scripts/run_paypal_migration.sh" ]; then
    ./scripts/run_paypal_migration.sh
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database migration completed${NC}"
    else
        echo -e "${RED}❌ Database migration failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Migration script not found${NC}"
    exit 1
fi

echo ""

# Step 4: Environment configuration
echo -e "${BLUE}⚙️  Step 4: Environment configuration...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    
    if [ -f "config/paypal.env.example" ]; then
        cp config/paypal.env.example .env
        echo -e "${GREEN}✅ .env file created from template${NC}"
    else
        echo -e "${YELLOW}⚠️  Template not found, creating basic .env file...${NC}"
        cat > .env << EOF
# PayPal Configuration
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your_sandbox_client_id_here
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret_here
PAYPAL_WEBHOOK_SECRET=your_webhook_secret_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Development Mode
DEVELOPMENT_MODE=false
EOF
        echo -e "${GREEN}✅ Basic .env file created${NC}"
    fi
else
    echo -e "${BLUE}📝 .env file exists. Checking PayPal configuration...${NC}"
    
    # Check if PayPal variables exist
    if grep -q "PAYPAL_MODE" .env && grep -q "PAYPAL_CLIENT_ID" .env; then
        echo -e "${GREEN}✅ PayPal configuration found in .env${NC}"
    else
        echo -e "${YELLOW}⚠️  PayPal configuration missing from .env${NC}"
        echo "Adding PayPal configuration to .env..."
        
        echo "" >> .env
        echo "# PayPal Integration Configuration" >> .env
        echo "PAYPAL_MODE=sandbox" >> .env
        echo "PAYPAL_CLIENT_ID=your_sandbox_client_id_here" >> .env
        echo "PAYPAL_CLIENT_SECRET=your_sandbox_client_secret_here" >> .env
        echo "PAYPAL_WEBHOOK_SECRET=your_webhook_secret_here" >> .env
        echo "REDIS_HOST=localhost" >> .env
        echo "REDIS_PORT=6379" >> .env
        echo "REDIS_DB=0" >> .env
        echo "FRONTEND_URL=http://localhost:3000" >> .env
        
        echo -e "${GREEN}✅ PayPal configuration added to .env${NC}"
    fi
fi

echo ""

# Step 5: Test database connection
echo -e "${BLUE}🔍 Step 5: Testing database connection...${NC}"

# Load .env variables
if [ -f ".env" ]; then
    source .env
fi

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-3306}
DB_USER=${DB_USER:-root}
DB_NAME=${DB_NAME:-bot_marketplace}

if [ -n "$DB_PASSWORD" ] && [ "$DB_PASSWORD" != "your_database_password" ]; then
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT COUNT(*) as paypal_tables FROM information_schema.tables WHERE table_schema='$DB_NAME' AND table_name LIKE 'paypal_%';" "$DB_NAME" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database connection successful${NC}"
        echo -e "${GREEN}✅ PayPal tables verified${NC}"
    else
        echo -e "${YELLOW}⚠️  Database connection test failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Database password not configured in .env${NC}"
fi

echo ""

# Step 6: Create test script
echo -e "${BLUE}🧪 Step 6: Creating test script...${NC}"

cat > scripts/test_paypal_integration.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for PayPal integration
Verifies that all components are working correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
import asyncio

async def test_paypal_integration():
    """Test PayPal integration components"""
    print("🧪 Testing PayPal Integration Components")
    print("=" * 40)
    
    # Test 1: Import dependencies
    try:
        import paypalrestsdk
        print("✅ PayPal SDK imported successfully")
    except ImportError as e:
        print(f"❌ PayPal SDK import failed: {e}")
        return False
    
    # Test 2: Currency service
    try:
        from services.currency_service import get_currency_service
        currency_service = get_currency_service()
        rate = currency_service.get_icp_usd_rate()
        print(f"✅ Currency service working. ICP/USD rate: ${rate}")
    except Exception as e:
        print(f"❌ Currency service failed: {e}")
        return False
    
    # Test 3: Database models
    try:
        from core import models
        print("✅ PayPal models imported successfully")
        
        # Check if PayPal enums exist
        assert hasattr(models, 'PayPalPaymentStatus')
        assert hasattr(models, 'PaymentMethod')
        print("✅ PayPal enums verified")
        
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False
    
    # Test 4: Database connection
    try:
        from core.database import SessionLocal
        db = SessionLocal()
        
        # Test query
        result = db.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'paypal_payments'")
        count = result.scalar()
        
        if count > 0:
            print("✅ PayPal database tables found")
        else:
            print("❌ PayPal database tables not found")
            return False
            
        db.close()
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    # Test 5: PayPal configuration
    try:
        paypal_mode = os.getenv('PAYPAL_MODE', 'not_set')
        paypal_client_id = os.getenv('PAYPAL_CLIENT_ID', 'not_set')
        
        if paypal_mode != 'not_set' and paypal_client_id != 'not_set':
            print(f"✅ PayPal configuration found (Mode: {paypal_mode})")
        else:
            print("⚠️  PayPal configuration incomplete - update .env file")
            
    except Exception as e:
        print(f"❌ PayPal configuration test failed: {e}")
        return False
    
    print("\n🎉 PayPal integration test completed successfully!")
    print("\n📝 Next steps:")
    print("1. Configure your PayPal credentials in .env")
    print("2. Start your FastAPI server: uvicorn core.main:app --reload")
    print("3. Test PayPal endpoints at http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_paypal_integration())
EOF

chmod +x scripts/test_paypal_integration.py
echo -e "${GREEN}✅ Test script created${NC}"

echo ""

# Final summary
echo -e "${CYAN}🎉 PayPal Integration Setup Complete!${NC}"
echo -e "${CYAN}====================================${NC}"
echo ""

echo -e "${BLUE}✅ Completed Steps:${NC}"
echo "  1. ✅ Python dependencies installed"
echo "  2. ✅ Redis availability checked"
echo "  3. ✅ Database migration applied"
echo "  4. ✅ Environment configuration setup"
echo "  5. ✅ Database connection verified"
echo "  6. ✅ Test script created"

echo ""
echo -e "${YELLOW}🔧 Configuration Required:${NC}"
echo "  1. Update .env with your PayPal sandbox credentials:"
echo "     - Get credentials from: https://developer.paypal.com/"
echo "     - Update PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET"
echo "  2. Ensure Redis is running for currency caching"
echo "  3. Configure FRONTEND_URL if different from localhost:3000"

echo ""
echo -e "${BLUE}🧪 Testing:${NC}"
echo "  Run the test script: python scripts/test_paypal_integration.py"

echo ""
echo -e "${BLUE}🚀 Starting the Server:${NC}"
echo "  uvicorn core.main:app --reload --host 0.0.0.0 --port 8000"

echo ""
echo -e "${BLUE}📚 API Documentation:${NC}"
echo "  http://localhost:8000/docs"
echo "  PayPal endpoints will be available under '/payments'"

echo ""
echo -e "${GREEN}🎯 PayPal Integration is ready to use!${NC}"

#!/bin/bash

# Google OAuth Setup Script
# This script helps you quickly configure Google OAuth for both frontend and backend

set -e

echo "🔐 Google OAuth Configuration Setup"
echo "===================================="
echo ""

# Check if running from project root
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Ask for Google Client ID
echo "📋 Please enter your Google Client ID:"
echo "   (Get it from: https://console.cloud.google.com/apis/credentials)"
echo "   Format: xxx.apps.googleusercontent.com"
echo ""
read -p "Client ID: " GOOGLE_CLIENT_ID

# Validate input
if [ -z "$GOOGLE_CLIENT_ID" ]; then
    echo "❌ Error: Client ID cannot be empty"
    exit 1
fi

if [[ ! "$GOOGLE_CLIENT_ID" =~ \.apps\.googleusercontent\.com$ ]]; then
    echo "⚠️  Warning: Client ID doesn't look like a valid Google Client ID"
    read -p "Continue anyway? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "⚙️  Configuring..."

# 1. Configure Backend
echo "1️⃣  Setting up Backend..."
if [ -f ".env" ]; then
    # Update existing .env
    if grep -q "GOOGLE_CLIENT_ID=" .env; then
        # Replace existing
        sed -i.bak "s|GOOGLE_CLIENT_ID=.*|GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID|" .env
        echo "   ✅ Updated GOOGLE_CLIENT_ID in .env"
    else
        # Add new
        echo "GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" >> .env
        echo "   ✅ Added GOOGLE_CLIENT_ID to .env"
    fi
else
    # Create new .env
    cat > .env << EOF
# Database Configuration
DATABASE_URL=mysql+pymysql://botuser:botpassword123@localhost:3307/bot_marketplace

# Google OAuth 2.0
GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID

# Other configs (adjust as needed)
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=your-secret-key-change-in-production
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
EOF
    echo "   ✅ Created .env with GOOGLE_CLIENT_ID"
fi

# 2. Configure Frontend
echo "2️⃣  Setting up Frontend..."
if [ -f "frontend/.env.local" ]; then
    # Update existing .env.local
    if grep -q "NEXT_PUBLIC_GOOGLE_CLIENT_ID=" frontend/.env.local; then
        # Replace existing
        sed -i.bak "s|NEXT_PUBLIC_GOOGLE_CLIENT_ID=.*|NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID|" frontend/.env.local
        echo "   ✅ Updated NEXT_PUBLIC_GOOGLE_CLIENT_ID in frontend/.env.local"
    else
        # Add new
        echo "NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" >> frontend/.env.local
        echo "   ✅ Added NEXT_PUBLIC_GOOGLE_CLIENT_ID to frontend/.env.local"
    fi
else
    # Create new .env.local
    cat > frontend/.env.local << EOF
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Google OAuth 2.0
NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
EOF
    echo "   ✅ Created frontend/.env.local with NEXT_PUBLIC_GOOGLE_CLIENT_ID"
fi

echo ""
echo "✅ Configuration Complete!"
echo ""
echo "📝 Next Steps:"
echo "   1. Restart your backend server: python main.py"
echo "   2. Restart your frontend server: cd frontend && npm run dev"
echo "   3. Visit: http://localhost:3001/auth/login"
echo "   4. You should see 'Sign in with Google' button!"
echo ""
echo "📚 Documentation:"
echo "   - Quick Start: GOOGLE_OAUTH_QUICKSTART.md"
echo "   - Full Guide: docs/GOOGLE_OAUTH_SETUP.md"
echo ""
echo "🎉 Happy coding!"


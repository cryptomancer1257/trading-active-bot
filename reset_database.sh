#!/bin/bash

echo "🔄 Resetting Bot Marketplace Database..."

# Stop all containers
echo "📦 Stopping all containers..."
docker-compose down

# Remove MySQL volume to start fresh
echo "🗑️ Removing MySQL volume..."
docker volume rm bot_marketplace_mysql_data

# Start containers with fresh database
echo "🚀 Starting containers with fresh database..."
docker-compose up -d

# Wait for MySQL to be ready
echo "⏳ Waiting for MySQL to be ready..."
sleep 30

# Check if database is initialized
echo "🔍 Checking database initialization..."
docker-compose exec db mysql -u botuser -pbotpassword123 -e "USE bot_marketplace; SELECT COUNT(*) as user_count FROM users;"

echo "✅ Database reset completed!"
echo ""
echo "📊 Database Status:"
echo "   - Users: $(docker-compose exec db mysql -u botuser -pbotpassword123 -e "USE bot_marketplace; SELECT COUNT(*) FROM users;" -s -N)"
echo "   - Bots: $(docker-compose exec db mysql -u botuser -pbotpassword123 -e "USE bot_marketplace; SELECT COUNT(*) FROM bots;" -s -N)"
echo "   - Subscriptions: $(docker-compose exec db mysql -u botuser -pbotpassword123 -e "USE bot_marketplace; SELECT COUNT(*) FROM subscriptions;" -s -N)"
echo ""
echo "🌐 API is running at: http://localhost:8000"
echo "📝 Admin credentials:"
echo "   - Email: admin@botmarketplace.com"
echo "   - Password: admin123"
echo ""
echo "🔧 System credentials:"
echo "   - Email: system@botmarketplace.com"
echo "   - Password: admin123" 
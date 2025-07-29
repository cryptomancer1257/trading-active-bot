# 🤖 Bot Marketplace

Advanced Trading Bot Platform

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone <repository-url>
cd bot_marketplace
cp env.example .env
nano .env  # Configure required settings
```

### 2. Configure Required Settings

#### A. Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### B. Configure Email (Choose One)

**SendGrid (Recommended):**
```env
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
```

**Gmail SMTP:**
```env
GMAIL_USER=your-gmail@gmail.com
GMAIL_PASSWORD=your-app-password
```

#### C. AWS S3 (Optional - for bot storage)
```env
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket
```

### 3. Start Application
```bash
docker-compose up -d
```

### 4. Access Application
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📧 Email Setup

### SendGrid
1. Create account at [sendgrid.com](https://sendgrid.com)
2. Generate API key
3. Verify sender email
4. Add to `.env`:
   ```env
   SENDGRID_API_KEY=your-api-key
   FROM_EMAIL=verified@yourdomain.com
   ```

### Gmail
1. Enable 2FA
2. Generate app password
3. Add to `.env`:
   ```env
   GMAIL_USER=your-gmail@gmail.com
   GMAIL_PASSWORD=your-app-password
   ```

## 🔧 Troubleshooting

### Reset Database
```bash
./reset_database.sh
```

### View Logs
```bash
docker-compose logs -f
```

### Common Issues
- **Port in use**: Change `API_PORT` in `.env`
- **Email not working**: Check API key/credentials
- **Database error**: Run `./reset_database.sh`

## 📚 Documentation
- **API Docs**: http://localhost:8000/docs
- **Detailed Setup**: See `SETUP_GUIDE.md`

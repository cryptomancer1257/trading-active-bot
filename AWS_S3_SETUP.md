# AWS S3 Configuration Guide

## 📋 Required Environment Variables

Để sử dụng AWS S3 cho lưu trữ bot code và ML models, bạn cần config các biến môi trường sau:

### 1. **AWS Credentials**
```bash
# AWS Access Keys
export AWS_ACCESS_KEY_ID=your_aws_access_key_id
export AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

# AWS Region
export AWS_DEFAULT_REGION=us-east-1

# S3 Bucket Name  
export AWS_S3_BUCKET_NAME=trading-bot-storage
```

### 2. **Optional: Custom Endpoint (LocalStack/MinIO)**
```bash
# For local development with LocalStack or MinIO
export AWS_S3_ENDPOINT_URL=http://localhost:4566
```

## 🔧 Setup Methods

### Method 1: Environment Variables (.env file)
Tạo file `.env` trong thư mục `bot_marketplace/`:

```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=AKIA...your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=us-east-1
AWS_S3_BUCKET_NAME=trading-bot-storage

# Optional for local testing
# AWS_S3_ENDPOINT_URL=http://localhost:4566
```

### Method 2: AWS CLI Configuration
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure
# Nhập: Access Key ID, Secret Access Key, Region, Output format

# Set bucket name
export AWS_S3_BUCKET_NAME=trading-bot-storage
```

### Method 3: IAM Role (Production)
Trong production, nên sử dụng IAM role thay vì access keys:

```bash
# Chỉ cần config region và bucket
export AWS_DEFAULT_REGION=us-east-1
export AWS_S3_BUCKET_NAME=trading-bot-storage
```

## 🪣 S3 Bucket Setup

### 1. **Tạo S3 Bucket**
```bash
# Sử dụng AWS CLI
aws s3 mb s3://trading-bot-storage --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket trading-bot-storage \
    --versioning-configuration Status=Enabled
```

### 2. **Bucket Structure**
Hệ thống sẽ tự động tạo cấu trúc thư mục:
```
trading-bot-storage/
├── bots/
│   ├── {bot_id}/
│   │   ├── code/
│   │   │   └── {version}/
│   │   │       └── bot.py
│   │   ├── models/
│   │   │   └── {version}/
│   │   │       ├── model.pkl
│   │   │       └── weights.h5
│   │   └── metadata/
│   │       └── {version}/
│   │           └── code_metadata.json
└── backups/
    └── bot_{bot_id}_{timestamp}.zip
```

## 🔐 IAM Permissions

Tạo IAM policy với quyền tối thiểu:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetBucketVersioning",
                "s3:PutBucketVersioning"
            ],
            "Resource": [
                "arn:aws:s3:::trading-bot-storage",
                "arn:aws:s3:::trading-bot-storage/*"
            ]
        }
    ]
}
```

## 🧪 Local Development với LocalStack

### 1. **Cài đặt LocalStack**
```bash
pip install localstack
```

### 2. **Chạy LocalStack**
```bash
# Start LocalStack
localstack start

# Hoặc với Docker
docker run --rm -it -p 4566:4566 -p 4510-4559:4510-4559 localstack/localstack
```

### 3. **Config cho LocalStack**
```env
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
AWS_S3_ENDPOINT_URL=http://localhost:4566
AWS_S3_BUCKET_NAME=trading-bot-storage
```

### 4. **Tạo bucket trong LocalStack**
```bash
aws --endpoint-url=http://localhost:4566 s3 mb s3://trading-bot-storage
```

## ✅ Verify Setup

Sau khi config, test bằng cách:

1. **Start application**:
```bash
cd bot_marketplace
python main.py
```

2. **Check health endpoint**:
```bash
curl http://localhost:8000/health
```

Response sẽ show S3 status:
```json
{
    "status": "healthy",
    "database": "healthy",
    "s3": "healthy",
    "bot_manager": "healthy"
}
```

3. **Check system info**:
```bash
curl http://localhost:8000/system/info
```

## 🐛 Troubleshooting

### Common Issues:

1. **"AWS credentials not found"**
   - Kiểm tra các env variables đã set chưa
   - Kiểm tra AWS CLI config: `aws configure list`

2. **"Bucket does not exist"**
   - Tạo bucket: `aws s3 mb s3://your-bucket-name`
   - Kiểm tra region đúng chưa

3. **"Access Denied"**
   - Kiểm tra IAM permissions
   - Kiểm tra bucket policy

4. **"LocalStack connection failed"**
   - Kiểm tra LocalStack đã chạy: `curl http://localhost:4566/health`
   - Config endpoint URL đúng

## 📚 API Usage Examples

### Upload Bot với S3:
```python
# POST /bots/with-code
files = {'file': open('my_bot.py', 'rb')}
data = {
    'name': 'My Trading Bot',
    'description': 'Advanced ML trading bot',
    'category_id': 1
}
response = requests.post('/bots/with-code', files=files, data=data)
```

### Create Subscription:
```python
# POST /subscriptions/
data = {
    'bot_id': 1,
    'symbol': 'BTCUSDT',
    'instance_name': 'my_bot_instance',
    'strategy_config': {'risk_level': 0.02}
}
response = requests.post('/subscriptions/', json=data)
```

Bot sẽ được load từ S3 và execute tự động! 🚀 
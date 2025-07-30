import boto3
import importlib.util
import sys
import os

BUCKET = 'your-bucket-name'  # Thay bằng bucket thật
S3_KEY = 'bots/demo/my_futures_bot.py'
LOCAL_BOT_PATH = '/tmp/my_futures_bot.py'

# 1. Upload file bot lên S3
def upload_to_s3(local_path, bucket, s3_key):
    s3 = boto3.client('s3')
    s3.upload_file(local_path, bucket, s3_key)
    print(f"✅ Uploaded {local_path} to s3://{bucket}/{s3_key}")

# 2. Download file bot từ S3 về local
def download_from_s3(bucket, s3_key, local_path):
    s3 = boto3.client('s3')
    s3.download_file(bucket, s3_key, local_path)
    print(f"✅ Downloaded s3://{bucket}/{s3_key} to {local_path}")

# 3. Import động class bot từ file vừa tải về
def dynamic_import(module_path, class_name):
    spec = importlib.util.spec_from_file_location("dynamic_bot", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["dynamic_bot"] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)

if __name__ == "__main__":
    # Giả sử bạn đã có file my_futures_bot.py ở thư mục hiện tại
    local_file = "my_futures_bot.py"  # Đảm bảo file này tồn tại
    
    # 1. Upload lên S3
    upload_to_s3(local_file, BUCKET, S3_KEY)
    
    # 2. Download về lại (giả lập worker)
    download_from_s3(BUCKET, S3_KEY, LOCAL_BOT_PATH)
    
    # 3. Import động và chạy thử
    BotClass = dynamic_import(LOCAL_BOT_PATH, "MyFuturesBot")  # Đảm bảo class đúng tên
    
    # 4. Khởi tạo và chạy thử bot
    config = {"param1": 123}
    api_keys = {"api_key": "demo", "api_secret": "demo"}
    bot = BotClass(config, api_keys)
    print("✅ Bot instance created from S3 code:", bot)
    # Có thể gọi bot.execute_algorithm(...) hoặc các method khác tuỳ ý 
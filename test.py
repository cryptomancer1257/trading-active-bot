
import sys
sys.path.append('.')
from s3_manager import S3Manager
from database import SessionLocal
import crud

# Initialize S3 manager
s3_manager = S3Manager()

# Read the bot file
with open('E:/projects/bot_trading/bot_marketplace/bots/golden_cross_bot.py', 'r', encoding='utf-8') as f:
    code_content = f.read()

print('File content length:', len(code_content))
print('First 200 chars:', code_content[:200])

# Upload to S3
try:
    result = s3_manager.upload_bot_code(
        bot_id=7,
        code_content=code_content,
        filename='golden_cross_bot.py',
        version='1.2.1'
    )
    print('Upload result:', result)
except Exception as e:
    print('Upload error:', str(e))
    import traceback
    traceback.print_exc()

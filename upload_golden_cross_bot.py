#!/usr/bin/env python3
"""
Script to upload Golden Cross Bot v1.2.0 to S3
"""

import sys
import os
sys.path.append('.')

from s3_manager import S3Manager
from database import SessionLocal
import crud
import models

def upload_golden_cross_bot():
    """Upload Golden Cross Bot to S3 with version 1.2.0"""
    
    # Initialize S3 manager
    s3_manager = S3Manager()
    
    # Read the bot file
    bot_file_path = 'bots/golden_cross_bot.py'
    
    if not os.path.exists(bot_file_path):
        print(f"Error: Bot file {bot_file_path} not found")
        return False
    
    try:
        with open(bot_file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        print(f"✅ Bot file loaded successfully")
        print(f"   File size: {len(code_content)} characters")
        print(f"   First 100 chars: {code_content[:100]}...")
        
        # Upload to S3
        print(f"\n📤 Uploading to S3...")
        result = s3_manager.upload_bot_code(
            bot_id=7,
            code_content=code_content,
            filename='golden_cross_bot.py',
            version='1.2.0'
        )
        
        print(f"✅ Upload successful!")
        print(f"   S3 Key: {result['s3_key']}")
        print(f"   Version: {result['version']}")
        print(f"   Size: {result.get('size', 'unknown')} bytes")
        
        # Update database
        print(f"\n📝 Updating database...")
        db = SessionLocal()
        
        try:
            # Update bot record
            bot_record = crud.get_bot_by_id(db, 7)
            if bot_record:
                bot_record.code_path = result['s3_key']
                bot_record.version = result['version']
                db.commit()
                print(f"✅ Database updated successfully")
            else:
                print(f"❌ Bot with ID 7 not found in database")
                
        except Exception as e:
            print(f"❌ Database update failed: {e}")
            db.rollback()
            
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bot_loading():
    """Test loading bot from S3"""
    print(f"\n🧪 Testing bot loading from S3...")
    
    try:
        db = SessionLocal()
        
        # Test loading bot from S3
        bot_instance = crud.load_bot_from_s3(
            bot_id=7,
            version='1.2.0',
            user_config={
                'short_window': 50,
                'long_window': 200,
                'position_size': 0.3,
                'timeframe': '1h'
            },
            user_api_keys={
                'key': 'test_key',
                'secret': 'test_secret'
            }
        )
        
        if bot_instance:
            print(f"✅ Bot loaded successfully from S3")
            print(f"   Bot name: {bot_instance.bot_name}")
            print(f"   Version: {bot_instance.version}")
            print(f"   Short window: {bot_instance.short_window}")
            print(f"   Long window: {bot_instance.long_window}")
            return True
        else:
            print(f"❌ Failed to load bot from S3")
            return False
            
    except Exception as e:
        print(f"❌ Bot loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    print("=== Golden Cross Bot S3 Upload ===")
    
    # Upload bot
    upload_success = upload_golden_cross_bot()
    
    if upload_success:
        # Test loading
        test_bot_loading()
        
        print(f"\n🎉 All done! You can now:")
        print(f"   1. Create new trial subscription for Golden Cross Bot")
        print(f"   2. Bot will be loaded from S3 with version 1.2.0")
        print(f"   3. Enhanced features: volume filtering, volatility checks, trend confirmation")
        
    else:
        print(f"\n❌ Upload failed. Please check the errors above.") 
#!/usr/bin/env python3
"""
Create Alternating Bot via Admin API
"""

import os
import sys
import requests
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from s3_manager import S3Manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "system@botmarketplace.com"
ADMIN_PASSWORD = "system_password_123"

def get_admin_token() -> Optional[str]:
    """Get admin access token"""
    try:
        login_data = {
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Successfully logged in as admin")
            return result["access_token"]
        else:
            logger.error(f"Failed to login: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting admin token: {e}")
        return None

def create_bot_via_admin_api(token: str) -> Optional[Dict[str, Any]]:
    """Create bot via admin API"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        bot_data = {
            "name": "Alternating Trading Bot",
            "description": "Simple strategy that alternates between BUY and SELL every timeframe with configurable allocation percentage. Perfect for testing and demonstrating consistent trading activity.",
            "version": "1.0.0",
            "bot_type": "TECHNICAL",
            "is_free": True,
            "price_per_month": 0.00,
            "default_config": {
                "allocation_percentage": 5.0,
                "enable_alternating": True,
                "start_with_buy": True,
                "timeframe": "1m"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/admin/bots",
            json=bot_data,
            headers=headers
        )
        
        if response.status_code == 201:
            result = response.json()
            logger.info(f"Successfully created bot via API: {result['id']}")
            return result
        else:
            logger.error(f"Failed to create bot: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating bot via API: {e}")
        return None

def upload_bot_code_to_s3(bot_id: int) -> Optional[str]:
    """Upload bot code using S3Manager upload_bot_code function"""
    try:
        # Read bot code
        bot_file = "bots/alternating_bot.py"
        
        if not os.path.exists(bot_file):
            logger.error(f"Bot file {bot_file} not found!")
            return None
        
        with open(bot_file, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        # Initialize S3Manager
        s3_manager = S3Manager()
        
        # Upload using upload_bot_code function
        upload_result = s3_manager.upload_bot_code(
            bot_id=bot_id,
            code_content=code_content,
            filename="alternating_bot.py",
            version="1.0.0"
        )
        
        if upload_result:
            logger.info(f"Successfully uploaded bot code to S3: {upload_result['s3_key']}")
            return upload_result['s3_key']
        else:
            logger.error("Failed to upload bot code to S3")
            return None
            
    except Exception as e:
        logger.error(f"Error uploading bot code: {e}")
        return None

def update_bot_code_path(bot_id: int, code_path: str) -> bool:
    """Update bot with code_path in database"""
    try:
        from database import get_db
        from sqlalchemy import text
        
        db = next(get_db())
        
        # Update using SQL directly to avoid column assignment issues
        db.execute(
            text("UPDATE bots SET code_path = :code_path WHERE id = :bot_id"),
            {"code_path": code_path, "bot_id": bot_id}
        )
        
        db.commit()
        logger.info(f"Successfully updated bot {bot_id} with code_path: {code_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating bot code_path: {e}")
        return False
    finally:
        db.close()

def main():
    """Main process"""
    logger.info("Starting Alternating Bot creation via Admin API...")
    
    # Step 1: Get admin token
    token = get_admin_token()
    if not token:
        logger.error("Failed to get admin token")
        return False
    
    # Step 2: Create bot via admin API
    created_bot = create_bot_via_admin_api(token)
    if not created_bot:
        logger.error("Failed to create bot via API")
        return False
    
    bot_id = created_bot['id']
    
    # Step 3: Upload bot code using S3Manager
    code_path = upload_bot_code_to_s3(bot_id)
    if not code_path:
        logger.error("Failed to upload bot code")
        return False
    
    # Step 4: Update bot with code_path
    if not update_bot_code_path(bot_id, code_path):
        logger.error("Failed to update bot code_path")
        return False
    
    logger.info("✅ Alternating Bot created successfully via Admin API!")
    logger.info(f"Bot ID: {bot_id}")
    logger.info(f"Bot Name: {created_bot['name']}")
    logger.info(f"Status: {created_bot['status']}")
    logger.info(f"Code Path: {code_path}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
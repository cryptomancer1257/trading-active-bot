#!/usr/bin/env python3
"""
Script to update API key for a user
"""

from sqlalchemy.orm import Session
from core.database import SessionLocal, engine
from core import models

def update_user_api_key(user_id: int, api_key: str):
    """Update API key for a user"""
    db = SessionLocal()
    try:
        # Find user
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            print(f"❌ User with ID {user_id} not found")
            return False
        
        # Update API key
        user.api_key = api_key
        db.commit()
        db.refresh(user)
        
        print(f"✅ Updated API key for user {user.email} (ID: {user.id})")
        print(f"   API Key: {api_key}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating API key: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Update user ID 2 with test API key
    api_key = "test_marketplace_api_key_12345"
    update_user_api_key(2, api_key)

#!/usr/bin/env python3
"""
Create admin user for seeding prompt templates
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core import models, crud
from core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user():
    """Create admin user"""
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(models.User).filter(models.User.role == "ADMIN").first()
        if admin_user:
            logger.info(f"Admin user already exists: {admin_user.email}")
            return admin_user
        
        # Create admin user
        admin_data = {
            "email": "admin@quantumforge.com",
            "hashed_password": get_password_hash("admin123"),  # In production, use a secure password
            "developer_name": "System Administrator",
            "role": "ADMIN",
            "is_active": True
        }
        
        # Create user
        admin_user = models.User(**admin_data)
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"✅ Created admin user: {admin_user.email}")
        return admin_user
        
    except Exception as e:
        logger.error(f"❌ Error creating admin user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()

#!/usr/bin/env python3
"""
Script to create test bot and approve it
"""

from sqlalchemy.orm import Session
from core.database import SessionLocal
from core import models
from datetime import datetime

def create_test_data():
    """Create test bot category and bot"""
    db = SessionLocal()
    try:
        # Create bot category if not exists
        category = db.query(models.BotCategory).filter(models.BotCategory.name == "Test Category").first()
        if not category:
            category = models.BotCategory(
                name="Test Category",
                description="Test category for marketplace testing"
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            print(f"✅ Created category: {category.name} (ID: {category.id})")
        else:
            print(f"✅ Category exists: {category.name} (ID: {category.id})")
        
        # Create bot if not exists
        bot = db.query(models.Bot).filter(models.Bot.id == 1).first()
        if not bot:
            bot = models.Bot(
                id=1,
                name="Test Trading Bot",
                description="A test trading bot for marketplace testing",
                category_id=category.id,
                developer_id=2,  # Our test user
                status=models.BotStatus.APPROVED,  # Pre-approve it
                approved_by=2,
                approved_at=datetime.now(),
                price=10.0,
                code_file_path="/test/bot.py",
                exchange=models.ExchangeType.BINANCE
            )
            db.add(bot)
            db.commit()
            db.refresh(bot)
            print(f"✅ Created bot: {bot.name} (ID: {bot.id})")
        else:
            # Make sure it's approved
            bot.status = models.BotStatus.APPROVED
            bot.approved_by = 2
            bot.approved_at = datetime.now()
            db.commit()
            print(f"✅ Bot exists and approved: {bot.name} (ID: {bot.id})")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()

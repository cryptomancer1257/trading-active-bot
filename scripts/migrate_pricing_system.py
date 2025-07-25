#!/usr/bin/env python3
"""
Migration script for advanced pricing system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from core.database import get_db
from core import models, crud, schemas
from decimal import Decimal
from datetime import datetime, timedelta

def create_pricing_tables():
    """Create new pricing tables"""
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    # Create BotPricingPlan table
    engine.execute(text("""
        CREATE TABLE IF NOT EXISTS bot_pricing_plans (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bot_id INT NOT NULL,
            plan_name VARCHAR(100) NOT NULL,
            plan_description TEXT,
            price_per_month DECIMAL(10, 2) DEFAULT 0.00,
            price_per_year DECIMAL(10, 2) DEFAULT 0.00,
            price_per_quarter DECIMAL(10, 2) DEFAULT 0.00,
            max_trading_pairs INT DEFAULT 1,
            max_daily_trades INT DEFAULT 10,
            max_position_size DECIMAL(5, 2) DEFAULT 0.10,
            advanced_features JSON,
            trial_days INT DEFAULT 0,
            trial_trades_limit INT DEFAULT 5,
            is_active BOOLEAN DEFAULT TRUE,
            is_popular BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE
        )
    """))
    
    # Create BotPromotion table
    engine.execute(text("""
        CREATE TABLE IF NOT EXISTS bot_promotions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bot_id INT NOT NULL,
            promotion_code VARCHAR(50) UNIQUE NOT NULL,
            promotion_name VARCHAR(100) NOT NULL,
            promotion_description TEXT,
            discount_type VARCHAR(20) NOT NULL,
            discount_value DECIMAL(10, 2) NOT NULL,
            max_uses INT DEFAULT 100,
            used_count INT DEFAULT 0,
            valid_from DATETIME NOT NULL,
            valid_until DATETIME NOT NULL,
            min_subscription_months INT DEFAULT 1,
            applicable_plans JSON,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INT NOT NULL,
            FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """))
    
    # Create SubscriptionInvoice table
    engine.execute(text("""
        CREATE TABLE IF NOT EXISTS subscription_invoices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subscription_id INT NOT NULL,
            user_id INT NOT NULL,
            invoice_number VARCHAR(50) UNIQUE NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'USD',
            base_price DECIMAL(10, 2) NOT NULL,
            discount_amount DECIMAL(10, 2) DEFAULT 0.00,
            tax_amount DECIMAL(10, 2) DEFAULT 0.00,
            final_amount DECIMAL(10, 2) NOT NULL,
            billing_period_start DATETIME NOT NULL,
            billing_period_end DATETIME NOT NULL,
            status VARCHAR(20) DEFAULT 'PENDING',
            payment_method VARCHAR(50),
            payment_date DATETIME,
            promotion_code VARCHAR(50),
            promotion_discount DECIMAL(10, 2) DEFAULT 0.00,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            due_date DATETIME NOT NULL,
            FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """))
    
    # Add pricing_plan_id to subscriptions table
    try:
        engine.execute(text("""
            ALTER TABLE subscriptions 
            ADD COLUMN pricing_plan_id INT,
            ADD COLUMN billing_cycle VARCHAR(20) DEFAULT 'MONTHLY',
            ADD COLUMN next_billing_date DATETIME,
            ADD COLUMN auto_renew BOOLEAN DEFAULT TRUE,
            ADD FOREIGN KEY (pricing_plan_id) REFERENCES bot_pricing_plans(id)
        """))
    except Exception as e:
        print(f"Columns might already exist: {e}")

def migrate_existing_bots():
    """Migrate existing bots to new pricing system"""
    db = next(get_db())
    
    try:
        # Get all existing bots
        bots = db.query(models.Bot).all()
        
        for bot in bots:
            print(f"Migrating bot: {bot.name}")
            
            # Create default pricing plan based on existing price
            default_plan = models.BotPricingPlan(
                bot_id=bot.id,
                plan_name="Standard" if bot.price_per_month > 0 else "Free",
                plan_description=f"Standard plan for {bot.name}",
                price_per_month=bot.price_per_month,
                price_per_year=bot.price_per_month * 10 if bot.price_per_month > 0 else 0,  # 10% discount
                price_per_quarter=bot.price_per_month * 2.5 if bot.price_per_month > 0 else 0,  # 17% discount
                max_trading_pairs=1,
                max_daily_trades=10,
                max_position_size=Decimal('0.10'),
                trial_days=7 if bot.price_per_month > 0 else 0,
                trial_trades_limit=5,
                is_active=True,
                is_popular=False
            )
            
            db.add(default_plan)
            
            # Create a "Pro" plan for paid bots
            if bot.price_per_month > 0:
                pro_plan = models.BotPricingPlan(
                    bot_id=bot.id,
                    plan_name="Pro",
                    plan_description=f"Pro plan for {bot.name} with advanced features",
                    price_per_month=bot.price_per_month * 2,  # Double the price
                    price_per_year=bot.price_per_month * 18,  # 25% discount
                    price_per_quarter=bot.price_per_month * 5,  # 17% discount
                    max_trading_pairs=3,
                    max_daily_trades=50,
                    max_position_size=Decimal('0.25'),
                    advanced_features={
                        "priority_execution": True,
                        "advanced_analytics": True,
                        "custom_indicators": True,
                        "api_access": True
                    },
                    trial_days=3,
                    trial_trades_limit=10,
                    is_active=True,
                    is_popular=True
                )
                db.add(pro_plan)
        
        db.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()

def create_sample_promotions():
    """Create sample promotions for testing"""
    db = next(get_db())
    
    try:
        # Get some bots
        bots = db.query(models.Bot).limit(3).all()
        
        for bot in bots:
            # Create a percentage discount promotion
            percentage_promo = models.BotPromotion(
                bot_id=bot.id,
                promotion_code=f"SAVE20_{bot.id}",
                promotion_name="20% Off Launch",
                promotion_description="Get 20% off your first month!",
                discount_type="PERCENTAGE",
                discount_value=Decimal('20.00'),
                max_uses=50,
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=30),
                min_subscription_months=1,
                applicable_plans=[1, 2],  # Standard and Pro plans
                is_active=True,
                created_by=1  # Assuming admin user ID is 1
            )
            db.add(percentage_promo)
            
            # Create a free trial promotion
            trial_promo = models.BotPromotion(
                bot_id=bot.id,
                promotion_code=f"FREETRIAL_{bot.id}",
                promotion_name="Free Trial Week",
                promotion_description="Try for free for 7 days!",
                discount_type="FREE_TRIAL",
                discount_value=Decimal('0.00'),
                max_uses=100,
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=60),
                min_subscription_months=1,
                applicable_plans=[1],  # Standard plan only
                is_active=True,
                created_by=1
            )
            db.add(trial_promo)
        
        db.commit()
        print("Sample promotions created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Failed to create sample promotions: {e}")
        raise
    finally:
        db.close()

def main():
    """Main migration function"""
    print("🚀 Starting Pricing System Migration...")
    
    # Step 1: Create tables
    print("📋 Creating pricing tables...")
    create_pricing_tables()
    
    # Step 2: Migrate existing bots
    print("🔄 Migrating existing bots...")
    migrate_existing_bots()
    
    # Step 3: Create sample promotions
    print("🎁 Creating sample promotions...")
    create_sample_promotions()
    
    print("✅ Migration completed successfully!")
    print("\n📊 New Features Available:")
    print("   • Multiple pricing plans per bot")
    print("   • Promotional codes and discounts")
    print("   • Detailed invoice tracking")
    print("   • Annual/quarterly billing options")
    print("   • Trial periods and usage limits")

if __name__ == "__main__":
    main() 
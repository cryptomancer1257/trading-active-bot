#!/usr/bin/env python3
"""
Test script for the new pricing system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db
from core import crud, models, schemas
from decimal import Decimal
from datetime import datetime, timedelta

def test_pricing_plans():
    """Test pricing plan creation and management"""
    print("🧪 Testing Pricing Plans")
    print("=" * 40)
    
    db = next(get_db())
    
    try:
        # Get a bot to test with
        bot = db.query(models.Bot).first()
        if not bot:
            print("❌ No bots found in database")
            return
        
        print(f"📊 Testing with bot: {bot.name}")
        
        # Create pricing plans
        free_plan = crud.create_pricing_plan(db, schemas.PricingPlanCreate(
            plan_name="Free",
            plan_description="Basic free plan with limited features",
            price_per_month=Decimal('0.00'),
            max_trading_pairs=1,
            max_daily_trades=5,
            trial_days=0
        ), bot.id)
        
        basic_plan = crud.create_pricing_plan(db, schemas.PricingPlanCreate(
            plan_name="Basic",
            plan_description="Standard plan for serious traders",
            price_per_month=Decimal('29.99'),
            price_per_year=Decimal('299.99'),
            price_per_quarter=Decimal('79.99'),
            max_trading_pairs=2,
            max_daily_trades=20,
            trial_days=7,
            trial_trades_limit=10
        ), bot.id)
        
        pro_plan = crud.create_pricing_plan(db, schemas.PricingPlanCreate(
            plan_name="Pro",
            plan_description="Professional plan with advanced features",
            price_per_month=Decimal('99.99'),
            price_per_year=Decimal('999.99'),
            price_per_quarter=Decimal('269.99'),
            max_trading_pairs=5,
            max_daily_trades=100,
            max_position_size=Decimal('0.25'),
            advanced_features={
                "priority_execution": True,
                "advanced_analytics": True,
                "custom_indicators": True,
                "api_access": True,
                "dedicated_support": True
            },
            trial_days=3,
            trial_trades_limit=20,
            is_popular=True
        ), bot.id)
        
        print("✅ Pricing plans created successfully!")
        
        # Get all plans
        plans = crud.get_bot_pricing_plans(db, bot.id)
        print(f"📋 Found {len(plans)} pricing plans:")
        for plan in plans:
            print(f"   • {plan.plan_name}: ${plan.price_per_month}/month")
        
        return bot, plans
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None
    finally:
        db.close()

def test_promotions():
    """Test promotion creation and validation"""
    print("\n🎁 Testing Promotions")
    print("=" * 30)
    
    db = next(get_db())
    
    try:
        # Get a bot
        bot = db.query(models.Bot).first()
        if not bot:
            print("❌ No bots found")
            return
        
        # Create promotions
        percentage_promo = crud.create_promotion(db, schemas.PromotionCreate(
            promotion_code="SAVE20",
            promotion_name="20% Off Launch",
            promotion_description="Get 20% off your first month!",
            discount_type="PERCENTAGE",
            discount_value=Decimal('20.00'),
            max_uses=100,
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=30),
            min_subscription_months=1
        ), bot.id, 1)  # Assuming user ID 1
        
        fixed_promo = crud.create_promotion(db, schemas.PromotionCreate(
            promotion_code="FREETRIAL",
            promotion_name="Free Trial Week",
            promotion_description="Try for free for 7 days!",
            discount_type="FREE_TRIAL",
            discount_value=Decimal('0.00'),
            max_uses=50,
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=60),
            min_subscription_months=1
        ), bot.id, 1)
        
        print("✅ Promotions created successfully!")
        
        # Test promotion validation
        promotion, error = crud.validate_promotion(db, "SAVE20", bot.id, 1)
        if promotion:
            print(f"✅ Promotion validation successful: {promotion.promotion_name}")
        else:
            print(f"❌ Promotion validation failed: {error}")
        
        return bot
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        db.close()

def test_price_calculation():
    """Test price calculation with different scenarios"""
    print("\n💰 Testing Price Calculation")
    print("=" * 35)
    
    db = next(get_db())
    
    try:
        # Get a pricing plan
        plan = db.query(models.BotPricingPlan).first()
        if not plan:
            print("❌ No pricing plans found")
            return
        
        print(f"📊 Testing with plan: {plan.plan_name}")
        
        # Test different billing cycles
        billing_cycles = ["MONTHLY", "QUARTERLY", "YEARLY"]
        
        for cycle in billing_cycles:
            pricing = crud.calculate_subscription_price(plan, cycle)
            print(f"   {cycle}: ${pricing['final_amount']} (Base: ${pricing['base_price']})")
        
        # Test with promotion
        promotion = db.query(models.BotPromotion).first()
        if promotion:
            print(f"\n🎁 Testing with promotion: {promotion.promotion_name}")
            pricing = crud.calculate_subscription_price(plan, "MONTHLY", promotion)
            print(f"   With {promotion.discount_type} discount: ${pricing['final_amount']}")
            print(f"   Savings: ${pricing['discount_amount']}")
        
        print("✅ Price calculation tests completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

def test_subscription_creation():
    """Test subscription creation with pricing plan"""
    print("\n📝 Testing Subscription Creation")
    print("=" * 40)
    
    db = next(get_db())
    
    try:
        # Get a bot and pricing plan
        bot = db.query(models.Bot).first()
        plan = db.query(models.BotPricingPlan).first()
        
        if not bot or not plan:
            print("❌ Bot or pricing plan not found")
            return
        
        # Create subscription data
        subscription_data = schemas.SubscriptionCreate(
            bot_id=bot.id,
            instance_name="Test Instance",
            trading_pair="BTC/USDT",
            timeframe="1h",
            strategy_config={},
            execution_config=schemas.ExecutionConfig(
                order_type="market",
                initial_balance=1000.0,
                max_position_size=0.1
            ),
            risk_config=schemas.RiskConfig(
                trailing_stop=False,
                max_daily_loss=0.05,
                max_loss_per_trade=0.02
            ),
            is_testnet=True
        )
        
        # Create subscription with pricing plan
        subscription = crud.create_subscription_with_plan(
            db, subscription_data, 1, plan.id, "SAVE20"  # Assuming user ID 1
        )
        
        print(f"✅ Subscription created: {subscription.id}")
        print(f"   Bot: {bot.name}")
        print(f"   Plan: {plan.plan_name}")
        print(f"   Status: {subscription.status.value}")
        
        # Check if invoice was created
        invoices = crud.get_subscription_invoices(db, subscription.id)
        if invoices:
            invoice = invoices[0]
            print(f"   Invoice: {invoice.invoice_number}")
            print(f"   Amount: ${invoice.final_amount}")
            print(f"   Status: {invoice.status}")
        
        print("✅ Subscription creation test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    """Main test function"""
    print("🚀 Bot Marketplace - Pricing System Test")
    print("=" * 50)
    
    # Test pricing plans
    bot, plans = test_pricing_plans()
    
    # Test promotions
    test_promotions()
    
    # Test price calculation
    test_price_calculation()
    
    # Test subscription creation
    test_subscription_creation()
    
    print("\n🎉 All tests completed!")
    print("\n📋 Next Steps:")
    print("   1. Run migration: python scripts/migrate_pricing_system.py")
    print("   2. Update API routes in main.py")
    print("   3. Test the new pricing endpoints")
    print("   4. Update frontend to use new pricing system")

if __name__ == "__main__":
    main() 
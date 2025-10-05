#!/usr/bin/env python3
"""
Test LLM Provider Selector
Tests the new LLM billing system and provider selection logic
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core import models
from services.llm_provider_selector import LLMProviderSelector
from datetime import datetime, timedelta


def test_byok_provider():
    """Test BYOK (Bring Your Own Keys) provider selection"""
    print("\n" + "="*60)
    print("TEST 1: BYOK Provider Selection")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Get first user with LLM providers
        user = db.query(models.User).filter(
            models.User.llm_providers.any()
        ).first()
        
        if not user:
            print("❌ No users with LLM providers found")
            print("💡 Hint: Go to http://localhost:3001/creator/llm-providers to add a provider")
            return
        
        print(f"✅ Found user: {user.email} (ID: {user.id})")
        
        # Show their providers
        providers = db.query(models.LLMProvider).filter(
            models.LLMProvider.user_id == user.id,
            models.LLMProvider.is_active == True
        ).all()
        
        print(f"\n📋 User has {len(providers)} active provider(s):")
        for p in providers:
            default_marker = "⭐ DEFAULT" if p.is_default else ""
            print(f"  - {p.provider_type.value}: {p.name} {default_marker}")
            print(f"    API Key: {p.api_key[:10]}... (hidden)")
        
        # Test provider selection
        print("\n🔍 Testing provider selection...")
        selector = LLMProviderSelector(db)
        
        try:
            source_type, provider_config = selector.get_provider_for_developer(
                developer_id=user.id
            )
            
            print(f"\n✅ Provider Selected:")
            print(f"   Source: {source_type}")
            print(f"   Provider: {provider_config['provider']}")
            print(f"   Model: {provider_config['model']}")
            print(f"   Is Free: {provider_config['is_free']}")
            print(f"   Is Default: {provider_config.get('is_default', False)}")
            
            # Test usage logging
            print("\n📊 Testing usage logging...")
            selector.log_usage(
                developer_id=user.id,
                provider_config=provider_config,
                bot_id=None,
                request_type="test",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.0
            )
            print("✅ Usage logged successfully")
            
            # Show usage stats
            stats = selector.get_usage_stats(user.id, days=7)
            print(f"\n📈 Usage Stats (Last 7 days):")
            print(f"   BYOK:")
            print(f"      Requests: {stats['user_configured']['requests']}")
            print(f"      Tokens: {stats['user_configured']['tokens']:,}")
            print(f"   Platform:")
            print(f"      Requests: {stats['platform']['requests']}")
            print(f"      Tokens: {stats['platform']['tokens']:,}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        db.close()


def test_platform_subscription():
    """Test Platform subscription provider selection"""
    print("\n" + "="*60)
    print("TEST 2: Platform Subscription Selection")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Check if there are any subscriptions
        subscription = db.query(models.DeveloperLLMSubscription).filter(
            models.DeveloperLLMSubscription.status == 'ACTIVE',
            models.DeveloperLLMSubscription.payment_status == 'PAID',
            models.DeveloperLLMSubscription.end_date > datetime.now()
        ).first()
        
        if not subscription:
            print("❌ No active platform subscriptions found")
            print("\n💡 To test platform subscriptions, run this SQL:")
            print("""
            -- Get a plan ID
            SELECT id, name FROM llm_subscription_plans WHERE is_active = TRUE LIMIT 1;
            
            -- Create a test subscription (use your user ID and plan ID)
            INSERT INTO developer_llm_subscriptions 
            (developer_id, plan_id, status, start_date, end_date, payment_status)
            VALUES 
            (1, 2, 'ACTIVE', NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), 'PAID');
            """)
            return
        
        print(f"✅ Found active subscription: {subscription.plan.name}")
        print(f"   Developer ID: {subscription.developer_id}")
        print(f"   Expires: {subscription.end_date}")
        print(f"   Usage: {subscription.requests_used}/{subscription.plan.max_requests_per_month} requests")
        print(f"   Tokens: {subscription.tokens_used:,}/{subscription.plan.max_tokens_per_month:,}")
        
        # Test provider selection
        print("\n🔍 Testing provider selection...")
        selector = LLMProviderSelector(db)
        
        try:
            source_type, provider_config = selector.get_provider_for_developer(
                developer_id=subscription.developer_id
            )
            
            print(f"\n✅ Provider Selected:")
            print(f"   Source: {source_type}")
            print(f"   Provider: {provider_config['provider']}")
            print(f"   Model: {provider_config['model']}")
            print(f"   Is Free: {provider_config['is_free']}")
            if not provider_config['is_free']:
                print(f"   Plan: {provider_config['plan_name']}")
                print(f"   Requests Remaining: {provider_config['requests_remaining']:,}")
                print(f"   Tokens Remaining: {provider_config['tokens_remaining']:,}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        db.close()


def test_available_plans():
    """Show available subscription plans"""
    print("\n" + "="*60)
    print("TEST 3: Available Subscription Plans")
    print("="*60)
    
    db = SessionLocal()
    try:
        plans = db.query(models.LLMSubscriptionPlan).filter(
            models.LLMSubscriptionPlan.is_active == True
        ).order_by(models.LLMSubscriptionPlan.display_order).all()
        
        print(f"\n📦 {len(plans)} Active Plans:\n")
        
        for plan in plans:
            print(f"{'='*50}")
            print(f"📋 {plan.name} - ${plan.price_per_month}/month")
            print(f"   {plan.description}")
            print(f"   Limits:")
            print(f"      ├─ Requests: {plan.max_requests_per_month:,}/month")
            print(f"      └─ Tokens: {plan.max_tokens_per_month:,}/month")
            print(f"   Providers: {', '.join(plan.available_providers)}")
            print(f"   Models:")
            for provider, models_list in plan.available_models.items():
                print(f"      ├─ {provider}: {', '.join(models_list)}")
        
    finally:
        db.close()


def main():
    """Run all tests"""
    print("\n" + "🤖"*30)
    print("LLM PROVIDER SELECTOR TEST SUITE")
    print("🤖"*30)
    
    try:
        # Test 1: BYOK providers
        test_byok_provider()
        
        # Test 2: Platform subscriptions
        test_platform_subscription()
        
        # Test 3: Available plans
        test_available_plans()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


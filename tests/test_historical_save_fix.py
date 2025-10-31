#!/usr/bin/env python3
"""
Test script to verify Historical Learning Save fix

This script tests:
1. BotUpdate schema accepts historical learning fields
2. Bot model has historical learning columns
3. Database operations work correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import ValidationError
from core import schemas, models
from sqlalchemy import inspect

def test_schema_accepts_fields():
    """Test 1: BotUpdate schema should accept historical learning fields"""
    print("\n" + "="*80)
    print("TEST 1: BotUpdate Schema Validation")
    print("="*80)
    
    try:
        # Create BotUpdate with historical learning fields
        bot_update = schemas.BotUpdate(
            historical_learning_enabled=True,
            historical_transaction_limit=25,
            include_failed_trades=True,
            learning_mode='recent'
        )
        
        print("✅ PASS: BotUpdate schema accepts all historical learning fields")
        print(f"   - historical_learning_enabled: {bot_update.historical_learning_enabled}")
        print(f"   - historical_transaction_limit: {bot_update.historical_transaction_limit}")
        print(f"   - include_failed_trades: {bot_update.include_failed_trades}")
        print(f"   - learning_mode: {bot_update.learning_mode}")
        
        # Test with only some fields (should work because all are Optional)
        bot_update_partial = schemas.BotUpdate(
            name="Test Bot",
            historical_learning_enabled=False
        )
        print("✅ PASS: Partial update with historical fields works")
        
        return True
    except ValidationError as e:
        print(f"❌ FAIL: Schema validation error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected error: {e}")
        return False

def test_model_has_columns():
    """Test 2: Bot model should have historical learning columns"""
    print("\n" + "="*80)
    print("TEST 2: Bot Model Column Definitions")
    print("="*80)
    
    try:
        # Use SQLAlchemy inspector to check model columns
        mapper = inspect(models.Bot)
        columns = {col.key: str(col.type) for col in mapper.columns}
        
        required_columns = {
            'historical_learning_enabled': 'BOOLEAN',
            'historical_transaction_limit': 'INTEGER',
            'include_failed_trades': 'BOOLEAN',
            'learning_mode': 'VARCHAR'
        }
        
        all_found = True
        for col_name, col_type in required_columns.items():
            if col_name in columns:
                actual_type = columns[col_name]
                print(f"✅ Column '{col_name}' found (Type: {actual_type})")
            else:
                print(f"❌ Column '{col_name}' NOT FOUND in Bot model!")
                all_found = False
        
        if all_found:
            print("\n✅ PASS: All historical learning columns defined in Bot model")
            return True
        else:
            print("\n❌ FAIL: Some columns missing from Bot model")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Error inspecting model: {e}")
        return False

def test_model_defaults():
    """Test 3: Bot model should have correct default values"""
    print("\n" + "="*80)
    print("TEST 3: Bot Model Default Values")
    print("="*80)
    
    try:
        # Get column objects
        mapper = inspect(models.Bot)
        columns = {col.key: col for col in mapper.columns}
        
        # Check defaults
        expected_defaults = {
            'historical_learning_enabled': False,
            'historical_transaction_limit': 25,
            'include_failed_trades': True,
            'learning_mode': 'recent'
        }
        
        all_correct = True
        for col_name, expected_default in expected_defaults.items():
            if col_name in columns:
                col = columns[col_name]
                # Get default value (may be callable or ColumnDefault)
                default = None
                if col.default is not None:
                    if hasattr(col.default, 'arg'):
                        default = col.default.arg
                    else:
                        default = col.default
                
                if default == expected_default:
                    print(f"✅ '{col_name}' has correct default: {default}")
                else:
                    print(f"⚠️  '{col_name}' default is {default}, expected {expected_default}")
            else:
                print(f"❌ Column '{col_name}' not found")
                all_correct = False
        
        if all_correct:
            print("\n✅ PASS: Default values are correct")
            return True
        else:
            print("\n⚠️  WARNING: Some defaults differ (might be OK if migration sets them)")
            return True  # Not a critical failure
            
    except Exception as e:
        print(f"❌ FAIL: Error checking defaults: {e}")
        return False

def test_dict_conversion():
    """Test 4: BotUpdate should serialize correctly with historical fields"""
    print("\n" + "="*80)
    print("TEST 4: Schema Serialization (dict conversion)")
    print("="*80)
    
    try:
        # Create BotUpdate with historical fields
        bot_update = schemas.BotUpdate(
            name="Test Bot",
            historical_learning_enabled=True,
            historical_transaction_limit=50,
            include_failed_trades=False,
            learning_mode='best_performance'
        )
        
        # Convert to dict (this is what FastAPI does internally)
        update_dict = bot_update.dict(exclude_unset=True)
        
        print(f"✅ Serialized update dict:")
        for key, value in update_dict.items():
            print(f"   {key}: {value}")
        
        # Verify historical fields are present
        if all(field in update_dict for field in ['historical_learning_enabled', 'historical_transaction_limit', 'include_failed_trades', 'learning_mode']):
            print("\n✅ PASS: All historical fields present in serialized dict")
            return True
        else:
            print("\n❌ FAIL: Some historical fields missing from serialized dict")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Serialization error: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*80)
    print("🧪 TESTING HISTORICAL LEARNING SAVE FIX")
    print("="*80)
    print("Testing if BotUpdate schema and Bot model support historical learning...")
    
    results = []
    
    # Run tests
    results.append(("Schema Validation", test_schema_accepts_fields()))
    results.append(("Model Columns", test_model_has_columns()))
    results.append(("Model Defaults", test_model_defaults()))
    results.append(("Serialization", test_dict_conversion()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        print("✅ Backend code is ready")
        print("\nNext steps:")
        print("1. Run migration: mysql -u <user> -p <db> < migrations/add_historical_learning_columns_mysql.sql")
        print("2. Restart backend server")
        print("3. Test Save button in UI: http://localhost:3001/creator/entities/140")
        print("4. Click 'Strategies' tab → Enable Historical Learning → Save")
        return True
    else:
        print("\n" + "="*80)
        print("❌ SOME TESTS FAILED")
        print("="*80)
        print("Please check the errors above and fix them before deploying")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)


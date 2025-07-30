#!/usr/bin/env python3
"""
Test Runner for Trade Bot Marketplace
Runs all test suites in organized manner
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_test_file(test_file_path, description):
    """Run a single test file and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {description}")
    print(f"📁 File: {test_file_path}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"✅ {description}: PASSED")
            return True
        else:
            print(f"❌ {description}: FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ {description}: ERROR - {e}")
        return False

def main():
    """Run all test suites"""
    print("🚀 Trade Bot Marketplace - Test Suite Runner")
    print("=" * 60)
    
    # Define test suites
    test_suites = [
        {
            "category": "API Tests",
            "tests": [
                ("tests/api/test_api_simple.py", "Basic API Implementation Tests"),
                ("tests/api/demo_api_functionality.py", "API Functionality Demo"),
                ("tests/api/final_test_summary.py", "Comprehensive API Test Summary")
            ]
        },
        {
            "category": "Bot Trading Tests",
            "tests": [
                ("tests/bot_trading/test_binance_bot.py", "Binance Bot Tests"),
                ("tests/bot_trading/test_futures_bot.py", "Futures Bot Tests")
            ]
        },
        {
            "category": "Marketplace Tests", 
            "tests": [
                ("tests/marketplace/test_marketplace_api.py", "Marketplace API Tests")
            ]
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    # Run each test suite
    for suite in test_suites:
        print(f"\n📋 {suite['category']}")
        print("-" * 40)
        
        for test_file, description in suite['tests']:
            test_path = project_root / test_file
            
            if test_path.exists():
                total_tests += 1
                if run_test_file(test_path, description):
                    passed_tests += 1
                else:
                    failed_tests.append(description)
            else:
                print(f"⚠️  Test file not found: {test_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests Run: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\nFailed Tests:")
        for test in failed_tests:
            print(f"  - {test}")
    
    # Overall result
    if passed_tests == total_tests and total_tests > 0:
        print(f"\n🎉 ALL TESTS PASSED! ({passed_tests}/{total_tests})")
        print("✅ System is ready for production!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed ({passed_tests}/{total_tests})")
        print("Please check and fix failing tests.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

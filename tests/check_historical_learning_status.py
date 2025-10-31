#!/usr/bin/env python3
"""
Diagnostic script to check Historical Learning status for a bot

Usage:
    python3 tests/check_historical_learning_status.py <bot_id> [subscription_id]
    
Examples:
    python3 tests/check_historical_learning_status.py 140
    python3 tests/check_historical_learning_status.py 140 809
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def connect_db():
    """Connect to database"""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '3306')),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'bot_marketplace'),
        cursorclass=pymysql.cursors.DictCursor
    )

def check_migration_status(cursor):
    """Check if historical learning columns exist"""
    print("\n" + "="*80)
    print("📋 STEP 1: Check Migration Status")
    print("="*80)
    
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'bots'
            AND COLUMN_NAME = 'historical_learning_enabled'
    """)
    result = cursor.fetchone()
    
    if result['count'] > 0:
        print("✅ Migration 061 columns exist in database")
        
        # Check all 4 columns
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_DEFAULT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'bots'
                AND COLUMN_NAME IN ('historical_learning_enabled', 'historical_transaction_limit', 
                                    'include_failed_trades', 'learning_mode')
            ORDER BY COLUMN_NAME
        """)
        columns = cursor.fetchall()
        print(f"\n   Found {len(columns)}/4 columns:")
        for col in columns:
            print(f"   • {col['COLUMN_NAME']} ({col['COLUMN_TYPE']}) = {col['COLUMN_DEFAULT']}")
        
        return True
    else:
        print("❌ Migration NOT run yet!")
        print("\n   Action needed:")
        print("   python3 migrations/versions/061_add_historical_learning_columns.py")
        return False

def check_bot_config(cursor, bot_id):
    """Check bot's historical learning configuration"""
    print("\n" + "="*80)
    print(f"📊 STEP 2: Check Bot {bot_id} Configuration")
    print("="*80)
    
    cursor.execute("""
        SELECT 
            id,
            name,
            bot_type,
            historical_learning_enabled,
            historical_transaction_limit,
            include_failed_trades,
            learning_mode,
            status
        FROM bots
        WHERE id = %s
    """, (bot_id,))
    
    bot = cursor.fetchone()
    
    if not bot:
        print(f"❌ Bot {bot_id} not found!")
        return None
    
    print(f"Bot Name: {bot['name']}")
    print(f"Bot Type: {bot['bot_type']}")
    print(f"Status: {bot['status']}")
    print(f"\nHistorical Learning Config:")
    print(f"  • Enabled: {bool(bot['historical_learning_enabled'])}")
    print(f"  • Transaction Limit: {bot['historical_transaction_limit']}")
    print(f"  • Include Failed Trades: {bool(bot['include_failed_trades'])}")
    print(f"  • Learning Mode: {bot['learning_mode']}")
    
    if not bot['historical_learning_enabled']:
        print("\n⚠️  Historical Learning is DISABLED!")
        print("\n   To enable:")
        print(f"   1. Go to: http://localhost:3001/creator/entities/{bot_id}")
        print("   2. Click 'Strategies' tab")
        print("   3. Enable 'Historical Learning'")
        print("   4. Click 'Save Configuration'")
        print("\n   Or via SQL:")
        print(f"   UPDATE bots SET historical_learning_enabled = TRUE WHERE id = {bot_id};")
    else:
        print("\n✅ Historical Learning is ENABLED")
    
    return bot

def check_transactions(cursor, bot_id, subscription_id=None):
    """Check available transactions for learning"""
    print("\n" + "="*80)
    print(f"📚 STEP 3: Check Available Transactions")
    print("="*80)
    
    # Get all subscriptions for this bot
    cursor.execute("""
        SELECT id, user_id, trading_pair, status, created_at
        FROM subscriptions
        WHERE bot_id = %s
        ORDER BY created_at DESC
        LIMIT 10
    """, (bot_id,))
    
    subscriptions = cursor.fetchall()
    print(f"\nFound {len(subscriptions)} subscriptions for bot {bot_id}")
    
    if subscription_id:
        print(f"\nFocusing on subscription {subscription_id}...")
        sub_filter = f"AND s.id = {subscription_id}"
    else:
        sub_filter = ""
    
    # Check transactions
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total_transactions,
            SUM(CASE WHEN t.exit_price IS NOT NULL AND t.status = 'CLOSED' THEN 1 ELSE 0 END) as closed_count,
            SUM(CASE WHEN t.status = 'OPEN' THEN 1 ELSE 0 END) as open_count,
            SUM(CASE WHEN t.status = 'FAILED' THEN 1 ELSE 0 END) as failed_count
        FROM transactions t
        JOIN subscriptions s ON t.subscription_id = s.id
        WHERE s.bot_id = %s {sub_filter}
    """, (bot_id,))
    
    stats = cursor.fetchone()
    
    print(f"\nTransaction Statistics:")
    print(f"  • Total Transactions: {stats['total_transactions']}")
    print(f"  • Closed (Available for Learning): {stats['closed_count']}")
    print(f"  • Open: {stats['open_count']}")
    print(f"  • Failed: {stats['failed_count']}")
    
    if stats['closed_count'] == 0:
        print("\n⚠️  NO CLOSED TRANSACTIONS found!")
        print("\n   Historical learning requires at least 1 CLOSED transaction")
        print("   (Transaction with exit_price IS NOT NULL and status = 'CLOSED')")
        return 0
    
    # Get sample closed transactions
    cursor.execute(f"""
        SELECT 
            t.id,
            t.subscription_id,
            t.side,
            t.symbol,
            t.entry_price,
            t.exit_price,
            t.pnl_percentage,
            t.status,
            t.exit_time
        FROM transactions t
        JOIN subscriptions s ON t.subscription_id = s.id
        WHERE s.bot_id = %s
            AND t.exit_price IS NOT NULL
            AND t.status = 'CLOSED'
            {sub_filter}
        ORDER BY t.exit_time DESC
        LIMIT 5
    """, (bot_id,))
    
    recent = cursor.fetchall()
    
    if recent:
        print(f"\n📋 Recent Closed Transactions (showing {len(recent)}):")
        for i, tx in enumerate(recent, 1):
            result = "WIN" if tx['pnl_percentage'] and tx['pnl_percentage'] > 0 else "LOSS"
            pnl = tx['pnl_percentage'] or 0
            print(f"   {i}. TX-{tx['id']} | {tx['side']} {tx['symbol']} | PnL: {pnl:+.2f}% | {result}")
        
        print("\n✅ Transactions available for learning!")
    
    return stats['closed_count']

def check_bot_loading(bot_id):
    """Check if bot can load historical learning config"""
    print("\n" + "="*80)
    print(f"🔧 STEP 4: Check Bot Loading")
    print("="*80)
    
    try:
        from core import models
        from core.database import SessionLocal
        
        db = SessionLocal()
        bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
        
        if not bot:
            print(f"❌ Bot {bot_id} not found in database")
            return False
        
        # Check if attributes exist
        has_enabled = hasattr(bot, 'historical_learning_enabled')
        has_limit = hasattr(bot, 'historical_transaction_limit')
        has_failed = hasattr(bot, 'include_failed_trades')
        has_mode = hasattr(bot, 'learning_mode')
        
        print("Bot Model Attributes:")
        print(f"  • historical_learning_enabled: {'✅' if has_enabled else '❌'}")
        print(f"  • historical_transaction_limit: {'✅' if has_limit else '❌'}")
        print(f"  • include_failed_trades: {'✅' if has_failed else '❌'}")
        print(f"  • learning_mode: {'✅' if has_mode else '❌'}")
        
        if has_enabled:
            print(f"\n  Values:")
            print(f"  • Enabled: {bot.historical_learning_enabled}")
            print(f"  • Limit: {bot.historical_transaction_limit}")
            print(f"  • Include Failed: {bot.include_failed_trades}")
            print(f"  • Mode: {bot.learning_mode}")
            
            print("\n✅ Bot can load historical learning config!")
        else:
            print("\n❌ Bot model missing historical learning attributes!")
            print("\n   Action needed:")
            print("   1. Ensure core/models.py has historical learning columns")
            print("   2. Restart backend to reload SQLAlchemy models")
        
        db.close()
        return has_enabled and has_limit and has_failed and has_mode
        
    except Exception as e:
        print(f"❌ Error loading bot: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tests/check_historical_learning_status.py <bot_id> [subscription_id]")
        print("\nExamples:")
        print("  python3 tests/check_historical_learning_status.py 140")
        print("  python3 tests/check_historical_learning_status.py 140 809")
        sys.exit(1)
    
    bot_id = int(sys.argv[1])
    subscription_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "🔍 HISTORICAL LEARNING DIAGNOSTIC TOOL" + " "*24 + "║")
    print("╚" + "="*78 + "╝")
    
    print(f"\n🎯 Checking Bot ID: {bot_id}")
    if subscription_id:
        print(f"   Subscription ID: {subscription_id}")
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Step 1: Check migration
        migration_ok = check_migration_status(cursor)
        
        if not migration_ok:
            print("\n" + "="*80)
            print("❌ DIAGNOSIS: Migration not run")
            print("="*80)
            print("\nRun migration first:")
            print("python3 migrations/versions/061_add_historical_learning_columns.py")
            return
        
        # Step 2: Check bot config
        bot = check_bot_config(cursor, bot_id)
        
        if not bot:
            return
        
        # Step 3: Check transactions
        tx_count = check_transactions(cursor, bot_id, subscription_id)
        
        # Step 4: Check bot loading
        can_load = check_bot_loading(bot_id)
        
        # Final diagnosis
        print("\n" + "="*80)
        print("📊 FINAL DIAGNOSIS")
        print("="*80)
        
        issues = []
        
        if not migration_ok:
            issues.append("Migration 061 not run")
        
        if not bot['historical_learning_enabled']:
            issues.append("Historical learning not enabled for bot")
        
        if tx_count == 0:
            issues.append("No closed transactions available")
        
        if not can_load:
            issues.append("Bot model cannot load historical learning attributes (restart backend needed)")
        
        if issues:
            print("\n❌ ISSUES FOUND:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
            
            print("\n🔧 ACTIONS TO FIX:")
            if "Migration 061 not run" in issues:
                print("   1. Run: python3 migrations/versions/061_add_historical_learning_columns.py")
            if "Bot model cannot load" in issues:
                print("   2. Restart backend: pkill -f uvicorn && uvicorn main:app --reload")
            if "Historical learning not enabled" in issues:
                print(f"   3. Enable in UI or SQL: UPDATE bots SET historical_learning_enabled=TRUE WHERE id={bot_id};")
            if "No closed transactions" in issues:
                print("   4. Wait for bot to complete at least 1 trade")
            
            print("\n   After fixes, re-run this diagnostic.")
        else:
            print("\n✅ ALL CHECKS PASSED!")
            print("\n🎉 Historical learning should work for this bot")
            print("\nNext execution should show:")
            print(f"   📚 Loaded N historical transactions for learning")
            print("   And LLM prompt will include:")
            print("   ╔═══════════════════════════════════════════════════╗")
            print("   ║ 🧠 HISTORICAL TRANSACTIONS                        ║")
            print("   ╚═══════════════════════════════════════════════════╝")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()


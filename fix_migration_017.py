#!/usr/bin/env python3
"""
Fix migration 017 conflict by marking it as completed
"""
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from core.database import DATABASE_URL

def main():
    print("=" * 80)
    print("🔧 FIXING MIGRATION 017 CONFLICT")
    print("=" * 80)
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if migration 017 is already tracked
            result = conn.execute(
                text("SELECT id FROM migration_history WHERE filename = :filename"),
                {"filename": "017_add_bot_risk_config.sql"}
            )
            existing = result.fetchone()
            
            if existing:
                print("\n✅ Migration 017 is already marked as completed")
                print(f"   ID: {existing[0]}")
            else:
                # Mark as completed
                conn.execute(
                    text("""
                        INSERT INTO migration_history (filename, applied_at)
                        VALUES (:filename, :applied_at)
                    """),
                    {
                        "filename": "017_add_bot_risk_config.sql",
                        "applied_at": datetime.now()
                    }
                )
                conn.commit()
                print("\n✅ Successfully marked migration 017 as completed")
            
            # Show recent migrations
            print("\n📋 Recent migrations:")
            result = conn.execute(
                text("""
                    SELECT filename, applied_at 
                    FROM migration_history 
                    ORDER BY applied_at DESC 
                    LIMIT 10
                """)
            )
            
            for row in result:
                print(f"   • {row[0]:40s} | {row[1]}")
            
            # Check for pending migrations
            print("\n🔍 Checking pending migrations...")
            import os
            migrations_dir = "migrations/versions"
            
            # Get all applied migrations
            result = conn.execute(
                text("SELECT filename FROM migration_history")
            )
            applied = {row[0] for row in result}
            
            # Get all migration files
            all_migrations = []
            if os.path.exists(migrations_dir):
                for filename in sorted(os.listdir(migrations_dir)):
                    if filename.endswith('.sql') and not filename.startswith('README'):
                        all_migrations.append(filename)
            
            pending = [m for m in all_migrations if m not in applied]
            
            if pending:
                print(f"\n📌 Found {len(pending)} pending migration(s):")
                for m in pending:
                    print(f"   • {m}")
                print("\n🚀 Run: python migrations/migration_runner.py")
            else:
                print("\n✅ All migrations are up to date!")
        
        print("\n" + "=" * 80)
        print("✅ DONE!")
        print("=" * 80)
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())


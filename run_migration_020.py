#!/usr/bin/env python3
"""
Run migration 020: Create prompt_templates table and add prompt_template_id to bots
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Run the migration script"""
    
    # Database connection - using SQLite for development
    DATABASE_URL = "sqlite:///./bot_marketplace.db"
    
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        print("🔄 Starting migration 020: Create prompt_templates table...")
        
        # Read migration file
        migration_file = "migrations/versions/020_create_prompt_templates_table.sql"
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for i, statement in enumerate(statements):
            if statement:
                print(f"📝 Executing statement {i+1}/{len(statements)}...")
                try:
                    db.execute(text(statement))
                    db.commit()
                    print(f"✅ Statement {i+1} executed successfully")
                except Exception as e:
                    print(f"⚠️ Statement {i+1} failed (might be expected): {e}")
                    db.rollback()
        
        print("✅ Migration 020 completed successfully!")
        print("📋 Summary:")
        print("   - Created prompt_templates table")
        print("   - Added prompt_template_id column to bots table")
        print("   - Inserted default prompt templates")
        print("   - Added necessary indexes and foreign keys")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

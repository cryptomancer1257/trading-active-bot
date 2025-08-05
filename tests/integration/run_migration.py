#!/usr/bin/env python3
"""
Run database migration for bot registration features
"""

from sqlalchemy import text
from core.database import engine

def run_migration():
    """Execute the migration SQL"""
    print("🔄 Running database migration...")
    
    try:
        with engine.connect() as connection:
            # Read migration file
            with open('../../scripts/migrate_bot_registration.sql', 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements):
                if statement:
                    try:
                        print(f"Executing statement {i+1}/{len(statements)}: {statement[:50]}...")
                        connection.execute(text(statement))
                        connection.commit()
                        print(f"✅ Statement {i+1} executed successfully")
                    except Exception as e:
                        if "Duplicate column name" in str(e) or "already exists" in str(e):
                            print(f"⚠️ Statement {i+1} skipped (already exists): {e}")
                        else:
                            print(f"❌ Error in statement {i+1}: {e}")
                            raise
        
        print("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    run_migration()

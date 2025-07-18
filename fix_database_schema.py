#!/usr/bin/env python3
"""
Script to fix database schema for ERROR status support
"""

import sys
import os
from sqlalchemy import text, inspect
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment
load_dotenv('.env')

from database import engine, SessionLocal
import models

def check_current_schema():
    """Check current database schema"""
    print("🔍 Checking current database schema...")
    
    inspector = inspect(engine)
    
    # Check if subscriptions table exists
    if 'subscriptions' not in inspector.get_table_names():
        print("❌ Subscriptions table does not exist")
        return False
    
    # Check columns in subscriptions table
    columns = inspector.get_columns('subscriptions')
    status_column = None
    
    for col in columns:
        if col['name'] == 'status':
            status_column = col
            break
    
    if not status_column:
        print("❌ Status column not found in subscriptions table")
        return False
    
    print(f"✅ Found status column: {status_column['type']}")
    return True

def fix_subscription_status_enum():
    """Fix the subscription status enum to include ERROR"""
    print("🔧 Fixing subscription status enum...")
    
    try:
        with engine.connect() as conn:
            # Check current enum values
            result = conn.execute(text("""
                SELECT COLUMN_TYPE 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'subscriptions' 
                AND COLUMN_NAME = 'status'
            """))
            
            current_type = result.fetchone()
            if current_type:
                print(f"Current enum type: {current_type[0]}")
                
                # Check if ERROR is already included
                if 'ERROR' in current_type[0]:
                    print("✅ ERROR status already exists in enum")
                    return True
                
                # Alter the enum to include ERROR
                print("Adding ERROR to enum...")
                conn.execute(text("""
                    ALTER TABLE subscriptions 
                    MODIFY COLUMN status ENUM('ACTIVE', 'PAUSED', 'CANCELLED', 'EXPIRED', 'ERROR') 
                    DEFAULT 'ACTIVE'
                """))
                conn.commit()
                print("✅ Successfully added ERROR to subscription status enum")
                return True
            else:
                print("❌ Could not determine current enum type")
                return False
                
    except Exception as e:
        print(f"❌ Error fixing enum: {e}")
        return False

def recreate_tables_if_needed():
    """Recreate tables if enum fix doesn't work"""
    print("🔄 Recreating tables with new schema...")
    
    try:
        # Drop and recreate all tables
        print("Dropping existing tables...")
        models.Base.metadata.drop_all(bind=engine)
        
        print("Creating tables with new schema...")
        models.Base.metadata.create_all(bind=engine)
        
        print("✅ Tables recreated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error recreating tables: {e}")
        return False

def verify_fix():
    """Verify that the fix worked"""
    print("✅ Verifying fix...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COLUMN_TYPE 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'subscriptions' 
                AND COLUMN_NAME = 'status'
            """))
            
            enum_type = result.fetchone()
            if enum_type and 'ERROR' in enum_type[0]:
                print("✅ ERROR status is now supported in database")
                return True
            else:
                print("❌ ERROR status still not supported")
                return False
                
    except Exception as e:
        print(f"❌ Error verifying fix: {e}")
        return False

def main():
    """Main function to fix database schema"""
    print("🗄️  Database Schema Fix for ERROR Status")
    print("=" * 50)
    
    # Check current schema
    if not check_current_schema():
        print("Creating database schema...")
        models.Base.metadata.create_all(bind=engine)
    
    # Try to fix enum first
    if fix_subscription_status_enum():
        if verify_fix():
            print("\n🎉 Database schema fixed successfully!")
            print("You can now restart Celery worker to apply changes")
            return
    
    # If enum fix failed, recreate tables
    print("\nEnum fix failed, trying table recreation...")
    choice = input("⚠️  This will delete all data. Continue? (y/N): ").lower()
    
    if choice == 'y':
        if recreate_tables_if_needed() and verify_fix():
            print("\n🎉 Database schema recreated successfully!")
            print("You can now restart Celery worker to apply changes")
        else:
            print("\n❌ Failed to fix database schema")
            print("Please check your database configuration")
    else:
        print("Operation cancelled")

if __name__ == "__main__":
    main() 
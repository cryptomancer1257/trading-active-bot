#!/usr/bin/env python3
"""
Auto Migration Runner for Trade Bot Marketplace
Runs all pending migrations automatically when container starts
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict
import pymysql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MigrationRunner:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'botuser'),
            'password': os.getenv('DB_PASSWORD', 'botpassword123'),
            'database': os.getenv('DB_NAME', 'bot_marketplace'),
            'charset': 'utf8mb4'
        }
        self.migrations_dir = Path(__file__).parent / 'versions'
        self.connection = None
    
    def wait_for_db(self, max_retries=30):
        """Wait for database to be ready"""
        logger.info("Waiting for database to be ready...")
        
        for attempt in range(max_retries):
            try:
                connection = pymysql.connect(**self.db_config)
                connection.close()
                logger.info("Database is ready!")
                return True
            except Exception as e:
                logger.info(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2)
        
        logger.error("Database failed to become ready")
        return False
    
    def connect_db(self):
        """Connect to database"""
        try:
            self.connection = pymysql.connect(**self.db_config)
            logger.info("Connected to database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def create_migration_table(self):
        """Create migration tracking table if not exists"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        version VARCHAR(255) NOT NULL UNIQUE,
                        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            self.connection.commit()
            logger.info("Migration tracking table ready")
            return True
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            return False
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
                result = cursor.fetchall()
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def get_pending_migrations(self) -> List[Dict]:
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        pending = []
        
        # Get all SQL files in migrations/versions directory
        if self.migrations_dir.exists():
            for file_path in sorted(self.migrations_dir.glob('*.sql')):
                version = file_path.stem
                if version not in applied:
                    pending.append({
                        'version': version,
                        'file_path': file_path
                    })
        
        return pending
    
    def apply_migration(self, migration: Dict) -> bool:
        """Apply a single migration"""
        try:
            logger.info(f"Applying migration: {migration['version']}")
            
            # Read SQL file
            with open(migration['file_path'], 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            with self.connection.cursor() as cursor:
                for statement in statements:
                    if statement:
                        cursor.execute(statement)
                
                # Record migration as applied
                cursor.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (migration['version'],)
                )
            
            self.connection.commit()
            logger.info(f"✅ Migration {migration['version']} applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply migration {migration['version']}: {e}")
            self.connection.rollback()
            return False
    
    def run_migrations(self):
        """Run all pending migrations"""
        logger.info("🚀 Starting migration runner...")
        
        # Wait for database
        if not self.wait_for_db():
            logger.error("❌ Database not available, exiting")
            sys.exit(1)
        
        # Connect to database
        if not self.connect_db():
            logger.error("❌ Failed to connect to database, exiting")
            sys.exit(1)
        
        try:
            # Create migration tracking table
            if not self.create_migration_table():
                logger.error("❌ Failed to create migration table, exiting")
                sys.exit(1)
            
            # Get pending migrations
            pending = self.get_pending_migrations()
            
            if not pending:
                logger.info("✅ No pending migrations found")
                return
            
            logger.info(f"📋 Found {len(pending)} pending migrations")
            
            # Apply each migration
            success_count = 0
            for migration in pending:
                if self.apply_migration(migration):
                    success_count += 1
                else:
                    logger.error(f"❌ Migration failed, stopping at: {migration['version']}")
                    sys.exit(1)
            
            logger.info(f"🎉 Successfully applied {success_count} migrations!")
            
        except Exception as e:
            logger.error(f"❌ Migration runner failed: {e}")
            sys.exit(1)
        
        finally:
            if self.connection:
                self.connection.close()

def main():
    """Main entry point"""
    runner = MigrationRunner()
    runner.run_migrations()

if __name__ == "__main__":
    main()

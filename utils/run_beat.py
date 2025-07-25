#!/usr/bin/env python3
"""
Celery beat scheduler runner
"""
import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run Celery beat scheduler"""
    from utils.celery_app import app
        
    # Start beat scheduler using app.start()
        app.start([
            'beat',
            '--loglevel=info',
        '--scheduler=celery.beat.PersistentScheduler'
        ])

if __name__ == '__main__':
    main() 
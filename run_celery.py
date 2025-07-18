#!/usr/bin/env python3
"""
Celery worker runner script
"""
import os
import sys
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run Celery worker"""
    from celery_app import app
    
    # Start worker
    app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--queues=default,bot_execution,maintenance,notifications',
        '--pool=threads'
    ])

if __name__ == '__main__':
    main() 
#!/usr/bin/env python3
"""
Celery beat scheduler for S3 Production Mode
Trading Bot Marketplace
"""
import os
import sys
import logging
import tempfile
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_s3_config():
    """Check S3 configuration"""
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_S3_BUCKET_NAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing S3 configuration: {', '.join(missing_vars)}")
        return False
    
    dev_mode = os.getenv('DEVELOPMENT_MODE', 'true').lower()
    if dev_mode != 'false':
        logger.warning("⚠️  DEVELOPMENT_MODE is not set to 'false'")
        logger.warning("    Set DEVELOPMENT_MODE=false in .env for S3 mode")
    
    logger.info("✅ S3 configuration check passed")
    return True

def main():
    """Run Celery beat for S3 mode"""
    logger.info("🗄️  Celery Beat - S3 Production Mode")
    logger.info("=" * 50)
    
    # Check S3 configuration
    if not check_s3_config():
        logger.error("Please configure S3 in .env file")
        sys.exit(1)
    
    # Check Redis
    try:
        import redis
        from dotenv import load_dotenv
        
        load_dotenv('.env')
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.Redis.from_url(redis_url)
        r.ping()
        logger.info("✅ Redis connection OK")
    except Exception as e:
        logger.error(f"❌ Redis error: {e}")
        sys.exit(1)
    
    try:
        # Import Celery app
        from celery_app import app
        
        # Clean up files
        temp_dir = tempfile.gettempdir()
        schedule_file = os.path.join(temp_dir, 'celerybeat-schedule-s3')
        pidfile = os.path.join(temp_dir, 'celerybeat-s3.pid')
        
        for f in [schedule_file, pidfile]:
            if os.path.exists(f):
                os.remove(f)
                logger.info(f"🗑️  Removed: {f}")
        
        logger.info(f"📋 Schedule: {schedule_file}")
        logger.info(f"🆔 PID: {pidfile}")
        
        # Show scheduled tasks
        logger.info("\n⏰ S3 Mode Scheduled Tasks:")
        for name, config in app.conf.beat_schedule.items():
            task = config.get('task', 'Unknown')
            schedule = config.get('schedule', 'Unknown')
            logger.info(f"   ✅ {name}: {task} (every {schedule}s)")
        
        logger.info("\n🚀 Starting S3 Celery Beat...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 50)
        
        # Start beat
        app.start([
            'beat',
            '--loglevel=info',
            f'--schedule={schedule_file}',
            f'--pidfile={pidfile}',
            '--max-interval=30'
        ])
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  S3 Beat stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
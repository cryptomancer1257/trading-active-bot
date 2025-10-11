import os
import sys
from celery import Celery
from kombu import Queue

# Add parent directory to path to import from core and services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env')

# Create Celery app
app = Celery('bot_marketplace')

# Configure broker and backend
app.conf.broker_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app.conf.result_backend = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Task configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
    imports=[
        'core.tasks',  # Updated import path
    ],
    task_routes={
        'core.tasks.run_bot_logic': {'queue': 'bot_execution'},
        'core.tasks.run_bot_rpa_logic': {'queue': 'bot_execution'},
        'core.tasks.run_bot_signal_logic': {'queue': 'bot_execution_signal'},
        'core.tasks.run_futures_bot_trading': {'queue': 'futures_trading'},
        'core.tasks.schedule_futures_bot_trading': {'queue': 'futures_trading'},
        'core.tasks.cleanup_old_logs': {'queue': 'maintenance'},
        'core.tasks.send_email_notification': {'queue': 'notifications'},
        'core.tasks.send_telegram_notification': {'queue': 'notifications'},
        'core.tasks.send_telegram_beauty_notification': {'queue': 'notifications'},
        'core.tasks.send_discord_notification': {'queue': 'notifications'},
        'core.tasks.monitor_open_positions_task': {'queue': 'monitoring'},
        'core.tasks.sync_open_positions_realtime': {'queue': 'monitoring'},
        'core.tasks.update_bot_performance_metrics': {'queue': 'analytics'},
        'core.tasks.update_prompt_performance_metrics': {'queue': 'analytics'},
        'core.tasks.update_risk_management_performance': {'queue': 'analytics'},
        'core.tasks.test_task': {'queue': 'default'},
    },
    task_default_queue='default',
    task_queues=(
        Queue('default'),
        Queue('bot_execution'),
        Queue('futures_trading'),
        Queue('maintenance'),
        Queue('notifications'),
        Queue('bot_execution_signal'),
        Queue('monitoring'),
        Queue('analytics'),
    ),
    beat_schedule={
        'cleanup-old-logs': {
            'task': 'core.tasks.cleanup_old_logs',
            'schedule': 300.0,  # Run every 5 minutes
        },
        'schedule-active-bots': {
            'task': 'core.tasks.schedule_active_bots',
            'schedule': 60.0,  # Run every 1 minute to check for bot executions
        },
        'monitor-open-positions': {
            'task': 'core.tasks.monitor_open_positions_task',
            'schedule': 180.0,  # Run every 3 minutes to check TP/SL and update P&L
        },
        'sync-open-positions-realtime': {
            'task': 'core.tasks.sync_open_positions_realtime',
            'schedule': 10.0,  # Run every 10 seconds for real-time position sync
        },
    },
)

# Auto-discover tasks
app.autodiscover_tasks(['core.tasks'])

if __name__ == '__main__':
    app.start() 
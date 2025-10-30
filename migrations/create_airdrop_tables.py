#!/usr/bin/env python3
"""
Migration script to add airdrop system tables to the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.database import get_database_url
from core.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_airdrop_tables():
    """Create airdrop system tables"""
    
    # Get database URL
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    try:
        # Create all tables
        logger.info("Creating airdrop system tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Airdrop tables created successfully!")
        
        # Insert default airdrop tasks
        insert_default_tasks(engine)
        
        # Insert default airdrop configuration
        insert_default_config(engine)
        
    except Exception as e:
        logger.error(f"❌ Error creating airdrop tables: {e}")
        raise
    finally:
        engine.dispose()

def insert_default_tasks(engine):
    """Insert default airdrop tasks"""
    
    default_tasks = [
        # Platform Usage Tasks (40% - 20M BOT)
        {
            'task_id': 'create_bot',
            'task_name': 'Create Trading Bot',
            'task_description': 'Create your first trading bot on the platform',
            'category': 'PLATFORM_USAGE',
            'points': 100,
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'trigger': 'bot_creation'}
        },
        {
            'task_id': 'first_trade',
            'task_name': 'Complete First Trade',
            'task_description': 'Execute your first successful trade',
            'category': 'PLATFORM_USAGE',
            'points': 200,
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'trigger': 'trade_execution'}
        },
        {
            'task_id': 'trading_volume',
            'task_name': 'Trading Volume Milestones',
            'task_description': 'Reach trading volume milestones ($100, $1K, $10K)',
            'category': 'PLATFORM_USAGE',
            'points': 50,  # Base points, can be upgraded based on volume
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'milestones': [100, 1000, 10000]}
        },
        {
            'task_id': 'profitable_bot',
            'task_name': 'Profitable Bot Bonus',
            'task_description': 'Create a bot that generates profit',
            'category': 'PLATFORM_USAGE',
            'points': 500,
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'trigger': 'pnl_calculation'}
        },
        {
            'task_id': 'daily_streak',
            'task_name': 'Daily Activity Streak',
            'task_description': 'Maintain daily activity on the platform',
            'category': 'PLATFORM_USAGE',
            'points': 10,  # Per day
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'trigger': 'activity_tracking'}
        },
        
        # Community Engagement Tasks (30% - 15M BOT)
        {
            'task_id': 'discord_member',
            'task_name': 'Discord Community Member',
            'task_description': 'Join our Discord server and get verified',
            'category': 'COMMUNITY_ENGAGEMENT',
            'points': 50,
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'oauth_required': True}
        },
        {
            'task_id': 'telegram_member',
            'task_name': 'Telegram Channel Member',
            'task_description': 'Join our Telegram channel',
            'category': 'COMMUNITY_ENGAGEMENT',
            'points': 30,
            'max_claims': None,
            'verification_method': 'SEMI_AUTO',
            'verification_data': {'bot_verification': True}
        },
        {
            'task_id': 'twitter_engagement',
            'task_name': 'Twitter Follow & Retweet',
            'task_description': 'Follow us on Twitter and retweet our announcement',
            'category': 'COMMUNITY_ENGAGEMENT',
            'points': 20,
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'oauth_required': True}
        },
        {
            'task_id': 'content_creation',
            'task_name': 'Content Creation',
            'task_description': 'Create educational content about trading bots',
            'category': 'COMMUNITY_ENGAGEMENT',
            'points': 100,  # Base points, varies by content type
            'max_claims': None,
            'verification_method': 'MANUAL',
            'verification_data': {'admin_review': True}
        },
        {
            'task_id': 'referral_program',
            'task_name': 'Referral Program',
            'task_description': 'Refer new users to the platform',
            'category': 'COMMUNITY_ENGAGEMENT',
            'points': 50,  # Per referral
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'tracking': True}
        },
        
        # SNS Participation Tasks (20% - 10M BOT)
        {
            'task_id': 'sns_participation',
            'task_name': 'SNS Sale Participation',
            'task_description': 'Participate in the SNS token sale',
            'category': 'SNS_PARTICIPATION',
            'points': 100,  # Base points, bonus based on ICP committed
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'blockchain_query': True}
        },
        {
            'task_id': 'governance_votes',
            'task_name': 'Governance Participation',
            'task_description': 'Vote on SNS governance proposals',
            'category': 'SNS_PARTICIPATION',
            'points': 50,  # Per vote
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'blockchain_query': True}
        },
        
        # Developer Contributions Tasks (10% - 5M BOT)
        {
            'task_id': 'bot_template',
            'task_name': 'Bot Template Submission',
            'task_description': 'Submit a high-quality bot template',
            'category': 'DEVELOPER_CONTRIBUTIONS',
            'points': 1000,
            'max_claims': None,
            'verification_method': 'MANUAL',
            'verification_data': {'github_integration': True, 'admin_review': True}
        },
        {
            'task_id': 'merged_pr',
            'task_name': 'Merged Pull Request',
            'task_description': 'Contribute code that gets merged',
            'category': 'DEVELOPER_CONTRIBUTIONS',
            'points': 500,
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'github_webhook': True}
        },
        {
            'task_id': 'bug_report',
            'task_name': 'Bug Report',
            'task_description': 'Report confirmed bugs in the platform',
            'category': 'DEVELOPER_CONTRIBUTIONS',
            'points': 100,
            'max_claims': None,
            'verification_method': 'AUTO',
            'verification_data': {'github_webhook': True}
        }
    ]
    
    with engine.connect() as conn:
        for task in default_tasks:
            try:
                # Check if task already exists
                result = conn.execute(text(
                    "SELECT id FROM airdrop_tasks WHERE task_id = :task_id"
                ), {'task_id': task['task_id']})
                
                if result.fetchone():
                    logger.info(f"Task {task['task_id']} already exists, skipping...")
                    continue
                
                # Insert task
                conn.execute(text("""
                    INSERT INTO airdrop_tasks 
                    (task_id, task_name, task_description, category, points, max_claims, 
                     is_active, verification_method, verification_data)
                    VALUES 
                    (:task_id, :task_name, :task_description, :category, :points, :max_claims,
                     :is_active, :verification_method, :verification_data)
                """), {
                    'task_id': task['task_id'],
                    'task_name': task['task_name'],
                    'task_description': task['task_description'],
                    'category': task['category'],
                    'points': task['points'],
                    'max_claims': task['max_claims'],
                    'is_active': True,
                    'verification_method': task['verification_method'],
                    'verification_data': str(task['verification_data']).replace("'", '"')
                })
                
                logger.info(f"✅ Inserted task: {task['task_id']}")
                
            except Exception as e:
                logger.error(f"❌ Error inserting task {task['task_id']}: {e}")
        
        conn.commit()

def insert_default_config(engine):
    """Insert default airdrop configuration"""
    
    default_configs = [
        {
            'config_key': 'AIRDROP_START_DATE',
            'config_value': '2025-01-01T00:00:00',
            'config_type': 'STRING',
            'description': 'Start date for airdrop campaign'
        },
        {
            'config_key': 'AIRDROP_END_DATE',
            'config_value': '2025-12-31T23:59:59',
            'config_type': 'STRING',
            'description': 'End date for airdrop campaign'
        },
        {
            'config_key': 'POINTS_TO_TOKENS_RATIO',
            'config_value': '10',
            'config_type': 'INTEGER',
            'description': 'Points to tokens conversion ratio (1 point = 10 BOT tokens)'
        },
        {
            'config_key': 'MAX_CLAIMS_PER_IP',
            'config_value': '5',
            'config_type': 'INTEGER',
            'description': 'Maximum claims allowed per IP address'
        },
        {
            'config_key': 'KYC_THRESHOLD',
            'config_value': '1000000000000',
            'config_type': 'INTEGER',
            'description': 'KYC threshold in e8s (10,000 BOT tokens)'
        },
        {
            'config_key': 'DISCORD_SERVER_ID',
            'config_value': '',
            'config_type': 'STRING',
            'description': 'Discord server ID for verification'
        },
        {
            'config_key': 'DISCORD_BOT_TOKEN',
            'config_value': '',
            'config_type': 'STRING',
            'description': 'Discord bot token for API access'
        },
        {
            'config_key': 'TELEGRAM_BOT_TOKEN',
            'config_value': '',
            'config_type': 'STRING',
            'description': 'Telegram bot token for verification'
        },
        {
            'config_key': 'TELEGRAM_CHANNEL_ID',
            'config_value': '',
            'config_type': 'STRING',
            'description': 'Telegram channel ID for membership verification'
        },
        {
            'config_key': 'TWITTER_BEARER_TOKEN',
            'config_value': '',
            'config_type': 'STRING',
            'description': 'Twitter API bearer token'
        },
        {
            'config_key': 'OUR_TWITTER_ACCOUNT_ID',
            'config_value': '',
            'config_type': 'STRING',
            'description': 'Our Twitter account ID for follow verification'
        },
        {
            'config_key': 'AIRDROP_ANNOUNCEMENT_TWEET_ID',
            'config_value': '',
            'config_type': 'STRING',
            'description': 'Tweet ID for retweet verification'
        },
        {
            'config_key': 'SNS_SWAP_CANISTER_ID',
            'config_value': '',
            'config_type': 'STRING',
            'description': 'SNS swap canister ID for participation verification'
        },
        {
            'config_key': 'SNS_GOVERNANCE_CANISTER_ID',
            'config_value': '',
            'config_type': 'STRING',
            'description': 'SNS governance canister ID for vote verification'
        },
        {
            'config_key': 'IC_MAINNET_URL',
            'config_value': 'https://ic0.app',
            'config_type': 'STRING',
            'description': 'Internet Computer mainnet URL'
        },
        {
            'config_key': 'GITHUB_TOKEN',
            'config_value': '',
            'config_type': 'STRING',
            'description': 'GitHub token for API access'
        }
    ]
    
    with engine.connect() as conn:
        for config in default_configs:
            try:
                # Check if config already exists
                result = conn.execute(text(
                    "SELECT id FROM airdrop_config WHERE config_key = :config_key"
                ), {'config_key': config['config_key']})
                
                if result.fetchone():
                    logger.info(f"Config {config['config_key']} already exists, skipping...")
                    continue
                
                # Insert config
                conn.execute(text("""
                    INSERT INTO airdrop_config 
                    (config_key, config_value, config_type, description, is_active)
                    VALUES 
                    (:config_key, :config_value, :config_type, :description, :is_active)
                """), {
                    'config_key': config['config_key'],
                    'config_value': config['config_value'],
                    'config_type': config['config_type'],
                    'description': config['description'],
                    'is_active': True
                })
                
                logger.info(f"✅ Inserted config: {config['config_key']}")
                
            except Exception as e:
                logger.error(f"❌ Error inserting config {config['config_key']}: {e}")
        
        conn.commit()

if __name__ == "__main__":
    create_airdrop_tables()

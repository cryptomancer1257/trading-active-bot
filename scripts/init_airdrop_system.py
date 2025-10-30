#!/usr/bin/env python3
"""
Initialize airdrop system - run migrations and setup
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrations.create_airdrop_tables import create_airdrop_tables
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main initialization function"""
    
    logger.info("🚀 Initializing BOT Token Airdrop System...")
    
    try:
        # Create airdrop tables and insert default data
        create_airdrop_tables()
        
        logger.info("✅ Airdrop system initialization completed successfully!")
        logger.info("")
        logger.info("📋 Next steps:")
        logger.info("1. Configure Discord, Telegram, Twitter API credentials")
        logger.info("2. Set up SNS canister IDs for blockchain verification")
        logger.info("3. Start the Telegram verification bot")
        logger.info("4. Launch the airdrop campaign!")
        logger.info("")
        logger.info("🔧 Configuration keys to set:")
        logger.info("- DISCORD_SERVER_ID")
        logger.info("- DISCORD_BOT_TOKEN")
        logger.info("- TELEGRAM_BOT_TOKEN")
        logger.info("- TELEGRAM_CHANNEL_ID")
        logger.info("- TWITTER_BEARER_TOKEN")
        logger.info("- OUR_TWITTER_ACCOUNT_ID")
        logger.info("- AIRDROP_ANNOUNCEMENT_TWEET_ID")
        logger.info("- SNS_SWAP_CANISTER_ID")
        logger.info("- SNS_GOVERNANCE_CANISTER_ID")
        logger.info("- GITHUB_TOKEN")
        
    except Exception as e:
        logger.error(f"❌ Error initializing airdrop system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

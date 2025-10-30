#!/usr/bin/env python3
"""
Seed airdrop tasks into database
"""
from core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check if tasks already exist
existing = db.execute(text("SELECT COUNT(*) FROM airdrop_tasks")).fetchone()[0]
if existing > 0:
    print(f"✅ Tasks already exist ({existing} tasks)")
    db.close()
    exit(0)

# Airdrop tasks to insert
tasks = [
    # Platform Usage (20% - 10M BOT)
    {
        'name': 'Create Your First Bot',
        'description': 'Deploy your first trading bot on the platform',
        'category': 'platform_usage',
        'points': 500,
        'verification_method': 'API_CHECK',
        'is_active': True
    },
    {
        'name': 'Execute First Trade',
        'description': 'Make your first successful trade with your bot',
        'category': 'platform_usage',
        'points': 1000,
        'verification_method': 'TRANSACTION_CHECK',
        'is_active': True
    },
    {
        'name': 'Achieve $1,000 Trading Volume',
        'description': 'Reach $1,000 in total trading volume across all your bots',
        'category': 'platform_usage',
        'points': 2000,
        'verification_method': 'VOLUME_CHECK',
        'is_active': True
    },
    {
        'name': 'Run Bot for 7 Days',
        'description': 'Keep at least one bot active for 7 consecutive days',
        'category': 'platform_usage',
        'points': 1500,
        'verification_method': 'TIME_CHECK',
        'is_active': True
    },
    {
        'name': 'Achieve Profitable Week',
        'description': 'End a week with positive profit across all your bots',
        'category': 'platform_usage',
        'points': 3000,
        'verification_method': 'PROFIT_CHECK',
        'is_active': True
    },
    
    # Community Engagement (15% - 7.5M BOT)
    {
        'name': 'Join Discord Server',
        'description': 'Join our official Discord community and verify your membership',
        'category': 'community',
        'points': 300,
        'verification_method': 'DISCORD_CHECK',
        'is_active': True
    },
    {
        'name': 'Join Telegram Group',
        'description': 'Join our Telegram group and verify your membership',
        'category': 'community',
        'points': 300,
        'verification_method': 'TELEGRAM_CHECK',
        'is_active': True
    },
    {
        'name': 'Refer 3 Friends',
        'description': 'Invite 3 friends who complete at least one task',
        'category': 'community',
        'points': 2000,
        'verification_method': 'REFERRAL_CHECK',
        'is_active': True
    },
    {
        'name': 'Refer 10 Friends',
        'description': 'Invite 10 friends who complete at least one task',
        'category': 'community',
        'points': 5000,
        'verification_method': 'REFERRAL_CHECK',
        'is_active': True
    },
    {
        'name': 'Create Educational Content',
        'description': 'Write a guide, tutorial, or review about the platform (min 500 words)',
        'category': 'community',
        'points': 3000,
        'verification_method': 'MANUAL_REVIEW',
        'is_active': True
    },
    
    # SNS Participation (10% - 5M BOT)
    {
        'name': 'Vote on SNS Proposal',
        'description': 'Participate in at least one SNS governance proposal vote',
        'category': 'sns',
        'points': 2000,
        'verification_method': 'SNS_VOTE_CHECK',
        'is_active': False  # Will activate when SNS launches
    },
    {
        'name': 'Create SNS Proposal',
        'description': 'Submit a governance proposal to the SNS DAO',
        'category': 'sns',
        'points': 5000,
        'verification_method': 'SNS_PROPOSAL_CHECK',
        'is_active': False
    },
    {
        'name': 'Stake BOT Tokens',
        'description': 'Stake at least 1,000 BOT tokens in the governance neuron',
        'category': 'sns',
        'points': 3000,
        'verification_method': 'STAKING_CHECK',
        'is_active': False
    },
    
    # Trader Contributions (10% - 5M BOT)
    {
        'name': 'Submit Strategy Template',
        'description': 'Create and submit a trading strategy template with verified performance',
        'category': 'trader_contributions',
        'points': 4000,
        'verification_method': 'STRATEGY_SUBMISSION_CHECK',
        'is_active': True
    },
    {
        'name': 'Get Strategy Adopted',
        'description': 'Have your strategy template adopted by 5 other traders',
        'category': 'trader_contributions',
        'points': 6000,
        'verification_method': 'STRATEGY_ADOPTION_CHECK',
        'is_active': True
    },
    {
        'name': 'Top 10 Monthly Performance',
        'description': 'Achieve top 10 rank in monthly performance leaderboard',
        'category': 'trader_contributions',
        'points': 8000,
        'verification_method': 'LEADERBOARD_CHECK',
        'is_active': True
    },
    {
        'name': 'Top 3 Monthly Performance',
        'description': 'Achieve top 3 rank in monthly performance leaderboard',
        'category': 'trader_contributions',
        'points': 15000,
        'verification_method': 'LEADERBOARD_CHECK',
        'is_active': True
    },
]

# Insert tasks
try:
    for task in tasks:
        db.execute(
            text("""
                INSERT INTO airdrop_tasks 
                (name, description, category, points, verification_method, is_active, created_at)
                VALUES 
                (:name, :description, :category, :points, :verification_method, :is_active, NOW())
            """),
            task
        )
    
    db.commit()
    print(f"✅ Successfully inserted {len(tasks)} airdrop tasks")
    
    # Display summary
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 AIRDROP TASKS SUMMARY")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    categories = {}
    for task in tasks:
        cat = task['category'].replace('_', ' ').title()
        if cat not in categories:
            categories[cat] = {'count': 0, 'points': 0, 'active': 0}
        categories[cat]['count'] += 1
        categories[cat]['points'] += task['points']
        if task['is_active']:
            categories[cat]['active'] += 1
    
    for cat, stats in categories.items():
        print(f"\n{cat}:")
        print(f"  • Total Tasks: {stats['count']}")
        print(f"  • Active Tasks: {stats['active']}")
        print(f"  • Total Points: {stats['points']:,}")
    
    total_tasks = len(tasks)
    active_tasks = sum(1 for t in tasks if t['is_active'])
    total_points = sum(t['points'] for t in tasks)
    
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"TOTAL: {total_tasks} tasks | {active_tasks} active | {total_points:,} points")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    print("\n✅ Database seeded successfully!")
    print("🌐 Refresh http://localhost:3002/tasks to see the tasks")
    
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
finally:
    db.close()


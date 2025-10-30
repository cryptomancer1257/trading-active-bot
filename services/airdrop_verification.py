"""
Airdrop verification services for different task types
"""

import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.models import (
    Bot, Transaction, UserActivity, AirdropClaim, AirdropConfig,
    TelegramVerification, ReferralCode, AirdropReferral
)

logger = logging.getLogger(__name__)

class VerificationService:
    """Base verification service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_config(self, key: str, default_value: Any = None) -> Any:
        """Get airdrop configuration value"""
        config = self.db.query(AirdropConfig).filter(
            AirdropConfig.config_key == key,
            AirdropConfig.is_active == True
        ).first()
        
        if not config:
            return default_value
        
        if config.config_type == 'INTEGER':
            return int(config.config_value)
        elif config.config_type == 'BOOLEAN':
            return config.config_value.lower() == 'true'
        elif config.config_type == 'JSON':
            return json.loads(config.config_value)
        else:
            return config.config_value


class PlatformUsageVerification(VerificationService):
    """Verification service for platform usage tasks"""
    
    def verify_bot_creation(self, principal: str) -> Dict[str, Any]:
        """Verify user has created a trading bot"""
        
        # Get airdrop start date
        start_date_str = self.get_config('AIRDROP_START_DATE', '2025-01-01T00:00:00')
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        
        # Query bots created by user since airdrop start
        bot_count = self.db.query(Bot).filter(
            Bot.created_at >= start_date
        ).join(
            # Join with user principals to find bots by principal
            # This assumes we have a way to link principals to users
        ).count()
        
        return {
            'verified': bot_count > 0,
            'points': 100 if bot_count > 0 else 0,
            'proof': f'{bot_count} bot(s) created since {start_date_str}',
            'bot_count': bot_count
        }
    
    def verify_first_trade(self, principal: str) -> Dict[str, Any]:
        """Verify user has completed their first trade"""
        
        start_date_str = self.get_config('AIRDROP_START_DATE', '2025-01-01T00:00:00')
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        
        # Query first completed trade
        trade = self.db.query(Transaction).filter(
            Transaction.user_principal_id == principal,
            Transaction.status == 'EXECUTED',
            Transaction.created_at >= start_date
        ).first()
        
        if trade:
            return {
                'verified': True,
                'points': 200,
                'proof': f'First trade: {trade.symbol} at {trade.entry_price}',
                'trade_id': trade.id,
                'symbol': trade.symbol,
                'entry_price': float(trade.entry_price)
            }
        
        return {
            'verified': False,
            'points': 0,
            'proof': 'No completed trades found'
        }
    
    def verify_trading_volume(self, principal: str) -> Dict[str, Any]:
        """Verify user's trading volume milestones"""
        
        start_date_str = self.get_config('AIRDROP_START_DATE', '2025-01-01T00:00:00')
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        
        # Calculate total trading volume
        total_volume = self.db.query(
            func.sum(Transaction.quantity * Transaction.entry_price)
        ).filter(
            Transaction.user_principal_id == principal,
            Transaction.status == 'EXECUTED',
            Transaction.created_at >= start_date
        ).scalar() or 0
        
        # Tiered points based on volume
        points = 0
        milestone_reached = None
        
        if total_volume >= 10000:
            points = 1000
            milestone_reached = '$10,000'
        elif total_volume >= 1000:
            points = 200
            milestone_reached = '$1,000'
        elif total_volume >= 100:
            points = 50
            milestone_reached = '$100'
        
        return {
            'verified': points > 0,
            'points': points,
            'proof': f'Trading volume: ${total_volume:,.2f}',
            'total_volume': total_volume,
            'milestone_reached': milestone_reached,
            'next_milestone': self._get_next_milestone(total_volume)
        }
    
    def verify_profitable_bot(self, principal: str) -> Dict[str, Any]:
        """Verify user has profitable bots"""
        
        # Get user's bots (assuming we can link principal to user)
        # This is a simplified version - in practice, you'd need proper user-principal mapping
        
        profitable_bots = []
        total_profit = 0
        
        # Query transactions with positive P&L
        profitable_transactions = self.db.query(Transaction).filter(
            Transaction.user_principal_id == principal,
            Transaction.status == 'EXECUTED',
            Transaction.realized_pnl > 0
        ).all()
        
        # Group by bot and calculate total profit per bot
        bot_profits = {}
        for tx in profitable_transactions:
            if tx.bot_id:
                if tx.bot_id not in bot_profits:
                    bot_profits[tx.bot_id] = 0
                bot_profits[tx.bot_id] += tx.realized_pnl or 0
        
        # Count profitable bots
        profitable_bot_count = len(bot_profits)
        total_profit = sum(bot_profits.values())
        
        if profitable_bot_count > 0:
            points = 500 * profitable_bot_count
            return {
                'verified': True,
                'points': points,
                'proof': f'{profitable_bot_count} profitable bot(s)',
                'profitable_bot_count': profitable_bot_count,
                'total_profit': total_profit,
                'bot_profits': bot_profits
            }
        
        return {
            'verified': False,
            'points': 0,
            'proof': 'No profitable bots found'
        }
    
    def verify_daily_streak(self, principal: str) -> Dict[str, Any]:
        """Verify user's daily activity streak"""
        
        start_date_str = self.get_config('AIRDROP_START_DATE', '2025-01-01T00:00:00')
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        
        # Get user activities
        activities = self.db.query(UserActivity).filter(
            UserActivity.principal_id == principal,
            UserActivity.activity_date >= start_date
        ).order_by(UserActivity.activity_date.desc()).all()
        
        # Calculate consecutive days
        streak_days = self._calculate_consecutive_days(activities)
        points = streak_days * 10
        
        return {
            'verified': streak_days > 0,
            'points': points,
            'proof': f'{streak_days} day streak',
            'streak_days': streak_days,
            'last_active': activities[0].activity_date if activities else None
        }
    
    def _get_next_milestone(self, current_volume: float) -> Dict[str, Any]:
        """Get next trading volume milestone"""
        milestones = [
            {'volume': 100, 'points': 50},
            {'volume': 1000, 'points': 200},
            {'volume': 10000, 'points': 1000}
        ]
        
        for milestone in milestones:
            if current_volume < milestone['volume']:
                return {
                    'next_volume': milestone['volume'],
                    'next_points': milestone['points'],
                    'remaining_volume': milestone['volume'] - current_volume
                }
        
        return {'next_volume': None, 'next_points': 0, 'remaining_volume': 0}
    
    def _calculate_consecutive_days(self, activities: List[UserActivity]) -> int:
        """Calculate consecutive days of activity"""
        if not activities:
            return 0
        
        # Sort by date descending
        sorted_activities = sorted(activities, key=lambda x: x.activity_date, reverse=True)
        
        consecutive_days = 0
        current_date = datetime.now().date()
        
        for activity in sorted_activities:
            activity_date = activity.activity_date.date()
            if activity_date == current_date:
                consecutive_days += 1
                current_date = current_date - timedelta(days=1)
            else:
                break
        
        return consecutive_days


class CommunityEngagementVerification(VerificationService):
    """Verification service for community engagement tasks"""
    
    def verify_discord_membership(self, discord_id: str) -> Dict[str, Any]:
        """Verify Discord server membership"""
        
        discord_server_id = self.get_config('DISCORD_SERVER_ID')
        discord_bot_token = self.get_config('DISCORD_BOT_TOKEN')
        
        if not discord_server_id or not discord_bot_token:
            logger.warning("Discord configuration not set")
            return {
                'verified': False,
                'points': 0,
                'error': 'Discord verification not configured'
            }
        
        try:
            # Check if user is member of Discord server
            headers = {'Authorization': f'Bot {discord_bot_token}'}
            url = f'https://discord.com/api/guilds/{discord_server_id}/members/{discord_id}'
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                member_data = response.json()
                return {
                    'verified': True,
                    'points': 50,
                    'proof': f'Discord member: {member_data.get("user", {}).get("username", "Unknown")}',
                    'discord_id': discord_id,
                    'username': member_data.get('user', {}).get('username')
                }
            else:
                return {
                    'verified': False,
                    'points': 0,
                    'proof': 'Not a Discord server member',
                    'error': f'Discord API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Discord verification error: {e}")
            return {
                'verified': False,
                'points': 0,
                'error': f'Discord verification failed: {str(e)}'
            }
    
    def verify_telegram_membership(self, code: str) -> Dict[str, Any]:
        """Verify Telegram membership using verification code"""
        
        # Find verification code
        verification = self.db.query(TelegramVerification).filter(
            TelegramVerification.code == code,
            TelegramVerification.used == False,
            TelegramVerification.expires_at > datetime.now()
        ).first()
        
        if not verification:
            return {
                'verified': False,
                'points': 0,
                'error': 'Invalid or expired verification code'
            }
        
        # Mark as used
        verification.used = True
        verification.used_at = datetime.now()
        self.db.commit()
        
        return {
            'verified': True,
            'points': 30,
            'proof': f'Telegram verified: {verification.telegram_id}',
            'telegram_id': verification.telegram_id
        }
    
    def verify_twitter_engagement(self, twitter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify Twitter follow and retweet"""
        
        bearer_token = self.get_config('TWITTER_BEARER_TOKEN')
        our_account_id = self.get_config('OUR_TWITTER_ACCOUNT_ID')
        announcement_tweet_id = self.get_config('AIRDROP_ANNOUNCEMENT_TWEET_ID')
        
        if not all([bearer_token, our_account_id, announcement_tweet_id]):
            return {
                'verified': False,
                'points': 0,
                'error': 'Twitter verification not configured'
            }
        
        try:
            headers = {'Authorization': f'Bearer {bearer_token}'}
            user_id = twitter_data.get('user_id')
            
            # Check if user follows our account
            follow_url = f'https://api.twitter.com/2/users/{user_id}/following/{our_account_id}'
            follow_response = requests.get(follow_url, headers=headers, timeout=10)
            
            is_following = follow_response.status_code == 200
            
            # Check if user retweeted announcement
            retweet_url = f'https://api.twitter.com/2/tweets/{announcement_tweet_id}/retweeted_by'
            retweet_response = requests.get(retweet_url, headers=headers, timeout=10)
            
            has_retweeted = False
            if retweet_response.status_code == 200:
                retweet_data = retweet_response.json()
                retweeted_by = [user['id'] for user in retweet_data.get('data', [])]
                has_retweeted = user_id in retweeted_by
            
            if is_following and has_retweeted:
                return {
                    'verified': True,
                    'points': 20,
                    'proof': 'Twitter follow + retweet verified',
                    'following': True,
                    'retweeted': True
                }
            else:
                return {
                    'verified': False,
                    'points': 0,
                    'proof': f'Following: {is_following}, Retweeted: {has_retweeted}',
                    'following': is_following,
                    'retweeted': has_retweeted
                }
                
        except Exception as e:
            logger.error(f"Twitter verification error: {e}")
            return {
                'verified': False,
                'points': 0,
                'error': f'Twitter verification failed: {str(e)}'
            }
    
    def verify_referral(self, referrer_principal: str, referee_principal: str) -> Dict[str, Any]:
        """Verify referral relationship"""
        
        # Check if referral exists
        referral = self.db.query(AirdropReferral).filter(
            AirdropReferral.referrer_principal == referrer_principal,
            AirdropReferral.referee_principal == referee_principal
        ).first()
        
        if referral:
            return {
                'verified': True,
                'points': 50,
                'proof': f'Referral: {referee_principal}',
                'referral_id': referral.id,
                'created_at': referral.created_at
            }
        
        return {
            'verified': False,
            'points': 0,
            'proof': 'No referral relationship found'
        }


class SNSParticipationVerification(VerificationService):
    """Verification service for SNS participation tasks"""
    
    def verify_sns_participation(self, principal: str) -> Dict[str, Any]:
        """Verify SNS sale participation"""
        
        swap_canister_id = self.get_config('SNS_SWAP_CANISTER_ID')
        ic_mainnet_url = self.get_config('IC_MAINNET_URL', 'https://ic0.app')
        
        if not swap_canister_id:
            return {
                'verified': False,
                'points': 0,
                'error': 'SNS swap canister not configured'
            }
        
        try:
            # TODO: Implement actual IC blockchain query
            # This is a placeholder - in practice, you'd use ic-py or similar
            # to query the SNS swap canister
            
            # For now, simulate verification
            icp_committed = 1000  # Replace with actual blockchain query
            
            if icp_committed > 0:
                base_points = 100
                bonus_points = min(icp_committed // 100, 500)  # Bonus: 1 point per 100 ICP, max 500
                total_points = base_points + bonus_points
                
                return {
                    'verified': True,
                    'points': total_points,
                    'proof': f'ICP committed: {icp_committed}',
                    'icp_committed': icp_committed,
                    'base_points': base_points,
                    'bonus_points': bonus_points
                }
            
            return {
                'verified': False,
                'points': 0,
                'proof': 'No SNS participation found'
            }
            
        except Exception as e:
            logger.error(f"SNS participation verification error: {e}")
            return {
                'verified': False,
                'points': 0,
                'error': f'SNS verification failed: {str(e)}'
            }
    
    def verify_governance_votes(self, principal: str) -> Dict[str, Any]:
        """Verify governance votes cast"""
        
        governance_canister_id = self.get_config('SNS_GOVERNANCE_CANISTER_ID')
        
        if not governance_canister_id:
            return {
                'verified': False,
                'points': 0,
                'error': 'SNS governance canister not configured'
            }
        
        try:
            # TODO: Implement actual SNS governance query
            # This is a placeholder - in practice, you'd query the governance canister
            
            # For now, simulate verification
            votes_cast = 5  # Replace with actual governance query
            
            if votes_cast > 0:
                points = votes_cast * 50
                return {
                    'verified': True,
                    'points': points,
                    'proof': f'{votes_cast} votes cast',
                    'votes_cast': votes_cast
                }
            
            return {
                'verified': False,
                'points': 0,
                'proof': 'No governance votes found'
            }
            
        except Exception as e:
            logger.error(f"Governance votes verification error: {e}")
            return {
                'verified': False,
                'points': 0,
                'error': f'Governance verification failed: {str(e)}'
            }


class DeveloperContributionsVerification(VerificationService):
    """Verification service for developer contribution tasks"""
    
    def verify_bot_template_submission(self, github_repo: str) -> Dict[str, Any]:
        """Verify bot template submission meets requirements"""
        
        github_token = self.get_config('GITHUB_TOKEN')
        
        if not github_token:
            return {
                'verified': False,
                'points': 0,
                'error': 'GitHub token not configured'
            }
        
        try:
            headers = {'Authorization': f'token {github_token}'}
            
            # Check if repo exists
            repo_url = f'https://api.github.com/repos/{github_repo}'
            repo_response = requests.get(repo_url, headers=headers, timeout=10)
            
            if repo_response.status_code != 200:
                return {
                    'verified': False,
                    'points': 0,
                    'error': 'GitHub repository not found'
                }
            
            repo_data = repo_response.json()
            
            # Check repository requirements
            checks = {
                'has_readme': self._check_file_exists(github_repo, 'README.md', headers),
                'has_tests': self._check_directory_exists(github_repo, 'tests', headers),
                'has_documentation': self._check_file_exists(github_repo, 'DOCS.md', headers),
                'proper_structure': self._check_bot_structure(github_repo, headers)
            }
            
            all_checks_passed = all(checks.values())
            points = 1000 if all_checks_passed else 500
            
            return {
                'verified': True,
                'points': points,
                'proof': f'GitHub repo: {github_repo}',
                'checks': checks,
                'all_checks_passed': all_checks_passed,
                'repo_name': repo_data.get('name'),
                'repo_description': repo_data.get('description')
            }
            
        except Exception as e:
            logger.error(f"Bot template verification error: {e}")
            return {
                'verified': False,
                'points': 0,
                'error': f'Template verification failed: {str(e)}'
            }
    
    def verify_merged_pr(self, github_username: str, pr_number: int) -> Dict[str, Any]:
        """Verify merged pull request"""
        
        github_token = self.get_config('GITHUB_TOKEN')
        
        if not github_token:
            return {
                'verified': False,
                'points': 0,
                'error': 'GitHub token not configured'
            }
        
        try:
            headers = {'Authorization': f'token {github_token}'}
            
            # Get PR details
            pr_url = f'https://api.github.com/repos/your-org/your-repo/pulls/{pr_number}'
            pr_response = requests.get(pr_url, headers=headers, timeout=10)
            
            if pr_response.status_code != 200:
                return {
                    'verified': False,
                    'points': 0,
                    'error': 'Pull request not found'
                }
            
            pr_data = pr_response.json()
            
            # Check if PR is merged and author matches
            if (pr_data.get('merged') and 
                pr_data.get('user', {}).get('login') == github_username):
                
                return {
                    'verified': True,
                    'points': 500,
                    'proof': f'PR #{pr_number} merged',
                    'pr_number': pr_number,
                    'pr_title': pr_data.get('title'),
                    'merged_at': pr_data.get('merged_at')
                }
            
            return {
                'verified': False,
                'points': 0,
                'proof': 'PR not merged or author mismatch'
            }
            
        except Exception as e:
            logger.error(f"Merged PR verification error: {e}")
            return {
                'verified': False,
                'points': 0,
                'error': f'PR verification failed: {str(e)}'
            }
    
    def verify_bug_report(self, github_username: str, issue_number: int) -> Dict[str, Any]:
        """Verify confirmed bug report"""
        
        github_token = self.get_config('GITHUB_TOKEN')
        
        if not github_token:
            return {
                'verified': False,
                'points': 0,
                'error': 'GitHub token not configured'
            }
        
        try:
            headers = {'Authorization': f'token {github_token}'}
            
            # Get issue details
            issue_url = f'https://api.github.com/repos/your-org/your-repo/issues/{issue_number}'
            issue_response = requests.get(issue_url, headers=headers, timeout=10)
            
            if issue_response.status_code != 200:
                return {
                    'verified': False,
                    'points': 0,
                    'error': 'Issue not found'
                }
            
            issue_data = issue_response.json()
            
            # Check if issue is by the user and has confirmed-bug label
            labels = [label['name'] for label in issue_data.get('labels', [])]
            
            if (issue_data.get('user', {}).get('login') == github_username and
                'confirmed-bug' in labels):
                
                return {
                    'verified': True,
                    'points': 100,
                    'proof': f'Bug report #{issue_number} confirmed',
                    'issue_number': issue_number,
                    'issue_title': issue_data.get('title'),
                    'labels': labels
                }
            
            return {
                'verified': False,
                'points': 0,
                'proof': 'Issue not confirmed as bug or author mismatch'
            }
            
        except Exception as e:
            logger.error(f"Bug report verification error: {e}")
            return {
                'verified': False,
                'points': 0,
                'error': f'Bug report verification failed: {str(e)}'
            }
    
    def _check_file_exists(self, repo: str, file_path: str, headers: Dict[str, str]) -> bool:
        """Check if file exists in GitHub repository"""
        try:
            url = f'https://api.github.com/repos/{repo}/contents/{file_path}'
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _check_directory_exists(self, repo: str, dir_path: str, headers: Dict[str, str]) -> bool:
        """Check if directory exists in GitHub repository"""
        try:
            url = f'https://api.github.com/repos/{repo}/contents/{dir_path}'
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _check_bot_structure(self, repo: str, headers: Dict[str, str]) -> bool:
        """Check if repository has proper bot structure"""
        required_files = ['bot.py', 'requirements.txt', 'config.json']
        
        for file_path in required_files:
            if not self._check_file_exists(repo, file_path, headers):
                return False
        
        return True

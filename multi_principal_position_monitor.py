"""
Multi-Principal Position Monitor - Monitor nhiều principal IDs động
Hệ thống monitor tất cả active subscriptions và positions của từng user
"""

import sys
import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot_files.binance_futures_bot import BinanceFuturesBot, BinanceFuturesIntegration
from bots.bot_sdk.Action import Action
from services.llm_integration import create_llm_service
from core.api_key_manager import get_bot_api_keys
from core.database import get_db
from core import crud, models

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PrincipalMonitor:
    """Monitor cho một principal ID cụ thể"""
    
    def __init__(self, user_principal_id: str, testnet: bool = True):
        self.user_principal_id = user_principal_id
        self.testnet = testnet
        self.binance_client = None
        self.last_check = None
        self.last_llm_analysis = None
        self.last_llm_time = None
        
        # Monitoring config
        self.check_interval = 60  # Check every 60 seconds
        self.max_loss_threshold = -0.05  # -5% max loss
        self.profit_take_threshold = 0.03  # 3% profit
        self.llm_interval = 15 * 60  # 15 minutes
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Binance client with database keys"""
        try:
            logger.info(f"Loading API keys for principal: {self.user_principal_id}")
            db_credentials = get_bot_api_keys(
                user_principal_id=self.user_principal_id,
                exchange="BINANCE",
                is_testnet=self.testnet
            )
            
            if not db_credentials:
                logger.warning(f"No API credentials found for principal: {self.user_principal_id}")
                return False
            
            self.binance_client = BinanceFuturesIntegration(
                db_credentials['api_key'], 
                db_credentials['api_secret'], 
                self.testnet
            )
            logger.info(f"✅ Client initialized for principal: {self.user_principal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize client for {self.user_principal_id}: {e}")
            return False
    
    async def check_positions(self) -> List[Dict[str, Any]]:
        """Kiểm tra positions cho principal này"""
        if not self.binance_client:
            return []
        
        try:
            positions = self.binance_client.get_positions()
            active_positions = []
            
            for position in positions:
                if hasattr(position, 'size'):
                    position_amt = float(position.size)
                    if position_amt != 0:  # Only active positions
                        pos_data = {
                            'principal_id': self.user_principal_id,
                            'symbol': position.symbol,
                            'side': position.side,
                            'size': abs(position_amt),
                            'entry_price': float(position.entry_price),
                            'mark_price': float(position.mark_price),
                            'unrealized_pnl': float(position.pnl),
                            'pnl_percentage': float(position.percentage) if position.percentage else 0,
                            'timestamp': datetime.now().isoformat(),
                            'risk_level': self._assess_risk(float(position.percentage) if position.percentage else 0)
                        }
                        active_positions.append(pos_data)
            
            self.last_check = datetime.now()
            return active_positions
            
        except Exception as e:
            logger.error(f"Error checking positions for {self.user_principal_id}: {e}")
            return []
    
    def _assess_risk(self, pnl_percentage: float) -> str:
        """Đánh giá mức độ rủi ro"""
        if pnl_percentage <= self.max_loss_threshold * 100:
            return "CRITICAL"
        elif pnl_percentage <= -2:
            return "HIGH"
        elif pnl_percentage >= self.profit_take_threshold * 100:
            return "PROFIT_READY"
        else:
            return "NORMAL"

class MultiPrincipalPositionMonitor:
    """Hệ thống monitor nhiều principal IDs động"""
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.principal_monitors: Dict[str, PrincipalMonitor] = {}
        self.active_subscriptions: List[Dict] = []
        self.last_subscription_update = None
        
        # LLM service (shared across all principals)
        self.llm_service = None
        self._initialize_llm()
        
        logger.info("🚀 Multi-Principal Position Monitor initialized")
    
    def _initialize_llm(self):
        """Initialize shared LLM service"""
        try:
            llm_config = {
                'openai_api_key': os.getenv('OPENAI_API_KEY'),
                'claude_api_key': os.getenv('CLAUDE_API_KEY'), 
                'gemini_api_key': os.getenv('GEMINI_API_KEY'),
            }
            self.llm_service = create_llm_service(llm_config)
            logger.info("🧠 Shared LLM service initialized")
        except Exception as e:
            logger.warning(f"LLM service not available: {e}")
    
    async def update_active_subscriptions(self):
        """Cập nhật danh sách active subscriptions từ database"""
        try:
            db = next(get_db())
            # Get all active subscriptions with futures bots
            subscriptions = db.query(models.Subscription).join(
                models.Bot
            ).filter(
                models.Subscription.status == "ACTIVE",
                models.Subscription.expires_at > datetime.now(),
                models.Subscription.started_at <= datetime.now(),
                models.Bot.bot_type == "FUTURES"  # Only futures bots
            ).all()
            
            current_principals = set()
            for sub in subscriptions:
                if sub.user_principal_id:
                    current_principals.add(sub.user_principal_id)
                    
                    # Add new principal monitors
                    if sub.user_principal_id not in self.principal_monitors:
                        logger.info(f"➕ Adding monitor for new principal: {sub.user_principal_id}")
                        monitor = PrincipalMonitor(sub.user_principal_id, sub.is_testnet)
                        self.principal_monitors[sub.user_principal_id] = monitor
            
            # Remove monitors for inactive subscriptions
            to_remove = []
            for principal_id in self.principal_monitors:
                if principal_id not in current_principals:
                    logger.info(f"➖ Removing monitor for inactive principal: {principal_id}")
                    to_remove.append(principal_id)
            
            for principal_id in to_remove:
                del self.principal_monitors[principal_id]
            
            self.last_subscription_update = datetime.now()
            logger.info(f"📊 Monitoring {len(self.principal_monitors)} active principals")
            
        except Exception as e:
            logger.error(f"Failed to update subscriptions: {e}")
    
    async def check_all_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Kiểm tra positions của tất cả principals"""
        all_positions = {}
        
        # Use ThreadPoolExecutor for concurrent position checking
        with ThreadPoolExecutor(max_workers=10) as executor:
            tasks = []
            for principal_id, monitor in self.principal_monitors.items():
                task = executor.submit(asyncio.run, monitor.check_positions())
                tasks.append((principal_id, task))
            
            for principal_id, task in tasks:
                try:
                    positions = task.result(timeout=30)  # 30 second timeout
                    if positions:
                        all_positions[principal_id] = positions
                        
                        # Log critical positions
                        critical_positions = [p for p in positions if p['risk_level'] == 'CRITICAL']
                        if critical_positions:
                            logger.warning(f"🚨 CRITICAL positions found for {principal_id}: {len(critical_positions)}")
                
                except Exception as e:
                    logger.error(f"Failed to check positions for {principal_id}: {e}")
        
        return all_positions
    
    async def handle_critical_positions(self, all_positions: Dict[str, List[Dict[str, Any]]]):
        """Xử lý các positions có risk level CRITICAL"""
        for principal_id, positions in all_positions.items():
            critical_positions = [p for p in positions if p['risk_level'] == 'CRITICAL']
            
            for pos in critical_positions:
                logger.warning(f"🚨 CRITICAL POSITION - Principal: {principal_id}, Symbol: {pos['symbol']}, PnL: {pos['pnl_percentage']:.2f}%")
                
                # TODO: Implement auto-close logic
                # await self._auto_close_position(principal_id, pos)
    
    async def generate_monitoring_report(self, all_positions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Tạo báo cáo tổng quan"""
        total_positions = 0
        total_pnl = 0
        risk_summary = {"CRITICAL": 0, "HIGH": 0, "PROFIT_READY": 0, "NORMAL": 0}
        
        for principal_id, positions in all_positions.items():
            total_positions += len(positions)
            for pos in positions:
                total_pnl += pos['unrealized_pnl']
                risk_summary[pos['risk_level']] += 1
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_principals': len(self.principal_monitors),
            'total_positions': total_positions,
            'total_unrealized_pnl': total_pnl,
            'risk_summary': risk_summary,
            'detailed_positions': all_positions
        }
        
        return report
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("🔄 Starting multi-principal monitoring loop...")
        
        while True:
            try:
                # Update subscriptions every 5 minutes
                if (not self.last_subscription_update or 
                    datetime.now() - self.last_subscription_update > timedelta(minutes=5)):
                    await self.update_active_subscriptions()
                
                if not self.principal_monitors:
                    logger.info("No active principals to monitor, waiting...")
                    await asyncio.sleep(self.check_interval)
                    continue
                
                # Check all positions
                logger.info(f"📊 Checking positions for {len(self.principal_monitors)} principals...")
                all_positions = await self.check_all_positions()
                
                # Handle critical positions
                await self.handle_critical_positions(all_positions)
                
                # Generate and log report
                report = await self.generate_monitoring_report(all_positions)
                logger.info(f"📈 Monitoring Report: {report['total_principals']} principals, {report['total_positions']} positions, PnL: ${report['total_unrealized_pnl']:.2f}")
                
                if report['risk_summary']['CRITICAL'] > 0:
                    logger.warning(f"🚨 {report['risk_summary']['CRITICAL']} CRITICAL positions require attention!")
                
                # Save report to file
                with open(f"monitoring_reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                    json.dump(report, f, indent=2)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Wait for next check
            logger.info(f"⏰ Next check in {self.check_interval} seconds...")
            await asyncio.sleep(self.check_interval)

async def main():
    """Main function"""
    print("🚀 Multi-Principal Position Monitor")
    print("="*50)
    print("✅ Monitor nhiều principal IDs động")
    print("✅ Auto-discover từ active subscriptions") 
    print("✅ Concurrent position checking")
    print("✅ Risk-based monitoring với alerts")
    print("✅ Comprehensive reporting")
    print("✅ Auto-scaling theo số lượng users")
    print()
    
    # Create monitoring reports directory
    os.makedirs("monitoring_reports", exist_ok=True)
    
    # Initialize and start monitor
    monitor = MultiPrincipalPositionMonitor(check_interval=60)
    
    try:
        await monitor.monitor_loop()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Monitor error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
"""
Demo Real Trading System - Tích hợp Bot với Database và Monitoring
Thể hiện cách bot hoạt động với:
1. Lưu transaction vào database thật
2. Monitoring tự động
3. Risk management
4. Email notifications
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot_files.binance_futures_bot import BinanceFuturesBot
from bots.bot_sdk.Action import Action

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealTradingSystem:
    """Hệ thống trading thật tích hợp với database và monitoring"""
    
    def __init__(self):
        self.bot = None
        self.subscription_id = None
        self.db_session = None
        
    def init_database_connection(self):
        """Khởi tạo kết nối database"""
        try:
            # Import database components
            from core.database import SessionLocal
            from core import crud, models, schemas
            
            self.db_session = SessionLocal()
            print("✅ Database connection established")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def save_trade_to_database(self, trade_result: Dict[str, Any]) -> bool:
        """Lưu trade vào database thật"""
        try:
            if not self.db_session:
                print("❌ No database connection")
                return False
            
            from core import crud, schemas
            
            # Create trade record
            trade_data = schemas.TradeCreate(
                subscription_id=self.subscription_id or 1,  # Default to 1 for demo
                side=trade_result.get('action'),
                status=schemas.TradeStatus.OPEN,
                entry_price=float(trade_result.get('entry_price', 0)),
                quantity=float(trade_result.get('quantity', 0)),
                stop_loss_price=trade_result.get('stop_loss', {}).get('price'),
                take_profit_price=trade_result.get('take_profit', {}).get('price'),
                exchange_order_id=str(trade_result.get('main_order_id', ''))
            )
            
            # Save to database
            db_trade = crud.create_trade(self.db_session, trade_data)
            
            # Log action
            crud.log_bot_action(
                self.db_session,
                self.subscription_id or 1,
                f"{trade_result.get('action')}_EXECUTED",
                f"Trade executed: {trade_result.get('reason', '')}"
            )
            
            print(f"✅ Trade saved to database with ID: {db_trade.id}")
            print(f"📊 Order ID: {trade_result.get('main_order_id')}")
            print(f"💰 Entry: ${trade_result.get('entry_price')}")
            print(f"🛡️ Stop Loss: ${trade_result.get('stop_loss', {}).get('price')}")
            print(f"🎯 Take Profit: ${trade_result.get('take_profit', {}).get('price')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save trade to database: {e}")
            if self.db_session:
                self.db_session.rollback()
            return False
    
    def get_trading_history(self) -> List[Dict[str, Any]]:
        """Lấy lịch sử trading từ database"""
        try:
            if not self.db_session:
                return []
            
            from core import crud
            
            # Get recent trades
            trades = crud.get_subscription_trades_paginated(
                self.db_session, 
                self.subscription_id or 1, 
                skip=0, 
                limit=10
            )
            
            history = []
            for trade in trades:
                history.append({
                    'id': trade.id,
                    'side': trade.side,
                    'status': trade.status.value,
                    'entry_price': float(trade.entry_price) if trade.entry_price else None,
                    'exit_price': float(trade.exit_price) if trade.exit_price else None,
                    'quantity': float(trade.quantity) if trade.quantity else None,
                    'pnl': float(trade.pnl) if trade.pnl else None,
                    'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
                    'exit_time': trade.exit_time.isoformat() if trade.exit_time else None
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get trading history: {e}")
            return []
    
    def print_trading_summary(self):
        """In tóm tắt trading"""
        try:
            print("\n💼 TRADING SUMMARY FROM DATABASE")
            print("=" * 50)
            
            history = self.get_trading_history()
            
            if not history:
                print("📊 No trading history found")
                return
            
            print(f"📊 Total Trades: {len(history)}")
            
            # Calculate stats
            open_trades = [t for t in history if t['status'] == 'OPEN']
            closed_trades = [t for t in history if t['status'] == 'CLOSED' and t['pnl'] is not None]
            
            print(f"🟢 Open Positions: {len(open_trades)}")
            print(f"🔒 Closed Positions: {len(closed_trades)}")
            
            if closed_trades:
                total_pnl = sum(t['pnl'] for t in closed_trades)
                winning_trades = [t for t in closed_trades if t['pnl'] > 0]
                win_rate = len(winning_trades) / len(closed_trades) * 100
                
                print(f"💰 Total PnL: ${total_pnl:.2f}")
                print(f"🎯 Win Rate: {win_rate:.1f}%")
            
            print("\n📋 Recent Trades:")
            for i, trade in enumerate(history[:5], 1):
                status_emoji = "🟢" if trade['status'] == 'OPEN' else "🔒"
                pnl_text = f"${trade['pnl']:+.2f}" if trade['pnl'] else "Pending"
                
                print(f"{i}. {status_emoji} {trade['side']} @ ${trade['entry_price']:.2f} - PnL: {pnl_text}")
        
        except Exception as e:
            logger.error(f"Error printing trading summary: {e}")
    
    async def run_integrated_trading_cycle(self):
        """Chạy chu trình trading tích hợp với database"""
        try:
            print("🚀 RUNNING INTEGRATED TRADING CYCLE")
            print("=" * 60)
            
            # Bot configuration
            config = {
                'trading_pair': 'BTCUSDT',
                'testnet': True,
                'leverage': 5,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04,
                'position_size_pct': 0.1,
                'timeframes': ['5m', '30m', '1h', '4h', '1d'],
                'primary_timeframe': '1h',
                'use_llm_analysis': True,
                'llm_model': 'openai',
                'require_confirmation': False  # Auto mode for demo
            }
            
            api_keys = {
                'api_key': 'eTVRuGceal7eZq0AlNKQLLEw5AILFbMOY9Shp2BvXRvkiu5SCQNK4Pq4vaS9f6bd',
                'api_secret': 'BgW2TKVLiFVy550iaBiHUNwIVnIiQ1Al1ldPoU9P2x6s3qWfV6BzHAeVZOQqDnJW'
            }
            
            # Initialize bot
            self.bot = BinanceFuturesBot(config, api_keys)
            print("✅ Bot initialized")
            
            # Check account
            account_status = self.bot.check_account_status()
            
            # Crawl and analyze data
            print("\n📊 Step 1: Multi-timeframe Analysis...")
            multi_timeframe_data = self.bot.crawl_data()
            analysis = self.bot.analyze_data(multi_timeframe_data)
            
            # Generate signal
            print("\n🧠 Step 2: LLM Signal Generation...")
            signal = self.bot.generate_signal(analysis)
            
            print(f"🎯 Signal: {signal.action}")
            print(f"📊 Confidence: {signal.value*100:.1f}%")
            print(f"💡 Reason: {signal.reason}")
            
            # Execute trade
            if signal.action != "HOLD":
                print(f"\n🚀 Step 3: Executing Real Trade...")
                trade_result = await self.bot.setup_position(signal, analysis)
                
                if trade_result.get('status') == 'success':
                    print("✅ Trade executed successfully!")
                    
                    # Save to database
                    if self.db_session:
                        self.save_trade_to_database(trade_result)
                    else:
                        # Fallback to JSON file
                        self.bot.save_transaction_to_db(trade_result)
                    
                    return trade_result
                else:
                    print(f"❌ Trade failed: {trade_result.get('message')}")
                    return None
            else:
                print("🟡 Signal is HOLD - No trade executed")
                return None
        
        except Exception as e:
            logger.error(f"Error in integrated trading cycle: {e}")
            return None
    
    def close_resources(self):
        """Đóng tài nguyên"""
        if self.db_session:
            self.db_session.close()
            print("✅ Database connection closed")

async def main():
    """Main demo function"""
    print("🤖 REAL TRADING SYSTEM DEMO")
    print("=" * 70)
    print("Tính năng được demo:")
    print("✅ Bot thực hiện trade thật trên Binance")
    print("✅ Lưu transaction vào database")
    print("✅ Quản lý rủi ro tự động") 
    print("✅ Kiểm tra account balance")
    print("✅ Multi-timeframe analysis với LLM")
    print()
    
    system = RealTradingSystem()
    
    try:
        # Try to connect to database
        db_connected = system.init_database_connection()
        if not db_connected:
            print("⚠️ Running without database - using file storage")
        
        # Show trading history if database available
        if db_connected:
            system.print_trading_summary()
        
        # Run trading cycle
        trade_result = await system.run_integrated_trading_cycle()
        
        if trade_result:
            print(f"\n🎊 TRADING CYCLE COMPLETED!")
            print(f"📈 Action: {trade_result.get('action')}")
            print(f"💰 Entry Price: ${trade_result.get('entry_price')}")
            print(f"📊 Order ID: {trade_result.get('main_order_id')}")
        
        # Show updated summary
        if db_connected:
            print("\n" + "="*50)
            system.print_trading_summary()
    
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
    finally:
        system.close_resources()

if __name__ == "__main__":
    print("⚠️ CẢNH BÁO: Đây là demo với TESTNET")
    print("Để chạy LIVE trading, thay testnet=False trong config")
    print()
    
    confirm = input("Tiếp tục demo? (yes/no): ")
    if confirm.lower() == 'yes':
        asyncio.run(main())
    else:
        print("👋 Demo cancelled")
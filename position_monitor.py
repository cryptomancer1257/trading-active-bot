"""
Position Monitoring System - Tự động kiểm tra và quản lý vị thế
Hệ thống này chạy định kỳ để kiểm tra các vị thế đang mở và thực hiện action tự động
"""

import sys
import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot_files.binance_futures_bot import BinanceFuturesBot, BinanceFuturesIntegration
from bots.bot_sdk.Action import Action
from services.llm_integration import create_llm_service
from core.api_key_manager import get_bot_api_keys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PositionMonitor:
    """Hệ thống monitoring tự động các vị thế futures"""
    
    def __init__(self, user_principal_id: str, testnet: bool = True):
        self.user_principal_id = user_principal_id
        self.testnet = testnet
        
        # Load API keys from database
        logger.info(f"Loading exchange API keys for principal ID: {user_principal_id}")
        db_credentials = get_bot_api_keys(
            user_principal_id=user_principal_id,
            exchange="BINANCE",
            is_testnet=testnet
        )
        
        if not db_credentials:
            raise ValueError(f"No exchange API credentials found in database for principal ID: {user_principal_id}. Please store your Binance API keys in the database first.")
        
        self.api_key = db_credentials['api_key']
        self.api_secret = db_credentials['api_secret']
        
        # Initialize Binance client
        self.binance_client = BinanceFuturesIntegration(self.api_key, self.api_secret, testnet)
        logger.info(f"✅ Position Monitor initialized with database keys for principal: {user_principal_id}")
        
        # Monitoring config
        self.check_interval = 60  # Check every 60 seconds
        self.max_loss_threshold = -0.05  # -5% max loss before emergency close
        self.profit_take_threshold = 0.03  # 3% profit to consider taking partial profit
        
        # LLM Configuration - 15 minute intervals
        self.llm_interval = 15 * 60  # 15 minutes in seconds
        self.last_llm_analysis = None
        self.last_llm_time = None
        self.llm_service = None
        
        # Initialize LLM service
        try:
            llm_config = {
                'openai_api_key': os.getenv('OPENAI_API_KEY'),
                'claude_api_key': os.getenv('CLAUDE_API_KEY'), 
                'gemini_api_key': os.getenv('GEMINI_API_KEY'),
            }
            self.llm_service = create_llm_service(llm_config)
            logger.info("🧠 LLM service initialized for position monitoring")
        except Exception as e:
            logger.warning(f"LLM service not available: {e}")
        
        logger.info(f"Position Monitor initialized - {'TESTNET' if testnet else 'LIVE'}")
    
    async def check_all_positions(self) -> List[Dict[str, Any]]:
        """Kiểm tra tất cả vị thế hiện tại"""
        try:
            positions = self.binance_client.get_positions()
            active_positions = []
            
            for position in positions:
                # Handle FuturesPosition objects
                if hasattr(position, 'size'):
                    position_amt = float(position.size)
                    if position_amt != 0:  # Only active positions
                        pos_data = {
                            'symbol': position.symbol,
                            'side': position.side,
                            'size': abs(position_amt),
                            'entry_price': float(position.entry_price),
                            'mark_price': float(position.mark_price),
                            'unrealized_pnl': float(position.pnl),
                            'pnl_percentage': float(position.percentage) if position.percentage else 0,
                            'margin_ratio': 0,  # Not available in FuturesPosition
                            'timestamp': datetime.now().isoformat()
                        }
                        active_positions.append(pos_data)
            
            return active_positions
        
        except Exception as e:
            logger.error(f"Error checking positions: {e}")
            return []
    
    async def get_market_context(self, symbol: str) -> Dict[str, Any]:
        """Lấy context thị trường để cung cấp cho LLM"""
        try:
            # Lấy dữ liệu thị trường gần đây
            klines = self.binance_client.get_klines(symbol, "1h", 24)  # 24h data
            
            # Fix DataFrame check - use .empty or len() for proper validation
            klines_valid = False
            if klines is not None:
                # Check if it's pandas DataFrame
                if hasattr(klines, 'empty'):
                    klines_valid = not klines.empty and len(klines) >= 2
                # Check if it's list
                elif isinstance(klines, list):
                    klines_valid = len(klines) >= 2
                # Check if it's dict or other iterable
                else:
                    try:
                        klines_valid = len(klines) >= 2
                    except:
                        klines_valid = False
            
            if klines_valid:
                # Handle different data formats
                if hasattr(klines, 'iloc'):  # pandas DataFrame
                    current_price = float(klines.iloc[-1]['close'])
                    prev_price = float(klines.iloc[-2]['close'])
                    volumes = [float(klines.iloc[i]['volume']) for i in range(max(0, len(klines)-5), len(klines))]
                    prices = [float(klines.iloc[i]['close']) for i in range(max(0, len(klines)-10), len(klines))]
                else:  # list or dict format
                    current_price = float(klines[-1]['close'])
                    prev_price = float(klines[-2]['close'])
                    volumes = [float(k['volume']) for k in klines[-5:]]
                    prices = [float(k['close']) for k in klines[-10:]]
                
                price_change = (current_price - prev_price) / prev_price * 100
                
                # Tính volume average
                avg_volume = sum(volumes) / len(volumes) if volumes else 0
                current_volume = volumes[-1] if volumes else 0
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                
                # Tính volatility
                volatility = (max(prices) - min(prices)) / min(prices) * 100 if prices and min(prices) > 0 else 0
                
                return {
                    'price_movement': f"{price_change:+.2f}% in last hour",
                    'volume': f"Current: {current_volume:.0f}, Avg: {avg_volume:.0f} (Ratio: {volume_ratio:.2f})",
                    'volatility': f"{volatility:.2f}%",
                    'sentiment': 'Bullish' if price_change > 0 else 'Bearish',
                    'technical': f"Price trend: {'Up' if price_change > 1 else 'Down' if price_change < -1 else 'Sideways'}"
                }
            else:
                return {
                    'price_movement': 'Unknown',
                    'volume': 'Unknown', 
                    'volatility': 'Unknown',
                    'sentiment': 'Unknown',
                    'technical': 'Unknown'
                }
                
        except Exception as e:
            logger.error(f"Failed to get market context: {e}")
            return {
                'price_movement': 'Error',
                'volume': 'Error',
                'volatility': 'Error',
                'sentiment': 'Unknown', 
                'technical': 'Error'
            }
    
    def should_run_llm_analysis(self) -> bool:
        """Kiểm tra xem có nên chạy LLM analysis không (mỗi 15 phút)"""
        if not self.llm_service:
            return False
            
        current_time = datetime.now()
        
        # Lần đầu tiên hoặc đã quá 15 phút
        if (self.last_llm_time is None or 
            (current_time - self.last_llm_time).total_seconds() >= self.llm_interval):
            return True
            
        return False
    
    async def llm_risk_analysis(self, position: Dict[str, Any], market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Sử dụng LLM để phân tích risk và đưa ra quyết định thông minh"""
        try:
            if not self.llm_service:
                return None
            
            # Chuẩn bị context cho LLM
            analysis_prompt = f"""
            POSITION RISK ANALYSIS - 15-MINUTE STRATEGIC REVIEW:
            
            Current Position:
            - Symbol: {position['symbol']}
            - Side: {position['side']}
            - Size: {position['size']}
            - Entry Price: ${position['entry_price']:,.2f}
            - Current Price: ${position['mark_price']:,.2f}
            - Unrealized PnL: ${position['unrealized_pnl']:+,.2f}
            - PnL Percentage: {position.get('pnl_percentage', 0):+.2f}%
            
            Market Context (Last Hour):
            - Price Movement: {market_context.get('price_movement', 'Unknown')}
            - Volume: {market_context.get('volume', 'Unknown')}
            - Volatility: {market_context.get('volatility', 'Unknown')}
            - Market Sentiment: {market_context.get('sentiment', 'Unknown')}
            - Technical Trend: {market_context.get('technical', 'Unknown')}
            
            Strategic Analysis Needed:
            1. Given the 15-minute strategic review interval, what is the overall risk assessment?
            2. Should we adjust our risk management approach?
            3. Are there any market developments that change our position outlook?
            4. What is the recommended action with current market conditions?
            
            Please provide your analysis in JSON format:
            {{
                "risk_level": "LOW|MEDIUM|HIGH|CRITICAL|PROFITABLE",
                "action": "HOLD|REDUCE_25|REDUCE_50|CLOSE_ALL|TIGHTEN_SL|TAKE_PROFIT",
                "reasoning": "detailed strategic reasoning",
                "market_outlook": "short-term market perspective",
                "confidence": "0-100",
                "next_review_trigger": "what event should trigger next analysis",
                "emergency_threshold": "suggested emergency exit level"
            }}
            """
            
            # Gọi LLM analysis - sử dụng OpenAI
            market_data_for_llm = {
                "symbol": position['symbol'],
                "analysis_type": "position_risk_analysis",
                "position_data": {
                    "side": position['side'],
                    "entry_price": position['entry_price'],
                    "current_price": position['mark_price'],
                    "pnl_percentage": position.get('pnl_percentage', 0),
                    "unrealized_pnl": position['unrealized_pnl']
                },
                "market_context": market_context,
                "prompt": analysis_prompt
            }
            
            llm_response = await self.llm_service.analyze_with_openai(market_data_for_llm)
            
            if llm_response.get('error'):
                raise Exception(f"LLM analysis error: {llm_response['error']}")
            
            # Extract response content
            response = llm_response.get('analysis', llm_response.get('recommendation', str(llm_response)))
            
            # Parse LLM response
            try:
                # Handle different response formats
                llm_result = {}
                
                if isinstance(response, dict):
                    # If it's already a dict (from parsed JSON)
                    if 'recommendation' in response:
                        llm_result = response['recommendation']
                    elif 'analysis' in response:
                        llm_result = response['analysis']
                    else:
                        llm_result = response
                        
                elif isinstance(response, str):
                    # Parse string response
                    if "```json" in response:
                        json_start = response.find("```json") + 7
                        json_end = response.find("```", json_start)
                        json_str = response[json_start:json_end].strip()
                    elif "{" in response and "}" in response:
                        json_start = response.find("{")
                        json_end = response.rfind("}") + 1
                        json_str = response[json_start:json_end]
                    else:
                        # Create simple analysis from string
                        llm_result = {
                            'action': 'HOLD',
                            'reasoning': response[:200] + '...' if len(response) > 200 else response,
                            'confidence': 50
                        }
                        json_str = None
                    
                    if json_str:
                        llm_result = json.loads(json_str)
                
                # Extract analysis results with fallbacks
                recommendation = llm_result.get('recommendation', llm_result)
                
                # Cập nhật cache
                self.last_llm_analysis = {
                    'risk_level': recommendation.get('risk_level', 'MEDIUM'),
                    'action_needed': recommendation.get('action', 'HOLD'),
                    'reason': recommendation.get('reasoning', 'LLM strategic analysis'),
                    'market_outlook': recommendation.get('market_outlook', 'Neutral'),
                    'confidence': float(recommendation.get('confidence', 50)) / 100 if recommendation.get('confidence', 50) > 1 else float(recommendation.get('confidence', 0.5)),
                    'next_review_trigger': recommendation.get('next_review_trigger', 'Next 15-min interval'),
                    'emergency_threshold': recommendation.get('emergency_threshold', 'Default -5%'),
                    'llm_analysis': True,
                    'timestamp': datetime.now().isoformat()
                }
                self.last_llm_time = datetime.now()
                
                logger.info(f"🧠 LLM Analysis completed: {recommendation.get('action', 'HOLD')} ({recommendation.get('confidence', 50)}% confidence)")
                
                return self.last_llm_analysis
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.error(f"Failed to parse LLM response: {e}")
                # Create fallback analysis
                self.last_llm_analysis = {
                    'risk_level': 'MEDIUM',
                    'action_needed': 'HOLD',
                    'reason': f'LLM parsing failed: {str(e)[:100]}',
                    'market_outlook': 'Unknown',
                    'confidence': 0.3,
                    'llm_analysis': True,
                    'timestamp': datetime.now().isoformat()
                }
                self.last_llm_time = datetime.now()
                return self.last_llm_analysis
                
        except Exception as e:
            logger.error(f"LLM risk analysis failed: {e}")
            return None
    
    async def analyze_position_risk(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Phân tích rủi ro của một vị thế - kết hợp Rules và LLM"""
        try:
            pnl_pct = position['pnl_percentage'] / 100  # Convert to decimal
            entry_price = position['entry_price']
            mark_price = position['mark_price']
            side = position['side']
            
            # Calculate price movement percentage
            if side == 'LONG':
                price_change_pct = (mark_price - entry_price) / entry_price
            else:
                price_change_pct = (entry_price - mark_price) / entry_price
            
            # Basic rules-based analysis (fallback)
            basic_analysis = {
                'risk_level': "LOW",
                'action_needed': "HOLD",
                'reason': "Position within normal parameters",
                'llm_analysis': False
            }
            
            # Emergency stop loss (always applies)
            if pnl_pct <= self.max_loss_threshold:
                basic_analysis.update({
                    'risk_level': "CRITICAL",
                    'action_needed': "EMERGENCY_CLOSE",
                    'reason': f"Emergency stop: Loss exceeds {self.max_loss_threshold*100:.1f}%"
                })
            # Profit taking opportunity
            elif pnl_pct >= self.profit_take_threshold:
                basic_analysis.update({
                    'risk_level': "PROFITABLE",
                    'action_needed': "PARTIAL_PROFIT",
                    'reason': f"Consider profit taking: Profit at {pnl_pct*100:.1f}%"
                })
            # High risk warning
            elif pnl_pct <= -0.025:  # -2.5%
                basic_analysis.update({
                    'risk_level': "HIGH",
                    'action_needed': "MONITOR_CLOSE",
                    'reason': "High risk: Consider closing if trend continues"
                })
            
            # Try LLM analysis if it's time (every 15 minutes)
            llm_analysis = None
            if self.should_run_llm_analysis():
                try:
                    market_context = await self.get_market_context(position['symbol'])
                    llm_analysis = await self.llm_risk_analysis(position, market_context)
                except Exception as e:
                    logger.warning(f"LLM analysis failed: {e}")
            
            # Use cached LLM analysis if available and recent
            if not llm_analysis and self.last_llm_analysis:
                # Check if cache is still valid (within 15 minutes)
                if self.last_llm_time and (datetime.now() - self.last_llm_time).total_seconds() < self.llm_interval:
                    llm_analysis = self.last_llm_analysis
            
            # Combine LLM and rules-based analysis
            final_analysis = basic_analysis.copy()
            
            if llm_analysis:
                # LLM overrides basic analysis except for emergency situations
                if basic_analysis['action_needed'] != "EMERGENCY_CLOSE":
                    final_analysis.update({
                        'risk_level': llm_analysis['risk_level'],
                        'action_needed': llm_analysis['action_needed'],
                        'reason': llm_analysis['reason'],
                        'llm_analysis': True,
                        'market_outlook': llm_analysis.get('market_outlook', ''),
                        'confidence': llm_analysis.get('confidence', 0.5),
                        'llm_timestamp': llm_analysis.get('timestamp', '')
                    })
                else:
                    # Emergency case: show both analyses
                    final_analysis.update({
                        'llm_suggestion': llm_analysis['action_needed'],
                        'llm_reason': llm_analysis['reason'],
                        'override_reason': 'Emergency threshold overrides LLM'
                    })
            
            # Add common fields
            final_analysis.update({
                'pnl_percentage': pnl_pct * 100,
                'price_change_pct': price_change_pct * 100,
                'should_auto_close': final_analysis['action_needed'] == "EMERGENCY_CLOSE"
            })
            
            return final_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing position risk: {e}")
            return {
                'risk_level': 'ERROR',
                'action_needed': 'MANUAL_CHECK',
                'reason': f'Analysis error: {e}',
                'should_auto_close': False,
                'llm_analysis': False
            }
    
    async def execute_auto_action(self, position: Dict[str, Any], risk_analysis: Dict[str, Any]) -> bool:
        """Thực hiện action tự động dựa trên phân tích rủi ro"""
        try:
            symbol = position['symbol']
            side = position['side']
            size = position['size']
            action_needed = risk_analysis['action_needed']
            
            if action_needed == "EMERGENCY_CLOSE":
                logger.warning(f"🚨 EMERGENCY CLOSE triggered for {symbol}")
                
                # Close position immediately
                close_side = "SELL" if side == "LONG" else "BUY"
                order = self.binance_client.create_market_order(
                    symbol, close_side, f"{size:.3f}"
                )
                
                logger.info(f"✅ Emergency close executed: {order.order_id}")
                
                # Log emergency action
                self.log_emergency_action(position, risk_analysis, order.order_id)
                return True
            
            elif action_needed == "PARTIAL_PROFIT":
                # Take 50% profit
                partial_size = size * 0.5
                close_side = "SELL" if side == "LONG" else "BUY"
                
                order = self.binance_client.create_market_order(
                    symbol, close_side, f"{partial_size:.3f}"
                )
                
                logger.info(f"💰 Partial profit taken: {order.order_id} - 50% of position")
                return True
            
            elif action_needed == "MONITOR_CLOSE":
                logger.warning(f"⚠️ High risk position detected: {symbol} - Manual review recommended")
                return False
            
            return False
        
        except Exception as e:
            logger.error(f"Error executing auto action: {e}")
            return False
    
    def log_emergency_action(self, position: Dict[str, Any], risk_analysis: Dict[str, Any], order_id: str):
        """Lưu log các action khẩn cấp"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action_type': 'EMERGENCY_CLOSE',
                'symbol': position['symbol'],
                'side': position['side'],
                'size': position['size'],
                'entry_price': position['entry_price'],
                'close_price': position['mark_price'],
                'pnl_percentage': risk_analysis['pnl_percentage'],
                'reason': risk_analysis['reason'],
                'order_id': order_id,
                'auto_executed': True
            }
            
            # Save to emergency log file
            filename = 'emergency_actions.json'
            try:
                with open(filename, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
            
            logs.append(log_entry)
            
            with open(filename, 'w') as f:
                json.dump(logs, f, indent=2)
            
            logger.info(f"📝 Emergency action logged to {filename}")
        
        except Exception as e:
            logger.error(f"Failed to log emergency action: {e}")
    
    async def print_position_summary(self, positions: List[Dict[str, Any]]):
        """In tóm tắt các vị thế với LLM insights"""
        current_time = datetime.now()
        print(f"\n💼 POSITION MONITORING REPORT - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Show LLM status
        if self.llm_service:
            if self.last_llm_time:
                time_since_llm = (current_time - self.last_llm_time).total_seconds() / 60
                llm_status = f"🧠 LLM: Last analysis {time_since_llm:.0f}min ago"
            else:
                llm_status = "🧠 LLM: Ready for first analysis"
        else:
            llm_status = "📊 LLM: Not available (Rules-based only)"
        
        print(llm_status)
        
        if not positions:
            print("📊 No active positions")
            return
        
        total_pnl = sum(pos['unrealized_pnl'] for pos in positions)
        total_pnl_pct = sum(pos['pnl_percentage'] for pos in positions) / len(positions)
        
        print(f"📊 Total Positions: {len(positions)}")
        print(f"💰 Total Unrealized PnL: ${total_pnl:+.2f}")
        print(f"📈 Average PnL%: {total_pnl_pct:+.2f}%")
        print("-" * 80)
        
        for i, position in enumerate(positions, 1):
            risk_analysis = await self.analyze_position_risk(position)
            
            risk_emoji = {
                'LOW': '🟢',
                'MEDIUM': '🟡',
                'HIGH': '🟠', 
                'CRITICAL': '🔴',
                'PROFITABLE': '💚',
                'ERROR': '❌'
            }.get(risk_analysis['risk_level'], '❓')
            
            # Determine analysis source
            analysis_source = "🧠 AI" if risk_analysis.get('llm_analysis') else "📊 Rules"
            
            print(f"{i}. {position['symbol']} {position['side']}")
            print(f"   💰 Size: {position['size']:.3f} | Entry: ${position['entry_price']:.2f} | Mark: ${position['mark_price']:.2f}")
            print(f"   📊 PnL: ${position['unrealized_pnl']:+.2f} ({position['pnl_percentage']:+.2f}%)")
            print(f"   {risk_emoji} Risk: {risk_analysis['risk_level']} ({analysis_source})")
            print(f"   💡 Analysis: {risk_analysis['reason']}")
            
            # Show LLM specific insights
            if risk_analysis.get('llm_analysis'):
                if risk_analysis.get('market_outlook'):
                    print(f"   🔮 Market: {risk_analysis['market_outlook']}")
                if risk_analysis.get('confidence'):
                    print(f"   📈 Confidence: {risk_analysis['confidence']*100:.0f}%")
            
            if risk_analysis['action_needed'] != 'HOLD':
                print(f"   🎯 Recommended Action: {risk_analysis['action_needed']}")
            
            # Show emergency override if applicable
            if risk_analysis.get('override_reason'):
                print(f"   ⚠️ Override: {risk_analysis['override_reason']}")
                if risk_analysis.get('llm_suggestion'):
                    print(f"   🧠 LLM Suggested: {risk_analysis['llm_suggestion']}")
            
            print()
    
    async def monitor_loop(self):
        """Vòng lặp monitoring chính với LLM 15-phút"""
        logger.info("🤖 Starting enhanced position monitoring with LLM intelligence...")
        
        while True:
            try:
                # Check all positions
                positions = await self.check_all_positions()
                
                # Print summary with LLM insights
                await self.print_position_summary(positions)
                
                # Analyze and take auto actions
                for position in positions:
                    risk_analysis = await self.analyze_position_risk(position)
                    
                    # Auto execute emergency actions
                    if risk_analysis['should_auto_close']:
                        success = await self.execute_auto_action(position, risk_analysis)
                        if success:
                            print(f"🤖 AUTO ACTION EXECUTED: {risk_analysis['action_needed']} for {position['symbol']}")
                
                # Show next check timing with LLM info
                next_llm_minutes = 15
                if self.last_llm_time:
                    elapsed_minutes = (datetime.now() - self.last_llm_time).total_seconds() / 60
                    next_llm_minutes = max(0, 15 - elapsed_minutes)
                
                print(f"\n⏰ Next check in {self.check_interval} seconds | 🧠 Next LLM analysis in {next_llm_minutes:.1f} minutes")
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

async def main():
    """Main function"""
    print("🧠 AI-POWERED POSITION MONITORING SYSTEM")
    print("=" * 70)
    print("Enhanced Features:")
    print("✅ Kiểm tra vị thế định kỳ mỗi 60 giây")
    print("✅ 🧠 LLM Intelligence mỗi 15 phút")
    print("✅ Phân tích market context thông minh")
    print("✅ Risk management adaptive với LLM")
    print("✅ Đóng lệnh khẩn cấp khi mất quá -5%")
    print("✅ Gợi ý chốt lời với AI insights")
    print("✅ Fallback to rules khi LLM không available")
    print("✅ Lưu log tất cả action")
    print()
    
    # Use principal ID from database
    user_principal_id = "ok7jr-d6ktf-idahj-ucbcb-pg5tt-2ayc4-kjkjm-xm6qd-h4uxv-vbnrz-bqe"
    
    # Initialize monitor with database keys
    monitor = PositionMonitor(user_principal_id, testnet=True)
    
    try:
        # Start monitoring
        await monitor.monitor_loop()
    except Exception as e:
        print(f"❌ Monitor error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
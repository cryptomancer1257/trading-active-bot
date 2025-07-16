"""
Email Bot Example
Demonstrates how to integrate email notifications into your trading bot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot_sdk import CustomBot, Action
from email_tasks import notify_trade_async, notify_signal_async, notify_error_async
import logging

logger = logging.getLogger(__name__)

class EmailNotificationBot(CustomBot):
    """
    Example bot that demonstrates email notification integration
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        self.bot_name = "Email Notification Demo Bot"
        self.last_signal = None
        self.trade_count = 0
        
    def analyze_market(self, market_data):
        """
        Analyze market data and generate trading signals with email notifications
        """
        try:
            # Get current price
            current_price = market_data.get('current_price', 0)
            symbol = market_data.get('symbol', 'BTC/USDT')
            
            # Simple moving average crossover logic
            if len(market_data.get('prices', [])) < 20:
                return Action.HOLD, {"message": "Insufficient data for analysis"}
            
            prices = market_data['prices']
            short_ma = sum(prices[-5:]) / 5  # 5-period MA
            long_ma = sum(prices[-20:]) / 20  # 20-period MA
            
            # Generate signal
            signal_data = {
                "symbol": symbol,
                "current_price": str(current_price),
                "short_ma": str(short_ma),
                "long_ma": str(long_ma),
                "confidence": "0",
                "message": ""
            }
            
            if short_ma > long_ma * 1.01:  # Buy signal
                signal_data.update({
                    "signal_type": "BUY",
                    "confidence": "75",
                    "message": f"Short MA ({short_ma:.2f}) crossed above Long MA ({long_ma:.2f})",
                    "entry_price": str(current_price * 0.999),  # Slightly below current
                    "stop_loss": str(current_price * 0.98),     # 2% stop loss
                    "take_profit": str(current_price * 1.04)    # 4% take profit
                })
                
                # Send signal notification
                self._send_signal_notification(signal_data)
                
                return Action.BUY, signal_data
                
            elif short_ma < long_ma * 0.99:  # Sell signal
                signal_data.update({
                    "signal_type": "SELL",
                    "confidence": "75",
                    "message": f"Short MA ({short_ma:.2f}) crossed below Long MA ({long_ma:.2f})",
                    "entry_price": str(current_price * 1.001),  # Slightly above current
                    "stop_loss": str(current_price * 1.02),     # 2% stop loss
                    "take_profit": str(current_price * 0.96)    # 4% take profit
                })
                
                # Send signal notification
                self._send_signal_notification(signal_data)
                
                return Action.SELL, signal_data
            
            else:  # Hold signal
                signal_data.update({
                    "signal_type": "HOLD",
                    "confidence": "50",
                    "message": f"No clear trend. Short MA: {short_ma:.2f}, Long MA: {long_ma:.2f}"
                })
                
                # Only send HOLD signals occasionally to avoid spam
                if self.last_signal != "HOLD":
                    self._send_signal_notification(signal_data)
                
                return Action.HOLD, signal_data
                
        except Exception as e:
            # Send error notification
            error_data = {
                "error_type": "ANALYSIS_ERROR",
                "message": f"Error in market analysis: {str(e)}",
                "details": f"Market data: {market_data}"
            }
            
            self._send_error_notification(error_data)
            
            logger.error(f"Error in market analysis: {e}")
            return Action.HOLD, {"message": f"Analysis error: {str(e)}"}
    
    def execute_trade(self, action, market_data, trade_params):
        """
        Execute trade with email notification
        """
        try:
            current_price = market_data.get('current_price', 0)
            symbol = market_data.get('symbol', 'BTC/USDT')
            
            # Simulate trade execution
            if action == Action.BUY:
                # Simulate buy trade
                quantity = trade_params.get('quantity', '0.001')
                trade_data = {
                    "side": "BUY",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": str(current_price),
                    "type": "MARKET",
                    "trade_id": f"TRD_{self.trade_count + 1}",
                    "timestamp": self._get_current_time()
                }
                
                self.trade_count += 1
                
                # Send trade notification
                self._send_trade_notification(trade_data)
                
                return {
                    "success": True,
                    "trade_id": trade_data["trade_id"],
                    "message": f"Buy order executed: {quantity} {symbol} at ${current_price}"
                }
                
            elif action == Action.SELL:
                # Simulate sell trade
                quantity = trade_params.get('quantity', '0.001')
                trade_data = {
                    "side": "SELL",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": str(current_price),
                    "type": "MARKET",
                    "trade_id": f"TRD_{self.trade_count + 1}",
                    "timestamp": self._get_current_time(),
                    "pnl": "+25.50"  # Simulated profit
                }
                
                self.trade_count += 1
                
                # Send trade notification
                self._send_trade_notification(trade_data)
                
                return {
                    "success": True,
                    "trade_id": trade_data["trade_id"],
                    "message": f"Sell order executed: {quantity} {symbol} at ${current_price}"
                }
            
            else:
                return {
                    "success": True,
                    "message": "No trade executed (HOLD signal)"
                }
                
        except Exception as e:
            # Send error notification
            error_data = {
                "error_type": "TRADE_ERROR",
                "message": f"Error executing trade: {str(e)}",
                "details": f"Action: {action}, Market: {market_data}, Params: {trade_params}"
            }
            
            self._send_error_notification(error_data)
            
            logger.error(f"Error executing trade: {e}")
            return {
                "success": False,
                "message": f"Trade execution failed: {str(e)}"
            }
    
    def _send_trade_notification(self, trade_data):
        """Send trade notification email"""
        try:
            user_email = self.config.get('user_email')
            subscription_id = self.config.get('subscription_id', 0)
            is_testnet = self.config.get('is_testnet', True)
            
            if user_email:
                notify_trade_async(
                    user_email=user_email,
                    subscription_id=subscription_id,
                    bot_name=self.bot_name,
                    trade_data=trade_data,
                    is_testnet=is_testnet
                )
                logger.info(f"Trade notification sent to {user_email}")
            else:
                logger.warning("No user email configured, skipping trade notification")
                
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")
    
    def _send_signal_notification(self, signal_data):
        """Send signal notification email"""
        try:
            user_email = self.config.get('user_email')
            subscription_id = self.config.get('subscription_id', 0)
            is_testnet = self.config.get('is_testnet', True)
            
            if user_email:
                notify_signal_async(
                    user_email=user_email,
                    subscription_id=subscription_id,
                    bot_name=self.bot_name,
                    signal_data=signal_data,
                    is_testnet=is_testnet
                )
                logger.info(f"Signal notification sent to {user_email}")
                
                # Update last signal to avoid spam
                self.last_signal = signal_data.get('signal_type')
            else:
                logger.warning("No user email configured, skipping signal notification")
                
        except Exception as e:
            logger.error(f"Error sending signal notification: {e}")
    
    def _send_error_notification(self, error_data):
        """Send error notification email"""
        try:
            user_email = self.config.get('user_email')
            subscription_id = self.config.get('subscription_id', 0)
            is_testnet = self.config.get('is_testnet', True)
            
            if user_email:
                notify_error_async(
                    user_email=user_email,
                    subscription_id=subscription_id,
                    bot_name=self.bot_name,
                    error_data=error_data,
                    is_testnet=is_testnet
                )
                logger.info(f"Error notification sent to {user_email}")
            else:
                logger.warning("No user email configured, skipping error notification")
                
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
    
    def _get_current_time(self):
        """Get current time formatted"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Example usage
if __name__ == "__main__":
    # Bot configuration
    config = {
        'user_email': 'user@example.com',
        'subscription_id': 123,
        'is_testnet': True,
        'initial_balance': 1000.0,
        'max_position_size': 0.1
    }
    
    # Create bot instance
    bot = EmailNotificationBot(config)
    
    # Sample market data
    market_data = {
        'symbol': 'BTC/USDT',
        'current_price': 45000.00,
        'prices': [44000, 44200, 44500, 44800, 45000, 45200, 45100, 44900, 45000] * 3  # 27 prices
    }
    
    print("🤖 Email Notification Bot Demo")
    print("=" * 40)
    
    # Analyze market
    action, analysis = bot.analyze_market(market_data)
    print(f"📊 Analysis Result: {action}")
    print(f"📋 Details: {analysis}")
    
    # Execute trade if needed
    if action != Action.HOLD:
        trade_params = {'quantity': '0.001'}
        result = bot.execute_trade(action, market_data, trade_params)
        print(f"📈 Trade Result: {result}")
    
    print("\n📧 Email notifications have been queued!")
    print("Check your email in a few seconds for notifications.") 
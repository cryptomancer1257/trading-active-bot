"""
Seed script to populate database with sample bots and trading algorithms
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models
import schemas
from security import get_password_hash

def create_sample_data():
    """Create sample users, categories, and bots"""
    db = SessionLocal()
    
    try:
        # Clear existing data (optional - comment out if you want to keep existing data)
        # db.query(models.Bot).delete()
        # db.query(models.BotCategory).delete()
        # db.query(models.User).delete()
        
        # Create sample users (developers)
        users_data = [
            {
                "email": "john.doe@example.com",
                "hashed_password": get_password_hash("password123"),
                "role": models.UserRole.DEVELOPER,
                "developer_name": "John Doe",
                "developer_bio": "Experienced algorithmic trader specializing in technical analysis",
                "is_active": True
            },
            {
                "email": "alice.smith@example.com", 
                "hashed_password": get_password_hash("password123"),
                "role": models.UserRole.DEVELOPER,
                "developer_name": "Alice Smith",
                "developer_bio": "Machine Learning engineer focused on crypto trading strategies",
                "is_active": True
            },
            {
                "email": "bob.wilson@example.com",
                "hashed_password": get_password_hash("password123"),
                "role": models.UserRole.DEVELOPER,
                "developer_name": "Bob Wilson", 
                "developer_bio": "Quantitative analyst with 5+ years experience in forex and crypto",
                "is_active": True
            }
        ]
        
        created_users = []
        for user_data in users_data:
            # Check if user already exists
            existing_user = db.query(models.User).filter(models.User.email == user_data["email"]).first()
            if not existing_user:
                user = models.User(**user_data)
                db.add(user)
                db.flush()  # Get the ID
                created_users.append(user)
                print(f"Created user: {user.developer_name}")
            else:
                created_users.append(existing_user)
                print(f"User already exists: {existing_user.developer_name}")
        
        # Create bot categories
        categories_data = [
            {"name": "Technical Analysis", "description": "Bots using traditional technical indicators"},
            {"name": "Arbitrage", "description": "Bots exploiting price differences across exchanges"},
            {"name": "Market Making", "description": "Bots providing liquidity to the market"},
            {"name": "Trend Following", "description": "Bots that follow market trends"},
            {"name": "Mean Reversion", "description": "Bots that trade on price reversals"},
            {"name": "Machine Learning", "description": "AI-powered trading bots"}
        ]
        
        created_categories = []
        for cat_data in categories_data:
            existing_cat = db.query(models.BotCategory).filter(models.BotCategory.name == cat_data["name"]).first()
            if not existing_cat:
                category = models.BotCategory(**cat_data)
                db.add(category)
                db.flush()
                created_categories.append(category)
                print(f"Created category: {category.name}")
            else:
                created_categories.append(existing_cat)
        
        # Sample bot codes
        bot_codes = {
            "golden_cross": '''
"""
Golden Cross Trading Bot
Buys when 50-day MA crosses above 200-day MA, sells when opposite occurs.
"""

from bot_sdk.CustomBot import CustomBot
from bot_sdk.Action import Action
import pandas as pd
import numpy as np

class GoldenCrossBot(CustomBot):
    def __init__(self, config):
        super().__init__(config)
        self.short_window = config.get('short_window', 50)
        self.long_window = config.get('long_window', 200)
    
    def execute_algorithm(self, data, current_position, balance):
        """
        Golden Cross Strategy Implementation
        """
        if len(data) < self.long_window:
            return Action.HOLD
        
        # Calculate moving averages
        data['ma_short'] = data['close'].rolling(window=self.short_window).mean()
        data['ma_long'] = data['close'].rolling(window=self.long_window).mean()
        
        # Get current and previous values
        current_short_ma = data['ma_short'].iloc[-1]
        current_long_ma = data['ma_long'].iloc[-1]
        prev_short_ma = data['ma_short'].iloc[-2]
        prev_long_ma = data['ma_long'].iloc[-2]
        
        # Golden Cross: short MA crosses above long MA
        if (prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma):
            if current_position == 0:
                return Action.BUY
        
        # Death Cross: short MA crosses below long MA
        elif (prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma):
            if current_position > 0:
                return Action.SELL
        
        return Action.HOLD
''',
            "rsi_strategy": '''
"""
RSI Mean Reversion Bot
Buys when RSI < 30 (oversold), sells when RSI > 70 (overbought).
"""

from bot_sdk.CustomBot import CustomBot
from bot_sdk.Action import Action
import pandas as pd
import numpy as np

class RSIBot(CustomBot):
    def __init__(self, config):
        super().__init__(config)
        self.rsi_period = config.get('rsi_period', 14)
        self.oversold_level = config.get('oversold_level', 30)
        self.overbought_level = config.get('overbought_level', 70)
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def execute_algorithm(self, data, current_position, balance):
        """
        RSI Mean Reversion Strategy
        """
        if len(data) < self.rsi_period + 1:
            return Action.HOLD
        
        # Calculate RSI
        data['rsi'] = self.calculate_rsi(data['close'], self.rsi_period)
        current_rsi = data['rsi'].iloc[-1]
        
        # Buy signal: RSI oversold
        if current_rsi < self.oversold_level and current_position == 0:
            return Action.BUY
        
        # Sell signal: RSI overbought
        elif current_rsi > self.overbought_level and current_position > 0:
            return Action.SELL
        
        return Action.HOLD
''',
            "macd_strategy": '''
"""
MACD Trend Following Bot
Uses MACD crossover signals for entry and exit.
"""

from bot_sdk.CustomBot import CustomBot
from bot_sdk.Action import Action
import pandas as pd
import numpy as np

class MACDBot(CustomBot):
    def __init__(self, config):
        super().__init__(config)
        self.fast_period = config.get('fast_period', 12)
        self.slow_period = config.get('slow_period', 26)
        self.signal_period = config.get('signal_period', 9)
    
    def calculate_macd(self, prices):
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=self.fast_period).mean()
        ema_slow = prices.ewm(span=self.slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def execute_algorithm(self, data, current_position, balance):
        """
        MACD Crossover Strategy
        """
        if len(data) < self.slow_period + self.signal_period:
            return Action.HOLD
        
        # Calculate MACD
        macd_line, signal_line, histogram = self.calculate_macd(data['close'])
        
        # Current and previous values
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]
        
        # Buy signal: MACD crosses above signal line
        if (prev_macd <= prev_signal and current_macd > current_signal):
            if current_position == 0:
                return Action.BUY
        
        # Sell signal: MACD crosses below signal line
        elif (prev_macd >= prev_signal and current_macd < current_signal):
            if current_position > 0:
                return Action.SELL
        
        return Action.HOLD
''',
            "bollinger_bands": '''
"""
Bollinger Bands Mean Reversion Bot
Buys when price touches lower band, sells when price touches upper band.
"""

from bot_sdk.CustomBot import CustomBot
from bot_sdk.Action import Action
import pandas as pd
import numpy as np

class BollingerBandsBot(CustomBot):
    def __init__(self, config):
        super().__init__(config)
        self.period = config.get('period', 20)
        self.std_dev = config.get('std_dev', 2)
    
    def calculate_bollinger_bands(self, prices):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=self.period).mean()
        std = prices.rolling(window=self.period).std()
        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)
        return upper_band, sma, lower_band
    
    def execute_algorithm(self, data, current_position, balance):
        """
        Bollinger Bands Mean Reversion Strategy
        """
        if len(data) < self.period:
            return Action.HOLD
        
        # Calculate Bollinger Bands
        upper_band, middle_band, lower_band = self.calculate_bollinger_bands(data['close'])
        
        current_price = data['close'].iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        # Buy signal: price touches lower band
        if current_price <= current_lower and current_position == 0:
            return Action.BUY
        
        # Sell signal: price touches upper band
        elif current_price >= current_upper and current_position > 0:
            return Action.SELL
        
        return Action.HOLD
'''
        }
        
        # Create sample bots
        bots_data = [
            {
                "name": "Golden Cross Strategy",
                "description": "Classic trend-following strategy using 50/200 day moving average crossover. Ideal for catching major market trends with reduced false signals.",
                "developer_id": created_users[0].id,
                "category_id": created_categories[0].id,  # Technical Analysis
                "status": models.BotStatus.APPROVED,
                "bot_type": "TECHNICAL",
                "price_per_month": Decimal('29.99'),
                "is_free": False,
                "code_path": "bots/golden_cross_bot.py",
                "version": "1.2.0",
                "total_subscribers": 45,
                "average_rating": 4.2,
                "total_reviews": 12,
                "approved_at": datetime.utcnow() - timedelta(days=30),
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "short_window": {"type": "integer", "minimum": 10, "maximum": 100, "default": 50},
                        "long_window": {"type": "integer", "minimum": 100, "maximum": 300, "default": 200}
                    }
                },
                "default_config": {
                    "short_window": 50,
                    "long_window": 200
                }
            },
            {
                "name": "RSI Mean Reversion",
                "description": "Contrarian strategy using RSI indicator to identify oversold/overbought conditions. Perfect for range-bound markets.",
                "developer_id": created_users[0].id,
                "category_id": created_categories[4].id,  # Mean Reversion
                "status": models.BotStatus.APPROVED,
                "bot_type": "TECHNICAL",
                "price_per_month": Decimal('19.99'),
                "is_free": False,
                "code_path": "bots/rsi_strategy_bot.py",
                "version": "1.1.0",
                "total_subscribers": 78,
                "average_rating": 4.5,
                "total_reviews": 23,
                "approved_at": datetime.utcnow() - timedelta(days=25),
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "rsi_period": {"type": "integer", "minimum": 7, "maximum": 21, "default": 14},
                        "oversold_level": {"type": "number", "minimum": 20, "maximum": 35, "default": 30},
                        "overbought_level": {"type": "number", "minimum": 65, "maximum": 80, "default": 70}
                    }
                },
                "default_config": {
                    "rsi_period": 14,
                    "oversold_level": 30,
                    "overbought_level": 70
                }
            },
            {
                "name": "MACD Trend Follower",
                "description": "Advanced trend-following bot using MACD crossover signals. Excellent for momentum trading in trending markets.",
                "developer_id": created_users[1].id,
                "category_id": created_categories[3].id,  # Trend Following
                "status": models.BotStatus.APPROVED,
                "bot_type": "TECHNICAL",
                "price_per_month": Decimal('39.99'),
                "is_free": False,
                "code_path": "bots/macd_strategy_bot.py",
                "version": "2.0.0",
                "total_subscribers": 32,
                "average_rating": 4.0,
                "total_reviews": 8,
                "approved_at": datetime.utcnow() - timedelta(days=15),
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "fast_period": {"type": "integer", "minimum": 8, "maximum": 16, "default": 12},
                        "slow_period": {"type": "integer", "minimum": 20, "maximum": 35, "default": 26},
                        "signal_period": {"type": "integer", "minimum": 7, "maximum": 12, "default": 9}
                    }
                },
                "default_config": {
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                }
            },
            {
                "name": "Bollinger Bands Scalper",
                "description": "High-frequency mean reversion strategy using Bollinger Bands. Designed for quick profits in volatile markets.",
                "developer_id": created_users[1].id,
                "category_id": created_categories[4].id,  # Mean Reversion
                "status": models.BotStatus.APPROVED,
                "bot_type": "TECHNICAL",
                "price_per_month": Decimal('0.00'),
                "is_free": True,
                "code_path": "bots/bollinger_bands_bot.py",
                "version": "1.0.0",
                "total_subscribers": 156,
                "average_rating": 3.8,
                "total_reviews": 34,
                "approved_at": datetime.utcnow() - timedelta(days=10),
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "period": {"type": "integer", "minimum": 15, "maximum": 30, "default": 20},
                        "std_dev": {"type": "number", "minimum": 1.5, "maximum": 2.5, "default": 2.0}
                    }
                },
                "default_config": {
                    "period": 20,
                    "std_dev": 2.0
                }
            },
            {
                "name": "Grid Trading Bot",
                "description": "Automated grid trading system that places buy and sell orders at predetermined price levels. Works best in sideways markets.",
                "developer_id": created_users[2].id,
                "category_id": created_categories[2].id,  # Market Making
                "status": models.BotStatus.APPROVED,
                "bot_type": "TECHNICAL",
                "price_per_month": Decimal('49.99'),
                "is_free": False,
                "code_path": "bots/grid_trading_bot.py",
                "version": "1.3.0",
                "total_subscribers": 67,
                "average_rating": 4.3,
                "total_reviews": 18,
                "approved_at": datetime.utcnow() - timedelta(days=20),
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "grid_size": {"type": "number", "minimum": 0.001, "maximum": 0.05, "default": 0.01},
                        "num_grids": {"type": "integer", "minimum": 5, "maximum": 20, "default": 10}
                    }
                },
                "default_config": {
                    "grid_size": 0.01,
                    "num_grids": 10
                }
            },
            {
                "name": "Simple Buy & Hold",
                "description": "Basic dollar-cost averaging strategy. Automatically buys at regular intervals regardless of price. Perfect for beginners.",
                "developer_id": created_users[2].id,
                "category_id": created_categories[0].id,  # Technical Analysis
                "status": models.BotStatus.APPROVED,
                "bot_type": "TECHNICAL",
                "price_per_month": Decimal('0.00'),
                "is_free": True,
                "code_path": "bots/dca_bot.py",
                "version": "1.0.0",
                "total_subscribers": 234,
                "average_rating": 4.1,
                "total_reviews": 56,
                "approved_at": datetime.utcnow() - timedelta(days=5),
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "buy_interval_hours": {"type": "integer", "minimum": 1, "maximum": 168, "default": 24},
                        "buy_amount_usd": {"type": "number", "minimum": 10, "maximum": 1000, "default": 50}
                    }
                },
                "default_config": {
                    "buy_interval_hours": 24,
                    "buy_amount_usd": 50
                }
            }
        ]
        
        created_bots = []
        for bot_data in bots_data:
            existing_bot = db.query(models.Bot).filter(models.Bot.name == bot_data["name"]).first()
            if not existing_bot:
                bot = models.Bot(**bot_data)
                db.add(bot)
                db.flush()
                created_bots.append(bot)
                print(f"Created bot: {bot.name}")
            else:
                created_bots.append(existing_bot)
                print(f"Bot already exists: {existing_bot.name}")
        
        # Upload bot codes to S3
        from s3_manager import S3Manager
        s3_manager = S3Manager()
        
        # Save sample bot codes to S3
        bot_files = [
            ("golden_cross_bot.py", bot_codes["golden_cross"], created_bots[0].id),
            ("rsi_strategy_bot.py", bot_codes["rsi_strategy"], created_bots[1].id),
            ("macd_strategy_bot.py", bot_codes["macd_strategy"], created_bots[2].id),
            ("bollinger_bands_bot.py", bot_codes["bollinger_bands"], created_bots[3].id)
        ]
        
        for i, (filename, code, bot_id) in enumerate(bot_files):
            if i < len(created_bots):
                try:
                    # Upload bot code to S3
                    s3_response = s3_manager.upload_bot_code(
                        bot_id=bot_id,
                        code_content=code,
                        filename=filename,
                        version="1.0.0"
                    )
                    
                    # Update bot's code_path in database (get s3_key from response)
                    s3_key = s3_response.get('s3_key', '') if isinstance(s3_response, dict) else str(s3_response)
                    created_bots[i].code_path = s3_key
                    print(f"Uploaded bot code to S3: {s3_key}")
                    
                except Exception as e:
                    print(f"⚠️ Warning: Failed to upload {filename} to S3: {e}")
                    # Fallback to local storage
                    import os
                    bots_dir = "local_bot_storage"
                    if not os.path.exists(bots_dir):
                        os.makedirs(bots_dir)
                    filepath = os.path.join(bots_dir, filename)
                    with open(filepath, 'w') as f:
                        f.write(code)
                    created_bots[i].code_path = filepath
                    print(f"Saved bot code locally: {filepath}")
        
        # Commit all changes
        db.commit()
        print("✅ Sample data created successfully!")
        print(f"Created {len(created_users)} users, {len(created_categories)} categories, and {len(created_bots)} bots")
        
        return {
            "users": len(created_users),
            "categories": len(created_categories), 
            "bots": len(created_bots)
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating sample data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creating sample data for Bot Marketplace...")
    
    # Create tables if they don't exist
    models.Base.metadata.create_all(bind=engine)
    
    # Create sample data
    result = create_sample_data()
    
    print("🎉 Done! You can now start the API server and see the sample bots.")
    print("Sample developer accounts:")
    print("- john.doe@example.com / password123")
    print("- alice.smith@example.com / password123") 
    print("- bob.wilson@example.com / password123") 
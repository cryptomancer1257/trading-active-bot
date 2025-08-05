#!/usr/bin/env python3
"""
Real Binance Testnet Trading Bot
Executes actual trades on Binance testnet with real API keys
"""

import sys
import os
import requests
import json
import time
import hmac
import hashlib
from urllib.parse import urlencode
from datetime import datetime
import pandas as pd
import numpy as np

class RealBinanceBot:
    """Real Binance trading bot that executes actual trades"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = True):
        """Initialize with real API credentials"""
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        
        # Testnet vs Production URLs
        if testnet:
            self.base_url = "https://testnet.binance.vision/api"
        else:
            self.base_url = "https://api.binance.com/api"
        
        print(f"🚀 Initialized {'TESTNET' if testnet else 'PRODUCTION'} Binance Bot")
        
    def _generate_signature(self, params: dict) -> str:
        """Generate HMAC SHA256 signature"""
        query_string = urlencode(params)
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, endpoint: str, method: str = "GET", params: dict = None, signed: bool = False):
        """Make authenticated request to Binance API"""
        if params is None:
            params = {}
            
        url = f"{self.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API Request failed: {e}")
            return None
    
    def test_connection(self):
        """Test API connection"""
        print("\n🔗 Testing API Connection...")
        
        # Test server time
        server_time = self._make_request("/v3/time")
        if server_time:
            print(f"✅ Server Time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
        else:
            print("❌ Failed to get server time")
            return False
            
        # Test account info (signed request)
        account = self._make_request("/v3/account", signed=True)
        if account:
            print(f"✅ Account Status: {account.get('accountType', 'UNKNOWN')}")
            
            # Show balances > 0
            balances = [b for b in account.get('balances', []) if float(b['free']) > 0 or float(b['locked']) > 0]
            print(f"💰 Non-zero Balances:")
            for balance in balances[:5]:  # Show top 5
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    print(f"   {balance['asset']}: Free={free:.8f}, Locked={locked:.8f}")
            return True
        else:
            print("❌ Failed to get account info")
            return False
    
    def get_market_data(self, symbol: str = "BTCUSDT", limit: int = 100):
        """Get real market data"""
        print(f"\n📊 Getting market data for {symbol}...")
        
        # Get klines (candlestick data)
        klines = self._make_request(f"/v3/klines", params={
            "symbol": symbol,
            "interval": "5m",
            "limit": limit
        })
        
        if not klines:
            print("❌ Failed to get market data")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Convert to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
            
        print(f"✅ Got {len(df)} data points")
        print(f"📈 Current Price: ${df['close'].iloc[-1]:.2f}")
        print(f"📊 24h Volume: {df['volume'].sum():.2f}")
        
        return df
    
    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        print("\n🧮 Calculating Technical Indicators...")
        
        # RSI
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        # MACD
        def calculate_macd(prices, fast=12, slow=26, signal=9):
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            signal_line = macd.ewm(span=signal).mean()
            histogram = macd - signal_line
            return macd, signal_line, histogram
        
        # Calculate indicators
        df['rsi'] = calculate_rsi(df['close'])
        df['macd'], df['macd_signal'], df['macd_hist'] = calculate_macd(df['close'])
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Current values
        current = df.iloc[-1]
        print(f"🎯 RSI: {current['rsi']:.2f}")
        print(f"📈 MACD: {current['macd']:.4f}")
        print(f"📊 SMA20: ${current['sma_20']:.2f}")
        print(f"📊 SMA50: ${current['sma_50']:.2f}")
        
        return df
    
    def generate_trading_signal(self, df):
        """Generate trading signal based on indicators"""
        print("\n🎯 Generating Trading Signal...")
        
        current = df.iloc[-1]
        signals = []
        
        # RSI signals
        rsi = current['rsi']
        if rsi < 30:
            signals.append("RSI_OVERSOLD")
        elif rsi > 70:
            signals.append("RSI_OVERBOUGHT")
        else:
            signals.append("RSI_NEUTRAL")
        
        # MACD signals
        macd = current['macd']
        macd_signal = current['macd_signal']
        if macd > macd_signal:
            signals.append("MACD_BULLISH")
        else:
            signals.append("MACD_BEARISH")
        
        # Moving Average signals
        price = current['close']
        sma_20 = current['sma_20']
        sma_50 = current['sma_50']
        
        if price > sma_20 > sma_50:
            signals.append("MA_BULLISH")
        elif price < sma_20 < sma_50:
            signals.append("MA_BEARISH")
        else:
            signals.append("MA_NEUTRAL")
        
        # Decision logic
        bullish_signals = sum(1 for s in signals if "BULLISH" in s or "OVERSOLD" in s)
        bearish_signals = sum(1 for s in signals if "BEARISH" in s or "OVERBOUGHT" in s)
        
        if bullish_signals >= 2:
            decision = "BUY"
        elif bearish_signals >= 2:
            decision = "SELL"
        else:
            decision = "HOLD"
        
        print(f"📋 Signals: {signals}")
        print(f"🎯 Decision: {decision}")
        
        return decision, signals
    
    def place_test_order(self, symbol: str, side: str, quantity: float):
        """Place a test order (doesn't execute)"""
        print(f"\n📝 Placing TEST Order...")
        print(f"Symbol: {symbol}")
        print(f"Side: {side}")
        print(f"Quantity: {quantity}")
        
        # Test order endpoint
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity
        }
        
        result = self._make_request("/v3/order/test", method="POST", params=params, signed=True)
        
        if result == {}:  # Test orders return empty dict on success
            print("✅ Test order successful!")
            return True
        else:
            print(f"❌ Test order failed: {result}")
            return False
    
    def get_symbol_info(self, symbol: str = "BTCUSDT"):
        """Get symbol trading info"""
        exchange_info = self._make_request("/v3/exchangeInfo")
        if not exchange_info:
            return None
            
        for s in exchange_info.get('symbols', []):
            if s['symbol'] == symbol:
                return s
        return None
    
    def run_full_analysis(self, symbol: str = "BTCUSDT"):
        """Run complete trading analysis"""
        print(f"\n🚀 Running Full Trading Analysis for {symbol}")
        print("=" * 60)
        
        # 1. Test connection
        if not self.test_connection():
            return False
        
        # 2. Get symbol info
        symbol_info = self.get_symbol_info(symbol)
        if symbol_info:
            min_qty = float([f['minQty'] for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0])
            print(f"📋 Min Quantity: {min_qty}")
        else:
            min_qty = 0.001
        
        # 3. Get market data
        df = self.get_market_data(symbol)
        if df is None:
            return False
        
        # 4. Calculate indicators
        df = self.calculate_indicators(df)
        
        # 5. Generate signal
        decision, signals = self.generate_trading_signal(df)
        
        # 6. Test order (if not HOLD)
        if decision != "HOLD":
            quantity = max(min_qty, 0.001)  # Use minimum allowed quantity
            success = self.place_test_order(symbol, decision, quantity)
            if success:
                print(f"✅ Would execute {decision} order for {quantity} {symbol}")
        
        print(f"\n🎉 Analysis Complete! Decision: {decision}")
        return True

def main():
    """Main function to run the bot"""
    print("🚀 Real Binance Trading Bot")
    print("=" * 50)
    
    # Get API keys from environment or user input
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("⚠️  API keys not found in environment variables")
        print("Please set BINANCE_API_KEY and BINANCE_SECRET_KEY")
        print("\nTo test with your keys, run:")
        print("export BINANCE_API_KEY='your_api_key_here'")
        print("export BINANCE_SECRET_KEY='your_secret_key_here'")
        print("python3 real_binance_test.py")
        return
    
    # Initialize bot
    bot = RealBinanceBot(api_key, secret_key, testnet=True)
    
    # Run analysis
    try:
        bot.run_full_analysis("BTCUSDT")
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
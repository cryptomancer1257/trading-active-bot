"""
Binance Futures Trading Bot with LLM Integration and Stop Loss
Advanced futures trading bot with LLM AI analysis, leverage, stop loss, and take profit
Uses OpenAI/Claude/Gemini for intelligent trading decisions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
import json
import hashlib
import hmac
import time
import requests
import asyncio
import redis
import os
from datetime import datetime
from dataclasses import dataclass

# from bots.bot_sdk.CustomBot import CustomBot
# from bots.bot_sdk.Action import Action
from bots.bot_sdk import CustomBot, Action
from services.llm_integration import create_llm_service
from bot_files.capital_management import CapitalManagement, RiskMetrics, PositionSizeRecommendation
from core.api_key_manager import get_bot_api_keys

logger = logging.getLogger(__name__)

@dataclass
class FuturesOrderInfo:
    """Futures order information"""
    order_id: int
    client_order_id: str
    symbol: str
    side: str
    type: str
    quantity: str
    price: str
    status: str
    executed_qty: str
    time_in_force: str = "GTC"

@dataclass
class FuturesPosition:
    """Futures position information"""
    symbol: str
    side: str
    size: str
    entry_price: str
    mark_price: str
    pnl: str
    percentage: str

class BinanceFuturesIntegration:
    """Binance Futures API Integration"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self._time_offset = 0
        self._symbol_info_cache = {}  # Cache for exchange info
        
        # Futures API endpoints
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
        
        logger.info(f"Initialized Binance Futures {'TESTNET' if testnet else 'PRODUCTION'}")
    
    def _generate_signature(self, params: dict) -> str:
        """Generate HMAC SHA256 signature"""
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False, recv_window: int = 50000):
        """Make authenticated request to Binance Futures API"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        headers = {"X-MBX-APIKEY": self.api_key}

        if signed:
            if self._time_offset == 0:
                self._sync_server_time()

            params['recvWindow'] = recv_window
            params['timestamp'] = int(time.time() * 1000) + self._time_offset
            params['signature'] = self._generate_signature(params)
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=params, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Futures API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    data = e.response.json()
                    if data.get("code") == -1021:
                        logger.warning("⏱️ Timestamp error (-1021), resyncing server time and retrying...")
                        self._sync_server_time()
                        return self._make_request(method, endpoint, params, signed, recv_window)
                except Exception:
                    pass
            logger.error(f"Futures API request failed: {e}")
            raise Exception(f"Futures API request failed: {e}")
    
    def test_connectivity(self) -> bool:
        """Test Futures API connectivity"""
        try:
            response = self._make_request("GET", "/fapi/v1/ping")
            return response == {}
        except Exception as e:
            logger.error(f"Futures connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get futures account information"""
        try:
            return self._make_request("GET", "/fapi/v2/account", signed=True)
        except Exception as e:
            logger.error(f"Failed to get futures account info: {e}")
            raise
    
    def get_position_info(self, symbol: str = None) -> List[FuturesPosition]:
        """Get position information"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            positions = self._make_request("GET", "/fapi/v2/positionRisk", params, signed=True)
            
            result = []
            for pos in positions:
                if float(pos['positionAmt']) != 0:  # Only active positions
                    result.append(FuturesPosition(
                        symbol=pos['symbol'],
                        side="LONG" if float(pos['positionAmt']) > 0 else "SHORT",
                        size=pos['positionAmt'],
                        entry_price=pos['entryPrice'],
                        mark_price=pos['markPrice'],
                        pnl=pos['unRealizedProfit'],
                        percentage=pos.get('percentage', '0')  # Handle missing percentage field
                    ))
            
            return result
        except Exception as e:
            logger.error(f"Failed to get position info: {e}")
            raise
    
    def get_positions(self):
        """Alias for get_position_info for compatibility"""
        return self.get_position_info()
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        try:
            # Try symbol price ticker first (simpler endpoint)
            params = {'symbol': symbol}
            response = self._make_request("GET", "/fapi/v1/ticker/price", params)
            return response
        except Exception as e:
            logger.error(f"Failed to get ticker price for {symbol}: {e}")
            # Fallback: try 24hr ticker
            try:
                response = self._make_request("GET", "/fapi/v1/ticker/24hr", params)
                # 24hr ticker uses 'lastPrice' instead of 'price'
                if 'lastPrice' in response:
                    response['price'] = response['lastPrice']
                return response
            except Exception as e2:
                logger.error(f"24hr ticker also failed: {e2}")
                # Final fallback: get from klines
                try:
                    klines = self.get_klines(symbol, "1m", 1)
                    if klines:
                        return {
                            'price': klines[0]['close'],
                            'symbol': symbol
                        }
                except Exception as e3:
                    logger.error(f"Klines fallback failed: {e3}")
                    pass
            raise Exception(f"All ticker methods failed for {symbol}")
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        try:
            params = {
                'symbol': symbol,
                'leverage': leverage
            }
            
            response = self._make_request("POST", "/fapi/v1/leverage", params, signed=True)
            logger.info(f"Set leverage {leverage}x for {symbol}: {response}")
            return True
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            return False
    
    def get_symbol_precision(self, symbol: str) -> dict:
        """
        Get quantity and price precision for a symbol
        Returns: {'quantityPrecision': int, 'stepSize': str, 'tickSize': str}
        """
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        
        try:
            # Get exchange info
            response = self._make_request("GET", "/fapi/v1/exchangeInfo", signed=False)
            
            # Find symbol info
            for sym_info in response.get('symbols', []):
                if sym_info['symbol'] == symbol:
                    precision_info = {
                        'quantityPrecision': sym_info['quantityPrecision'],
                        'pricePrecision': sym_info['pricePrecision'],
                        'stepSize': '0.01',  # Default
                        'tickSize': '0.01'   # Default
                    }
                    
                    # Get step size from LOT_SIZE filter
                    for filter_item in sym_info.get('filters', []):
                        if filter_item['filterType'] == 'LOT_SIZE':
                            precision_info['stepSize'] = filter_item['stepSize']
                        elif filter_item['filterType'] == 'PRICE_FILTER':
                            precision_info['tickSize'] = filter_item['tickSize']
                    
                    # Cache result
                    self._symbol_info_cache[symbol] = precision_info
                    logger.info(f"📏 {symbol} precision: {precision_info}")
                    return precision_info
            
            # Symbol not found, use defaults
            logger.warning(f"Symbol {symbol} not found in exchange info, using defaults")
            return {'quantityPrecision': 3, 'pricePrecision': 2, 'stepSize': '0.001', 'tickSize': '0.01'}
            
        except Exception as e:
            logger.error(f"Failed to get symbol precision: {e}")
            # Return safe defaults
            return {'quantityPrecision': 3, 'pricePrecision': 2, 'stepSize': '0.001', 'tickSize': '0.01'}
    
    def round_quantity(self, quantity: float, symbol: str) -> str:
        """
        Round quantity to proper precision for a symbol
        Args:
            quantity: Raw quantity as float
            symbol: Trading pair symbol (e.g., 'SOLUSDT')
        Returns:
            Properly rounded quantity as string
        """
        precision_info = self.get_symbol_precision(symbol)
        decimals = precision_info['quantityPrecision']
        step_size = float(precision_info['stepSize'])
        
        # Round to step size
        rounded_qty = round(quantity / step_size) * step_size
        
        # Format with correct decimals
        qty_str = f"{rounded_qty:.{decimals}f}"
        
        logger.debug(f"Rounded quantity: {quantity} → {qty_str} (precision={decimals}, step={step_size})")
        return qty_str
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> FuturesOrderInfo:
        """Create futures market order with proper quantity rounding"""
        try:
            # Round quantity to proper precision
            quantity_float = float(quantity)
            rounded_quantity = self.round_quantity(quantity_float, symbol)
            
            logger.info(f"📊 Creating market order: {symbol} {side} {rounded_quantity}")
            
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': rounded_quantity
            }
            
            response = self._make_request("POST", "/fapi/v1/order", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=response['orderId'],
                client_order_id=response['clientOrderId'],
                symbol=response['symbol'],
                side=response['side'],
                type=response['type'],
                quantity=response['origQty'],
                price=response.get('price', '0'),
                status=response['status'],
                executed_qty=response['executedQty']
            )
        except Exception as e:
            logger.error(f"Failed to create futures market order: {e}")
            raise
    
    def create_stop_loss_order(self, symbol: str, side: str, quantity: str, stop_price: str, 
                              reduce_only: bool = True) -> FuturesOrderInfo:
        """Create stop loss order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'STOP_MARKET',
                'quantity': quantity,
                'stopPrice': stop_price,
                'timeInForce': 'GTC'
            }
            
            if reduce_only:
                params['reduceOnly'] = 'true'
            
            response = self._make_request("POST", "/fapi/v1/order", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=response['orderId'],
                client_order_id=response['clientOrderId'],
                symbol=response['symbol'],
                side=response['side'],
                type=response['type'],
                quantity=response['origQty'],
                price=response.get('stopPrice', '0'),
                status=response['status'],
                executed_qty=response['executedQty']
            )
        except Exception as e:
            logger.error(f"Failed to create stop loss order: {e}")
            raise
    
    def create_take_profit_order(self, symbol: str, side: str, quantity: str, stop_price: str,
                                reduce_only: bool = True) -> FuturesOrderInfo:
        """Create take profit order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'TAKE_PROFIT_MARKET',
                'quantity': quantity,
                'stopPrice': stop_price,
                'timeInForce': 'GTC'
            }
            
            if reduce_only:
                params['reduceOnly'] = 'true'
            
            response = self._make_request("POST", "/fapi/v1/order", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=response['orderId'],
                client_order_id=response['clientOrderId'],
                symbol=response['symbol'],
                side=response['side'],
                type=response['type'],
                quantity=response['origQty'],
                price=response.get('stopPrice', '0'),
                status=response['status'],
                executed_qty=response['executedQty']
            )
        except Exception as e:
            logger.error(f"Failed to create take profit order: {e}")
            raise
    
    def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """Get all open orders for a symbol"""
        try:
            params = {'symbol': symbol}
            response = self._make_request("GET", "/fapi/v1/openOrders", params, signed=True)
            return response
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """Cancel a specific order"""
        try:
            params = {
                'symbol': symbol,
                'orderId': order_id
            }
            self._make_request("DELETE", "/fapi/v1/order", params, signed=True)
            logger.info(f"❌ Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def create_managed_orders(self, symbol: str, side: str, quantity: str, 
                            stop_price: str, take_profit_price: str, 
                            reduce_only: bool = True) -> Dict[str, Any]:
        """Create orders with proper management - check existing orders first"""
        try:
            # 🔍 STEP 1: Check existing orders
            existing_orders = self.get_open_orders(symbol)
            
            # Filter existing SL and TP orders for this symbol
            existing_sl = [o for o in existing_orders if o['type'] == 'STOP_MARKET' and o['side'] == side]
            existing_tp = [o for o in existing_orders if o['type'] == 'TAKE_PROFIT_MARKET' and o['side'] == side]
            
            logger.info(f"📊 Existing orders: {len(existing_sl)} SL, {len(existing_tp)} TP")
            
            # 🧹 STEP 2: Cancel excessive orders (keep max 1 SL + 2 TP)
            if len(existing_sl) > 0:
                logger.info("⚠️ Stop Loss orders already exist, cancelling old ones...")
                for order in existing_sl:
                    self.cancel_order(symbol, int(order['orderId']))
            
            if len(existing_tp) > 1:
                logger.info("⚠️ Too many Take Profit orders, cancelling old ones...")
                for order in existing_tp:
                    self.cancel_order(symbol, int(order['orderId']))
            
            # 🆕 STEP 3: Create new managed orders
            # Split quantity for partial TP strategy
            total_qty = float(quantity)
            partial_qty = total_qty * 0.5  # 50% for first TP (recover capital)
            remaining_qty = total_qty * 0.5  # 50% for second TP (profit)
            
            # Create stop loss order (full quantity)
            stop_params = {
                'symbol': symbol,
                'side': side,
                'type': 'STOP_MARKET',
                'quantity': f"{total_qty:.5f}",
                'stopPrice': stop_price,
                'timeInForce': 'GTC'
            }
            
            if reduce_only:
                stop_params['reduceOnly'] = 'true'
            
            stop_response = self._make_request("POST", "/fapi/v1/order", stop_params, signed=True)
            
            # Create first take profit order (partial - recover capital)
            tp1_price = float(take_profit_price)
            tp1_params = {
                'symbol': symbol,
                'side': side,
                'type': 'TAKE_PROFIT_MARKET',
                'quantity': f"{partial_qty:.5f}",
                'stopPrice': f"{tp1_price:.2f}",
                'timeInForce': 'GTC'
            }
            
            if reduce_only:
                tp1_params['reduceOnly'] = 'true'
            
            tp1_response = self._make_request("POST", "/fapi/v1/order", tp1_params, signed=True)
            
            # Create second take profit order (remaining - profit taking)
            tp2_price = tp1_price * 1.02  # 2% higher for profit taking
            tp2_params = {
                'symbol': symbol,
                'side': side,
                'type': 'TAKE_PROFIT_MARKET',
                'quantity': f"{remaining_qty:.5f}",
                'stopPrice': f"{tp2_price:.2f}",
                'timeInForce': 'GTC'
            }
            
            if reduce_only:
                tp2_params['reduceOnly'] = 'true'
            
            tp2_response = self._make_request("POST", "/fapi/v1/order", tp2_params, signed=True)
            
            logger.info(f"✅ Managed Orders Created:")
            logger.info(f"🛡️ Stop Loss: {stop_response['orderId']} (Full: {total_qty:.5f})")
            logger.info(f"🎯 Take Profit 1: {tp1_response['orderId']} (Partial: {partial_qty:.5f} @ ${tp1_price:.2f})")
            logger.info(f"🎯 Take Profit 2: {tp2_response['orderId']} (Profit: {remaining_qty:.5f} @ ${tp2_price:.2f})")
            
            return {
                'stop_loss_order': {
                    'order_id': stop_response['orderId'],
                    'quantity': total_qty,
                    'price': stop_price
                },
                'take_profit_orders': [
                    {
                        'order_id': tp1_response['orderId'],
                        'quantity': partial_qty,
                        'price': tp1_price,
                        'type': 'partial'
                    },
                    {
                        'order_id': tp2_response['orderId'],
                        'quantity': remaining_qty,
                        'price': tp2_price,
                        'type': 'profit'
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to create managed orders: {e}")
            raise
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100, start_time: int = None,
           end_time: int = None) -> pd.DataFrame:
        """Get futures kline data"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit,
                'startTime': start_time,
                'endTime': end_time
            }
            
            response = self._make_request("GET", "/fapi/v1/klines", params)
            
            # Convert to DataFrame
            df = pd.DataFrame(response, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to get futures klines: {e}")
            raise
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol"""
        try:
            params = {'symbol': symbol}
            response = self._make_request("DELETE", "/fapi/v1/allOpenOrders", params, signed=True)
            logger.info(f"Cancelled all orders for {symbol}: {response}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False

    def _sync_server_time(self):
        """Sync local offset with Binance server time"""
        try:
            r = requests.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            r.raise_for_status()
            server_time = int(r.json()["serverTime"])
            local_time = int(time.time() * 1000)
            self._time_offset = server_time - local_time
            logger.info(f"⏱️ Server time synced, offset={self._time_offset} ms")
        except Exception as e:
            logger.warning(f"⚠️ Failed to sync server time: {e}")
            self._time_offset = 0

class BinanceFuturesBot(CustomBot):
    """Advanced Binance Futures Trading Bot with LLM Integration and Stop Loss"""
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str] = None, user_principal_id: str = None, subscription_id: int = None):
        """Initialize Futures Trading Bot"""
        super().__init__(config, api_keys)
        
        # Store bot_id and subscription_id for LLM prompt customization
        self.bot_id = config.get('bot_id')
        self.subscription_id = subscription_id
        logger.info(f"🤖 [BOT INIT] bot_id={self.bot_id}, subscription_id={subscription_id}")
        
        # Futures specific configuration
        raw_trading_pair = config.get('trading_pair', 'BTCUSDT')
        # Normalize trading pair: remove '/' for Binance Futures API (BTC/USDT → BTCUSDT)
        self.trading_pair = raw_trading_pair.replace('/', '')
        
        # Log normalization for debugging
        if raw_trading_pair != self.trading_pair:
            logger.info(f"🔧 [BOT INIT] Normalized trading pair: '{raw_trading_pair}' → '{self.trading_pair}'")
        else:
            logger.info(f"✅ [BOT INIT] Trading pair already normalized: '{self.trading_pair}'")
        
        self.leverage = config.get('leverage', 5)  # Safer default leverage
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)  # 2% stop loss
        self.take_profit_pct = config.get('take_profit_pct', 0.04)  # 4% take profit
        self.position_size_pct = config.get('position_size_pct', 0.1)  # 10% of balance
        self.testnet = config.get('testnet', True)  # Add testnet attribute
        
        # Multi-timeframe configuration - Optimized 3 timeframes
        self.timeframes = config.get('timeframes', ['30m', '1h', '4h'])  # Optimized 3 timeframes
        self.primary_timeframe = config.get('primary_timeframe', self.timeframes[0])  # First timeframe as primary
        
        # 🔒 Redis client for distributed locking and caching
        self.redis_client = None
        try:
            import os
            redis_url = os.getenv('REDIS_URL', 'redis://redis_db:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established for LLM locking")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. LLM calls may duplicate across workers.")
            self.redis_client = None
        
        # Validate timeframes
        supported_timeframes = [
            '1m', '3m', '5m', '15m', '30m',  # Minutes
            '1h', '2h', '4h', '6h', '8h', '12h',  # Hours  
            '1d', '3d', '1w', '1M'  # Days, weeks, months
        ]
        
        # Filter out unsupported timeframes
        valid_timeframes = [tf for tf in self.timeframes if tf in supported_timeframes]
        if len(valid_timeframes) != len(self.timeframes):
            invalid_tfs = [tf for tf in self.timeframes if tf not in supported_timeframes]
            logger.warning(f"Unsupported timeframes removed: {invalid_tfs}")
            logger.info(f"Supported timeframes: {supported_timeframes}")
        
        self.timeframes = valid_timeframes if valid_timeframes else ['1h']  # Fallback to 1h
        
        # Ensure primary timeframe is valid
        if self.primary_timeframe not in self.timeframes:
            self.primary_timeframe = self.timeframes[0]
            logger.warning(f"Primary timeframe adjusted to: {self.primary_timeframe}")
        
        # LLM configuration
        self.llm_model = config.get('llm_model', 'openai')  # Default to OpenAI
        self.use_llm_analysis = config.get('use_llm_analysis', True)  # Enable LLM by default
        
        # Technical indicators config (kept for fallback)
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        
        # Initialize futures client - ONLY database lookup for exchange keys
        if not user_principal_id:
            raise ValueError("user_principal_id is required - all exchange API keys must come from database")
        
        # Store user principal ID for this bot instance
        self.user_principal_id = user_principal_id
        logger.info(f"Bot initialized for principal ID: {self.user_principal_id}")
        
        # Get API keys from database by user principal ID
        logger.info(f"Loading exchange API keys for principal ID: {user_principal_id}")
        db_credentials = get_bot_api_keys(
            user_principal_id=user_principal_id,
            exchange="BINANCE",
            is_testnet=config.get('testnet', True),
            subscription_id=subscription_id
        )

        if not db_credentials:
            raise ValueError(f"No exchange API credentials found in database for principal ID: {user_principal_id}. Please store your Binance API keys in the database first.")

        client_api_key = db_credentials['api_key']
        client_api_secret = db_credentials['api_secret']
        client_testnet = db_credentials['testnet']
        
        logger.info(f"✅ Loaded encrypted Binance API keys from database for principal ID: {user_principal_id}")
        
        self.futures_client = BinanceFuturesIntegration(
            api_key=client_api_key,
            api_secret=client_api_secret,
            testnet=client_testnet
        )

        # Try to get mainnet credentials (optional for TRIAL users)
        db_credentials_mainnet = get_bot_api_keys(
            user_principal_id=user_principal_id,
            exchange="BINANCE",
            is_testnet=False,
            subscription_id=subscription_id
        )

        if db_credentials_mainnet:
            client_api_key_mainnet = db_credentials_mainnet.get('api_key', None)
            client_api_secret_mainnet = db_credentials_mainnet.get('api_secret', None)

            self.futures_client_mainnet = BinanceFuturesIntegration(
                api_key=client_api_key_mainnet,
                api_secret=client_api_secret_mainnet,
                testnet=False
            )
            logger.info("✅ Mainnet client initialized with user credentials")
        else:
            # ALWAYS create mainnet client for data crawling (public endpoints don't need auth)
            logger.warning("⚠️ No mainnet credentials, creating public mainnet client for data crawling only")
            self.futures_client_mainnet = BinanceFuturesIntegration(
                api_key="",  # Empty key for public endpoints
                api_secret="",
                testnet=False
            )
            logger.info("✅ Public mainnet client created for accurate market data")
        
        # Initialize LLM service - get LLM keys from api_keys or environment
        self.llm_service = None
        if self.use_llm_analysis:
            try:
                # LLM keys can come from api_keys parameter or environment variables
                import os
                
                # Get bot's preferred LLM provider and model from config (set in UI)
                preferred_provider = config.get('llm_provider')
                llm_model = config.get('llm_model')  # Specific model selected in UI
                
                # If no specific model, use provider name as model identifier
                if not llm_model and preferred_provider:
                    llm_model = preferred_provider
                    logger.info(f"ℹ️  No specific model configured, using provider: {preferred_provider}")
                
                llm_config = {
                    'openai_api_key': os.getenv('OPENAI_API_KEY'),
                    'claude_api_key': os.getenv('CLAUDE_API_KEY'),
                    'gemini_api_key': os.getenv('GEMINI_API_KEY'),
                    'openai_model': config.get('openai_model', 'gpt-4o'),
                    'claude_model': config.get('claude_model', 'claude-3-5-sonnet-20241022'),
                    'gemini_model': config.get('gemini_model', 'gemini-2.5-flash')
                }
                
                # Override with specific model if provided (from UI dropdown)
                if llm_model and preferred_provider:
                    if preferred_provider == 'openai':
                        llm_config['openai_model'] = llm_model
                    elif preferred_provider in ['anthropic', 'claude']:
                        llm_config['claude_model'] = llm_model
                    elif preferred_provider == 'gemini':
                        llm_config['gemini_model'] = llm_model
                    logger.info(f"✅ Using {preferred_provider} model: {llm_model}")
                
                self.llm_service = create_llm_service(llm_config)
                logger.info(f"LLM service initialized with model: {self.llm_model}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
                self.use_llm_analysis = False
                logger.warning("Falling back to traditional technical analysis")
        
        # Initialize Capital Management System
        capital_config = {
            'base_position_size_pct': config.get('base_position_size_pct', 0.02),  # 2% base
            'max_position_size_pct': config.get('max_position_size_pct', 0.10),   # 10% max
            'max_portfolio_exposure': config.get('max_portfolio_exposure', 0.30), # 30% total
            'max_drawdown_threshold': config.get('max_drawdown_threshold', 0.20), # 20%
            'volatility_threshold_low': config.get('volatility_threshold_low', 0.02),
            'volatility_threshold_high': config.get('volatility_threshold_high', 0.08),
            'kelly_multiplier': config.get('kelly_multiplier', 0.25),
            'min_win_rate': config.get('min_win_rate', 0.35),
            'use_llm_capital_management': config.get('use_llm_capital_management', True),
            'llm_capital_weight': config.get('llm_capital_weight', 0.40),
            'sizing_method': config.get('sizing_method', 'llm_hybrid')
        }
        
        self.capital_manager = CapitalManagement(capital_config)
        logger.info(f"Capital Management initialized - Method: {capital_config['sizing_method']}")
        
        logger.info(f"Initialized BinanceFuturesBot for {self.trading_pair} with {self.leverage}x leverage")
        logger.info(f"Timeframes: {self.timeframes} (Total: {len(self.timeframes)})")
        logger.info(f"Primary timeframe: {self.primary_timeframe}")
        logger.info(f"Analysis method: {'LLM (' + self.llm_model + ')' if self.use_llm_analysis else 'Technical Indicators'}")
    
    def _get_llm_cache_key(self, symbol: str, timeframes: List[str]) -> str:
        """Generate cache key for LLM analysis"""
        # Create unique key based on symbol and current minute (cache for 1 minute)
        current_minute = int(time.time() // 60)
        key_data = f"{symbol}:{':'.join(sorted(timeframes))}:{current_minute}"
        return f"llm_analysis:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def _get_llm_lock_key(self, symbol: str) -> str:
        """Generate lock key for LLM analysis"""
        return f"llm_lock:{symbol}"
    
    def _acquire_llm_lock(self, symbol: str, timeout: int = 300) -> bool:
        """
        Acquire distributed lock for LLM analysis to prevent duplicate calls
        Returns True if lock acquired, False if another worker is already processing
        """
        if not self.redis_client:
            return True  # No Redis, proceed without locking
            
        lock_key = self._get_llm_lock_key(symbol)
        worker_id = f"worker_{os.getpid()}_{int(time.time())}"
        
        try:
            # Try to acquire lock with expiration
            acquired = self.redis_client.set(lock_key, worker_id, nx=True, ex=timeout)
            if acquired:
                logger.info(f"🔒 LLM lock acquired by {worker_id} for {symbol}")
                return True
            else:
                current_owner = self.redis_client.get(lock_key)
                logger.info(f"⏳ LLM lock held by {current_owner} for {symbol}, skipping duplicate analysis")
                return False
        except Exception as e:
            logger.warning(f"Failed to acquire LLM lock: {e}")
            return True  # Proceed if Redis fails
    
    def _release_llm_lock(self, symbol: str):
        """Release LLM analysis lock"""
        if not self.redis_client:
            return
            
        lock_key = self._get_llm_lock_key(symbol)
        try:
            self.redis_client.delete(lock_key)
            logger.debug(f"🔓 LLM lock released for {symbol}")
        except Exception as e:
            logger.warning(f"Failed to release LLM lock: {e}")
    
    def _get_cached_llm_result(self, symbol: str, timeframes: List[str]) -> Optional[Dict[str, Any]]:
        """Get cached LLM analysis result"""
        if not self.redis_client:
            return None
            
        cache_key = self._get_llm_cache_key(symbol, timeframes)
        try:
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                logger.info(f"📋 Using cached LLM analysis for {symbol}")
                return json.loads(cached_result)
        except Exception as e:
            logger.warning(f"Failed to get cached LLM result: {e}")
        return None
    
    def _cache_llm_result(self, symbol: str, timeframes: List[str], result: Dict[str, Any]):
        """Cache LLM analysis result for 60 seconds"""
        if not self.redis_client:
            return
            
        cache_key = self._get_llm_cache_key(symbol, timeframes)
        try:
            # Cache for 60 seconds
            self.redis_client.setex(cache_key, 60, json.dumps(result))
            logger.debug(f"💾 Cached LLM analysis for {symbol}")
        except Exception as e:
            logger.warning(f"Failed to cache LLM result: {e}")

    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """Execute futures trading algorithm"""
        try:
            logger.info(f"Executing futures algorithm for {len(data)} data points")
            
            if len(data) < 50:
                return Action(action="HOLD", value=0.0, reason="Insufficient data for futures analysis")
            
            # Convert DataFrame to historical data format for LLM
            historical_data = []
            for idx, row in data.iterrows():
                historical_data.append({
                    'timestamp': int(idx.timestamp() * 1000) if hasattr(idx, 'timestamp') else int(idx),
                    'open': float(row.get('open', 0)),
                    'high': float(row.get('high', 0)),
                    'low': float(row.get('low', 0)),
                    'close': float(row.get('close', 0)),
                    'volume': float(row.get('volume', 0))
                })
            
            # Calculate technical indicators with historical data
            analysis = self._calculate_futures_analysis(data, historical_data)
            
            # Generate signal with futures-specific logic
            return self._generate_futures_signal(analysis, data)
            
        except Exception as e:
            logger.error(f"Error in futures algorithm: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Futures algorithm error: {e}")
    
    def _calculate_futures_analysis(self, data: pd.DataFrame, historical_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate analysis for futures trading"""
        try:
            # RSI
            def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                return rsi.iloc[-1] if not rsi.empty else 50
            
            # MACD
            def calculate_macd(prices: pd.Series, fast=12, slow=26, signal=9):
                ema_fast = prices.ewm(span=fast).mean()
                ema_slow = prices.ewm(span=slow).mean()
                macd_line = ema_fast - ema_slow
                signal_line = macd_line.ewm(span=signal).mean()
                return macd_line.iloc[-1], signal_line.iloc[-1]
            
            # Calculate indicators
            rsi = calculate_rsi(data['close'], self.rsi_period)
            macd, macd_signal = calculate_macd(data['close'])
            
            # Moving averages
            sma_20 = data['close'].rolling(window=20).mean().iloc[-1]
            sma_50 = data['close'].rolling(window=50).mean().iloc[-1]
            
            # Volatility (ATR)
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=14).mean().iloc[-1]
            
            analysis = {
                'current_price': float(data['close'].iloc[-1]),
                'rsi': float(rsi),
                'rsi_oversold': bool(rsi < self.rsi_oversold),
                'rsi_overbought': bool(rsi > self.rsi_overbought),
                'macd': float(macd),
                'macd_signal': float(macd_signal),
                'macd_bullish': bool(macd > macd_signal),
                'sma_20': float(sma_20),
                'sma_50': float(sma_50),
                'trend_bullish': bool(sma_20 > sma_50),
                'atr': float(atr),
                'volatility': float(atr / data['close'].iloc[-1] * 100),
                'volume_ratio': float(data['volume'].iloc[-1] / data['volume'].rolling(20).mean().iloc[-1])
            }
            
            # Include historical data for LLM analysis if provided
            if historical_data:
                analysis['historical_data'] = historical_data
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error calculating futures analysis: {e}")
            return {'error': str(e), 'historical_data': historical_data}
    
    def _convert_data_to_llm_format(self, historical_data: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Convert historical data to LLM-friendly multi-timeframe format for futures"""
        try:
            if not historical_data:
                return {}
            
            # Clean data to ensure JSON serializable (convert any pandas objects to primitives)
            cleaned_data = []
            for item in historical_data:
                cleaned_item = {}
                for key, value in item.items():
                    if hasattr(value, 'timestamp'):  # pandas Timestamp
                        cleaned_item[key] = value.timestamp() if hasattr(value, 'timestamp') else float(value)
                    elif hasattr(value, 'isoformat'):  # datetime object
                        cleaned_item[key] = value.isoformat()
                    else:
                        cleaned_item[key] = float(value) if isinstance(value, (int, float)) else value
                cleaned_data.append(cleaned_item)
            
            # For futures, we might want to use smaller timeframes
            timeframes_data = {
                "1h": cleaned_data[-24:] if len(cleaned_data) >= 24 else cleaned_data,  # Last 24 hours
                "4h": cleaned_data[-12:] if len(cleaned_data) >= 12 else cleaned_data,  # Last 48 hours 
                "1d": cleaned_data[-7:] if len(cleaned_data) >= 7 else cleaned_data     # Last 7 days
            }
            
            return timeframes_data
            
        except Exception as e:
            logger.error(f"Error converting futures data to LLM format: {e}")
            return {}
    
    async def generate_futures_signal_with_llm(self, historical_data: List[Dict[str, Any]]) -> Action:
        """Generate futures trading signal using LLM analysis"""
        try:
            if not self.llm_service:
                logger.error("LLM service not available")
                return Action(action="HOLD", value=0.0, reason="LLM service unavailable")
            
            # Analyze data to get indicators
            analysis = self.analyze_futures_data(historical_data)
            if 'error' in analysis:
                logger.error(f"Analysis error: {analysis['error']}")
                return Action(action="HOLD", value=0.0, reason=f"Analysis error: {analysis['error']}")
            
            # Convert data to LLM format
            timeframes_data = self._convert_data_to_llm_format(historical_data)
            if not timeframes_data:
                return Action(action="HOLD", value=0.0, reason="Failed to format data for LLM")
            
            # Prepare indicators analysis - use same indicators for all timeframes
            # since this bot only has one real timeframe
            indicators_analysis = {}
            for timeframe in timeframes_data.keys():
                indicators_analysis[timeframe] = {
                    'indicators': {
                        'rsi': analysis.get('rsi', 50),
                        'macd': {
                            'macd': analysis.get('macd', 0),
                            'signal': analysis.get('macd_signal', 0),
                            'histogram': analysis.get('macd_histogram', 0)
                        },
                        'ma_fast': analysis.get('ma_fast', 0),
                        'ma_slow': analysis.get('ma_slow', 0),
                        'bollinger_bands': {
                            'upper': analysis.get('bb_upper', 0),
                            'middle': analysis.get('bb_middle', 0),
                            'lower': analysis.get('bb_lower', 0)
                        }
                    },
                    'current_price': analysis.get('current_price', 0),
                    'volume_ratio': analysis.get('volume_ratio', 1.0)
                }
            
            # Get LLM analysis with futures context
            self.trading_pair = self.trading_pair.replace('/', '')
            symbol = self.trading_pair  # e.g., "BTCUSDT"
            llm_analysis = await self.llm_service.analyze_market(
                symbol=symbol,
                timeframes_data=timeframes_data,
                indicators_analysis=indicators_analysis,  # ✅ Pass indicators to LLM
                model=self.llm_model,
                bot_id=self.bot_id  # Pass bot_id for custom prompt
            )
            
            if "error" in llm_analysis:
                logger.error(f"LLM analysis failed: {llm_analysis['error']}")
                return Action(action="HOLD", value=0.0, reason=f"LLM analysis error: {llm_analysis['error']}")
            
            # Parse LLM recommendation for futures
            if llm_analysis.get("parsed", False) and "recommendation" in llm_analysis:
                recommendation = llm_analysis["recommendation"]
                
                action = recommendation.get("action", "HOLD").upper()
                
                # Parse confidence safely (handle both "60%" and 60 formats)
                confidence_raw = recommendation.get("confidence", 0)
                try:
                    if isinstance(confidence_raw, str):
                        # Remove % sign if present and convert
                        confidence_str = confidence_raw.replace("%", "").strip()
                        confidence = float(confidence_str) / 100.0
                    else:
                        # Already a number
                        confidence = float(confidence_raw) / 100.0
                    
                    # Ensure confidence is in valid range 0-1
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse confidence '{confidence_raw}': {e}")
                    confidence = 0.0
                
                reasoning = recommendation.get("reasoning", "LLM futures analysis")
                
                # For futures, we might want to map CLOSE to SELL for existing positions
                if action == "CLOSE":
                    action = "SELL"  # Treat CLOSE as SELL for simplicity
                
                # Validate action
                if action not in ["BUY", "SELL", "HOLD"]:
                    action = "HOLD"
                    confidence = 0.0
                    reasoning = f"Invalid LLM action: {action}"
                
                # Boost confidence slightly for futures (more aggressive)
                confidence = min(confidence * 1.1, 1.0)
                
                logger.info(f"🤖 LLM: {action} ({confidence*100:.1f}%) - {reasoning[:50]}...")
                
                return Action(action=action, value=confidence, reason=f"[FUTURES] {reasoning}")
            else:
                logger.warning("LLM response could not be parsed properly")
                return Action(action="HOLD", value=0.0, reason="Unparseable LLM response")
                
        except Exception as e:
            logger.error(f"Error in LLM futures signal generation: {e}")
            return Action(action="HOLD", value=0.0, reason=f"LLM futures signal error: {e}")

    def _generate_futures_signal(self, analysis: Dict[str, Any], data: pd.DataFrame, allow_llm: bool = True) -> Action:
        """Generate futures trading signal (uses LLM if available, falls back to technical analysis)"""
        try:
            # If LLM is enabled and we have historical data, use LLM analysis
            if allow_llm and self.use_llm_analysis and self.llm_service and 'historical_data' in analysis:
                # 🔍 Step 1: Check cache first
                self.trading_pair = self.trading_pair.replace('/', '')
                cached_result = self._get_cached_llm_result(self.trading_pair, self.timeframes)
                if cached_result:
                    return Action(
                        action=cached_result.get('action', 'HOLD'),
                        value=cached_result.get('confidence', 0.0),
                        reason=f"[CACHED] {cached_result.get('reasoning', 'Cached LLM analysis')}"
                    )
                
                # 🔒 Step 2: Try to acquire lock for LLM analysis
                if not self._acquire_llm_lock(self.trading_pair):
                    # Another worker is processing, wait for cache or fallback
                    time.sleep(2)  # Wait 2 seconds
                    cached_result = self._get_cached_llm_result(self.trading_pair, self.timeframes)
                    if cached_result:
                        return Action(
                            action=cached_result.get('action', 'HOLD'),
                            value=cached_result.get('confidence', 0.0),
                            reason=f"[WAITED] {cached_result.get('reasoning', 'LLM analysis from other worker')}"
                        )
                    else:
                        logger.warning("⚠️ No cached result available, falling back to technical analysis")
                        return self._generate_technical_signal(analysis, data)
                
                logger.info("🤖 Generating futures signal using LLM analysis...")
                
                try:
                    # Run async LLM analysis safely with ThreadPoolExecutor
                    import concurrent.futures
                    
                    def run_llm_signal():
                        """Run LLM signal generation in a separate thread with new event loop"""
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            return new_loop.run_until_complete(
                                self.generate_futures_signal_with_llm(analysis['historical_data'])
                            )
                        except Exception as e:
                            logger.error(f"LLM signal generation error: {e}")
                            return None
                        finally:
                            new_loop.close()
                    
                    # Run in thread pool to avoid event loop conflicts
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(run_llm_signal)
                        try:
                            llm_action = future.result(timeout=300)  # 60 second timeout for LLM
                            if llm_action:
                                # 💾 Cache the successful LLM result
                                cache_data = {
                                    'action': llm_action.action,
                                    'confidence': llm_action.value,
                                    'reasoning': llm_action.reason
                                }
                                self._cache_llm_result(self.trading_pair, self.timeframes, cache_data)
                                
                                # 🔓 Release lock after successful processing
                                self._release_llm_lock(self.trading_pair)
                                return llm_action
                        except concurrent.futures.TimeoutError:
                            logger.warning("LLM signal generation timed out")
                            self._release_llm_lock(self.trading_pair)
                        except Exception as e:
                            logger.warning(f"LLM signal generation failed: {e}")
                            self._release_llm_lock(self.trading_pair)
                            
                except Exception as e:
                    logger.warning(f"Failed to setup LLM signal generation: {e}")
                    self._release_llm_lock(self.trading_pair)
                
                # Fall through to traditional analysis if LLM fails
                logger.info("Falling back to traditional analysis...")
            
            # Fallback to traditional technical analysis
            return self._generate_technical_signal(analysis, data)
            
        except Exception as e:
            logger.error(f"Error in futures signal generation: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Futures signal error: {e}")
    
    def _generate_technical_signal(self, analysis: Dict[str, Any], data: pd.DataFrame) -> Action:
        """Generate signal using traditional technical analysis"""
        try:
            logger.info("Generating futures signal using traditional technical analysis...")
            if 'error' in analysis:
                return Action(action="HOLD", value=0.0, reason=f"Analysis error: {analysis['error']}")
            
            signals = []
            signal_strength = 0
            reasons = []
            
            # RSI signals (stronger for futures)
            if analysis.get('rsi_oversold', False):
                signals.append('RSI_OVERSOLD')
                signal_strength += 3  # Stronger signal for futures
                reasons.append(f"RSI oversold ({analysis.get('rsi', 0):.1f})")
            elif analysis.get('rsi_overbought', False):
                signals.append('RSI_OVERBOUGHT')
                signal_strength -= 3
                reasons.append(f"RSI overbought ({analysis.get('rsi', 0):.1f})")
            
            # MACD signals - Only add if clear signal
            macd_value = analysis.get('macd', 0)
            macd_signal_value = analysis.get('macd_signal', 0)
            if abs(macd_value - macd_signal_value) > 50:  # Significant divergence
                if analysis.get('macd_bullish', False):
                    signals.append('MACD_BULLISH')
                    signal_strength += 2
                    reasons.append("MACD bullish crossover")
                elif analysis.get('macd_bullish') == False:  # Explicitly bearish (not None or missing)
                    signals.append('MACD_BEARISH')
                    signal_strength -= 2
                    reasons.append("MACD bearish crossover")
                # No signal if MACD is neutral between bullish/bearish
            # No signal if MACD divergence is too small (neutral/unclear)
            
            # Trend signals - Only add if clear trend
            sma_20 = analysis.get('sma_20', 0)
            sma_50 = analysis.get('sma_50', 0)
            if sma_20 > 0 and sma_50 > 0:  # Ensure we have valid SMA values
                trend_strength = abs(sma_20 - sma_50) / sma_50
                if trend_strength > 0.01:  # At least 1% difference for clear trend
                    if analysis.get('trend_bullish', False):
                        signals.append('TREND_BULLISH')
                        signal_strength += 1
                        reasons.append(f"Strong bullish trend (SMA20 {trend_strength*100:.1f}% above SMA50)")
                    else:
                        signals.append('TREND_BEARISH')
                        signal_strength -= 1
                        reasons.append(f"Strong bearish trend (SMA20 {trend_strength*100:.1f}% below SMA50)")
            # No signal if trend is unclear or neutral
            
            # Volatility consideration
            volatility = analysis.get('volatility', 0)
            if volatility > 3:  # High volatility
                signal_strength *= 0.8  # Reduce strength in high volatility
                reasons.append(f"High volatility ({volatility:.1f}%)")
            
            # Decision logic for futures (more aggressive)
            confidence = min(abs(signal_strength) * 12, 100)  # Higher multiplier for futures
            reason_text = ", ".join(reasons)
            
            if signal_strength >= 4:  # Increased threshold for more conservative trading
                return Action(action="BUY", value=confidence/100, reason=reason_text)
            elif signal_strength <= -4:  # Increased threshold for more conservative trading
                return Action(action="SELL", value=confidence/100, reason=reason_text)
            else:
                return Action(action="HOLD", value=confidence/100, reason=reason_text)
                
        except Exception as e:
            logger.error(f"Error generating futures signal: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Signal generation error: {e}")
    
    async def setup_position(self, action: Action, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Setup futures position with intelligent capital management and stop loss/take profit"""
        try:
            if action.action == "HOLD":
                return {
                    'status': 'success',
                    'action': 'HOLD',
                    'reason': action.reason
                }
            self.trading_pair = self.trading_pair.replace('/', '')
            # Get account information for capital management
            account_info = self.futures_client.get_account_info()
            available_balance = float(account_info.get('availableBalance', 0))
            
            if available_balance <= 0:
                return {'status': 'error', 'message': 'No available balance for trading'}
            
            # Calculate risk metrics for position sizing
            risk_metrics = self.capital_manager.calculate_risk_metrics(account_info)
            
            # Prepare market data for capital management
            market_data = {
                'current_price': analysis.get('current_price', 0),
                'atr': analysis.get('primary_analysis', {}).get('atr', 0),
                'volatility': risk_metrics.volatility
            }
            
            # Get optimal position size using capital management system
            logger.info("🧠 Calculating optimal position size using capital management...")
            position_recommendation = self.capital_manager.calculate_position_size(
                signal_confidence=action.value,
                risk_metrics=risk_metrics,
                market_data=market_data,
                llm_service=self.llm_service
            )
            
            logger.info(f"💰 Capital Management Recommendation:")
            logger.info(f"   Recommended Size: {position_recommendation.recommended_size_pct*100:.2f}%")
            logger.info(f"   Risk Level: {position_recommendation.risk_level}")
            logger.info(f"   Method: {position_recommendation.sizing_method}")
            logger.info(f"   Reasoning: {position_recommendation.reasoning}")
            
            # Use recommended position size instead of hardcoded percentage
            optimal_position_size_pct = position_recommendation.recommended_size_pct
            
            if optimal_position_size_pct <= 0:
                return {
                    'status': 'info',
                    'action': 'HOLD',
                    'reason': f'Capital management recommends no position: {position_recommendation.reasoning}'
                }
            
            # Get entry price - use recommendation if available, fallback to current price
            entry_price = None
            take_profit_target = None
            stop_loss_target = None
            
            # First, try to get from recommendation
            if action.recommendation:
                rec = action.recommendation
                try:
                    # Parse entry price
                    entry_str = rec.get('entry_price', '').replace(',', '').strip()
                    if entry_str and entry_str != 'Market' and entry_str != 'N/A':
                        entry_price = float(entry_str)
                    
                    # Parse take profit (handle multiple TP levels)
                    # Formats: "4481.70 4493.06 4519.36" or "TP1: 0.8575 TP2: 0.8703" or "0.8575"
                    tp_str = rec.get('take_profit', '').replace(',', '').strip()
                    if tp_str and tp_str != 'N/A':
                        import re
                        # Match decimal numbers (with mandatory decimal point for prices)
                        numbers = re.findall(r'\d+\.\d+', tp_str)
                        if numbers:
                            take_profit_target = float(numbers[0])  # Take first TP
                            logger.info(f"📊 Extracted TP from '{tp_str}' → {take_profit_target}")
                        else:
                            # Try integers if no decimals found
                            numbers = re.findall(r'\d+', tp_str)
                            if numbers:
                                take_profit_target = float(numbers[0])
                                logger.info(f"📊 Extracted TP from '{tp_str}' → {take_profit_target}")
                            else:
                                logger.warning(f"Could not extract TP from: {tp_str}")
                    
                    # Parse stop loss (handle multiple SL levels)
                    sl_str = rec.get('stop_loss', '').replace(',', '').strip()
                    if sl_str and sl_str != 'N/A':
                        import re
                        # Match decimal numbers
                        numbers = re.findall(r'\d+\.\d+', sl_str)
                        if numbers:
                            stop_loss_target = float(numbers[0])  # Take first SL
                            logger.info(f"📊 Extracted SL from '{sl_str}' → {stop_loss_target}")
                        else:
                            # Try integers if no decimals found
                            numbers = re.findall(r'\d+', sl_str)
                            if numbers:
                                stop_loss_target = float(numbers[0])
                                logger.info(f"📊 Extracted SL from '{sl_str}' → {stop_loss_target}")
                            else:
                                logger.warning(f"Could not extract SL from: {sl_str}")
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse recommendation prices in setup_position: {e}")
            
            # Fallback to current market price
            if not entry_price:
                current_price = analysis.get('current_price', 0)
                if current_price <= 0:
                    return {'status': 'error', 'message': 'Invalid current price'}
                entry_price = current_price
            
            # Setup leverage
            symbol = self.trading_pair
            if not self.futures_client.set_leverage(symbol, self.leverage):
                logger.warning(f"Failed to set leverage, continuing with current leverage")
            
            # Calculate position size using capital management recommendation
            position_value = available_balance * optimal_position_size_pct * self.leverage
            quantity = position_value / entry_price
            
            # Round to proper precision
            quantity = round(quantity, 3)
            quantity_str = f"{quantity:.3f}"
            
            logger.info(f"🚀 Opening {action.action} position:")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Quantity: {quantity_str}")
            logger.info(f"   Entry Price: ${entry_price:.2f}")
            logger.info(f"   Position Size: {optimal_position_size_pct*100:.2f}% of balance")
            logger.info(f"   Position Value: ${position_value:.2f}")
            logger.info(f"   Leverage: {self.leverage}x")
            logger.info(f"   Available Balance: ${available_balance:.2f}")
            
            # Log recommendation usage
            if action.recommendation:
                            logger.info(f"🎯 LLM Targets: Entry=${entry_price:.2f}, TP=${take_profit_target or 'Default'}, SL=${stop_loss_target or 'Default'}")
            
            # Place market order
            order = self.futures_client.create_market_order(symbol, action.action, quantity_str)
            
            # Market orders are usually filled immediately, check status
            if order.status not in ['FILLED', 'NEW']:  # NEW can also indicate successful placement
                return {
                    'status': 'error',
                    'message': f'Order failed with status: {order.status}'
                }
            
            logger.info(f"✅ Market order placed successfully: {order.status}")
            
            # Calculate stop loss and take profit prices - use recommendation if available
            if action.action == "BUY":
                # Use recommendation targets or fallback to percentage calculation
                if stop_loss_target:
                    stop_loss_price = stop_loss_target
                else:
                    stop_loss_price = entry_price * (1 - self.stop_loss_pct)
                
                if take_profit_target:
                    take_profit_price = take_profit_target
                else:
                    take_profit_price = entry_price * (1 + self.take_profit_pct)
                
                sl_side = "SELL"
                tp_side = "SELL"
            else:  # SELL
                # Use recommendation targets or fallback to percentage calculation
                if stop_loss_target:
                    stop_loss_price = stop_loss_target
                else:
                    stop_loss_price = entry_price * (1 + self.stop_loss_pct)
                
                if take_profit_target:
                    take_profit_price = take_profit_target
                else:
                    take_profit_price = entry_price * (1 - self.take_profit_pct)
                
                sl_side = "BUY"
                tp_side = "BUY"
            
            # 🔗 Place OCO order (One-Cancels-Other) with STOP_MARKET and TAKE_PROFIT_MARKET
            try:
                # Get current market price for validation
                current_ticker = self.futures_client.get_ticker(symbol)
                current_market_price = float(current_ticker['price'])
                
                # Validate and adjust stop loss price
                min_distance = current_market_price * 0.001  # 0.1% minimum distance
                adjusted_stop_price = stop_loss_price
                
                if action.action == "BUY":  # Long position
                    # Stop loss should be BELOW current market price
                    if stop_loss_price >= current_market_price:
                        adjusted_stop_price = current_market_price * (1 - max(self.stop_loss_pct, 0.005))  # Min 0.5%
                        logger.warning(f"⚠️ Stop loss adjusted: {stop_loss_price:.2f} → {adjusted_stop_price:.2f}")
                    
                    # Ensure minimum distance
                    if current_market_price - adjusted_stop_price < min_distance:
                        adjusted_stop_price = current_market_price - min_distance
                        logger.warning(f"⚠️ Stop loss distance adjusted for safety: {adjusted_stop_price:.2f}")
                    
                else:  # SELL - Short position  
                    # Stop loss should be ABOVE current market price
                    if stop_loss_price <= current_market_price:
                        adjusted_stop_price = current_market_price * (1 + max(self.stop_loss_pct, 0.005))  # Min 0.5%
                        logger.warning(f"⚠️ Stop loss adjusted: {stop_loss_price:.2f} → {adjusted_stop_price:.2f}")
                    
                    # Ensure minimum distance
                    if adjusted_stop_price - current_market_price < min_distance:
                        adjusted_stop_price = current_market_price + min_distance
                        logger.warning(f"⚠️ Stop loss distance adjusted for safety: {adjusted_stop_price:.2f}")
                
                # Validate and adjust take profit price
                adjusted_tp_price = take_profit_price
                min_tp_distance = current_market_price * 0.002  # 0.2% minimum for TP
                
                if action.action == "BUY":  # Long position
                    # Take profit should be ABOVE current market price
                    if take_profit_price <= current_market_price:
                        adjusted_tp_price = current_market_price * (1 + max(self.take_profit_pct, 0.01))  # Min 1%
                        logger.warning(f"⚠️ Take profit adjusted: {take_profit_price:.2f} → {adjusted_tp_price:.2f}")
                    
                    # Ensure minimum distance
                    if adjusted_tp_price - current_market_price < min_tp_distance:
                        adjusted_tp_price = current_market_price + min_tp_distance
                        logger.warning(f"⚠️ Take profit distance adjusted: {adjusted_tp_price:.2f}")
                    
                else:  # SELL - Short position
                    # Take profit should be BELOW current market price
                    if take_profit_price >= current_market_price:
                        adjusted_tp_price = current_market_price * (1 - max(self.take_profit_pct, 0.01))  # Min 1%
                        logger.warning(f"⚠️ Take profit adjusted: {take_profit_price:.2f} → {adjusted_tp_price:.2f}")
                    
                    # Ensure minimum distance
                    if current_market_price - adjusted_tp_price < min_tp_distance:
                        adjusted_tp_price = current_market_price - min_tp_distance
                        logger.warning(f"⚠️ Take profit distance adjusted: {adjusted_tp_price:.2f}")
                
                # Create managed orders (1 SL + 2 TP with duplicate check)
                managed_orders = self.futures_client.create_managed_orders(
                    symbol=symbol,
                    side=sl_side,  # Same side for both SL and TP (opposite of entry)
                    quantity=quantity_str,
                    stop_price=f"{adjusted_stop_price:.2f}",
                    take_profit_price=f"{adjusted_tp_price:.2f}",
                    reduce_only=True
                )
                
                sl_order = managed_orders['stop_loss_order']
                tp_orders = managed_orders['take_profit_orders']
                
                logger.info(f"✅ Managed Orders placed successfully:")
                logger.info(f"🛡️ Stop Loss: {sl_order.get('order_id', 'N/A')} @ ${adjusted_stop_price:.2f}")
                logger.info(f"🎯 Take Profit 1: {tp_orders[0].get('order_id', 'N/A')} (50% @ ${tp_orders[0].get('price', 'N/A')})")
                logger.info(f"🎯 Take Profit 2: {tp_orders[1].get('order_id', 'N/A')} (50% @ ${tp_orders[1].get('price', 'N/A')})")
                
            except Exception as e:
                logger.error(f"Failed to place managed orders: {e}")
                if "would immediately trigger" in str(e).lower():
                    logger.error("💡 Tip: Order prices too close to market price. Consider wider stop/profit percentages.")
                sl_order = None
                tp_orders = None
            
            result = {
                'status': 'success',
                'action': action.action,
                'symbol': symbol,
                'quantity': quantity_str,
                'entry_price': entry_price,
                'leverage': self.leverage,
                'position_value': position_value,
                'main_order_id': order.order_id,
                'stop_loss': {
                    'price': stop_loss_price,
                    'order_id': sl_order.get('order_id') if sl_order else None,
                    'source': 'recommendation' if stop_loss_target else 'percentage'
                },
                'take_profit': {
                    'price': take_profit_price,
                    'order_ids': [tp.get('order_id') for tp in tp_orders] if 'tp_orders' in locals() and tp_orders else [None],
                    'strategy': 'partial_profit_taking',
                    'source': 'recommendation' if take_profit_target else 'percentage'
                },
                'confidence': action.value,
                'reason': action.reason,
                'timestamp': datetime.now().isoformat(),
                
                # Capital Management Results
                'capital_management': {
                    'recommended_size_pct': position_recommendation.recommended_size_pct * 100,
                    'risk_level': position_recommendation.risk_level,
                    'sizing_method': position_recommendation.sizing_method,
                    'reasoning': position_recommendation.reasoning,
                    'confidence_adjustment': position_recommendation.confidence_adjustment,
                    'volatility_adjustment': position_recommendation.volatility_adjustment,
                    'drawdown_adjustment': position_recommendation.drawdown_adjustment
                },
                
                # Risk Metrics
                'risk_metrics': {
                    'account_balance': risk_metrics.account_balance,
                    'available_balance': risk_metrics.available_balance,
                    'current_drawdown': f"{risk_metrics.current_drawdown*100:.2f}%",
                    'portfolio_exposure': f"{risk_metrics.portfolio_exposure*100:.2f}%",
                    'volatility': f"{risk_metrics.volatility*100:.2f}%",
                    'sharpe_ratio': risk_metrics.sharpe_ratio,
                    'win_rate': f"{risk_metrics.win_rate*100:.1f}%"
                }
            }
            
            # Add recommendation info if available
            if action.recommendation:
                result['recommendation_used'] = True
                result['strategy'] = action.recommendation.get('strategy', 'N/A')
                result['risk_reward'] = action.recommendation.get('risk_reward', 'N/A')
            else:
                result['recommendation_used'] = False
            
            return result
            
        except Exception as e:
            logger.error(f"Error setting up futures position: {e}")
            return {
                'status': 'error',
                'message': f'Position setup error: {e}'
            }

    # Giả lập 50 cây nến gần nhất theo khung thời gian (ví dụ: 1H)
    def generate_fake_klines_df(n_rows=50, interval_seconds=3600):
        import random
        now = int(time.time())
        timestamps = [now - i * interval_seconds for i in reversed(range(n_rows))]

        data = {
            "timestamp": timestamps,
            "open": [],
            "high": [],
            "low": [],
            "close": [],
            "volume": [],
        }

        base_price = 27000.0

        for _ in range(n_rows):
            o = base_price + random.uniform(-100, 100)
            h = o + random.uniform(0, 50)
            l = o - random.uniform(0, 50)
            c = random.uniform(l, h)
            v = random.uniform(10, 100)

            data["open"].append(round(o, 2))
            data["high"].append(round(h, 2))
            data["low"].append(round(l, 2))
            data["close"].append(round(c, 2))
            data["volume"].append(round(v, 2))

        return pd.DataFrame(data)

    def crawl_data(self) -> Dict[str, Any]:
        """
        Crawl historical data for multiple timeframes dynamically
        - Đảm bảo mỗi timeframe có ÍT NHẤT 20 nến đã đóng
        - Tự backfill (mở rộng lookback) nếu lần fetch đầu chưa đủ
        - Snap end_time về nến đã đóng gần nhất để tránh dính nến đang chạy
        """

        import time
        from datetime import datetime
        import pandas as pd

        # ==== Helper: đồng bộ time offset nếu class có hàm/thuộc tính ====
        def _now_ms():
            # Nếu class có self._time_offset (đã sync server time trước đó) thì dùng
            offset = getattr(self, "_time_offset", 0)
            return int(time.time() * 1000) + int(offset)

        # ==== Helper: chuyển DataFrame/records => list[dict] chuẩn output ====
        def _df_to_records(df: pd.DataFrame) -> list:
            out = []
            for _, row in df.iterrows():
                ts = row["timestamp"]
                if hasattr(ts, "timestamp"):
                    ts_ms = int(ts.timestamp() * 1000)
                elif isinstance(ts, (int, float)):
                    ts_ms = int(ts) if ts > 1e12 else int(ts * 1000)
                else:
                    ts_ms = int(pd.to_datetime(ts).timestamp() * 1000)

                out.append({
                    "timestamp": ts_ms,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                })
            return out

        # ==== Cấu hình ====
        timeframe_to_ms = {
            "1m": 60_000, "3m": 3 * 60_000, "5m": 5 * 60_000, "15m": 15 * 60_000,
            "30m": 30 * 60_000, "1h": 60 * 60_000, "2h": 2 * 60 * 60_000, "4h": 4 * 60 * 60_000,
            "6h": 6 * 60 * 60_000, "8h": 8 * 60 * 60_000, "12h": 12 * 60 * 60_000,
            "1d": 24 * 60 * 60_000, "3d": 3 * 24 * 60 * 60_000, "1w": 7 * 24 * 60 * 60_000,
            "1M": 30 * 24 * 60 * 60_000,
        }

        # Giới hạn mặc định theo TF (có thể lớn hơn 20 để vẽ chỉ báo đẹp hơn)
        timeframe_limits = {
            "30m": 200, "1h": 200, "4h": 42,
            "1m": 1000, "3m": 1000, "5m": 500, "15m": 500,
            "2h": 84, "6h": 28, "8h": 21, "12h": 14,
            "1d": 30, "3d": 30, "1w": 52, "1M": 12
        }

        MIN_NEEDED = 20  # Bắt buộc tối thiểu
        INITIAL_LOOKBACK_MULT = 1.5  # lần đầu lấy rộng hơn limit 1.5x
        MAX_RETRIES = 3  # số vòng backfill tối đa nếu thiếu
        # SYMBOL = self.trading_pair
        self.trading_pair = self.trading_pair.replace('/', '')
        # ALWAYS use mainnet client for data crawling (accurate volume & real-time data)
        # Use the correct client based on subscription's is_testnet setting
        # Data crawling should match the trading environment (testnet vs mainnet)
        CLIENT = self.futures_client
        if not CLIENT:
            logger.error("❌ No futures client available")
            return {
                'timeframes': {},
                'error': 'No futures client initialized'
            }
        
        client_type = "TESTNET (subscription is_testnet=True)" if self.testnet else "MAINNET (subscription is_testnet=False)"
        logger.info(f"📊 Data crawling using {client_type} client for accurate volume & real-time data")

        timeframes_data = {}
        try:
            logger.info(f"🔄 Crawling data for timeframes: {self.timeframes}")

            for i, timeframe in enumerate(self.timeframes, 1):
                try:
                    if timeframe not in timeframe_to_ms:
                        raise ValueError(f"Unsupported timeframe: {timeframe}")

                    interval_ms = timeframe_to_ms[timeframe]
                    # Snap về nến đã đóng gần nhất
                    now_ms = _now_ms()
                    last_closed_open = (now_ms // interval_ms) * interval_ms - interval_ms
                    end_time = last_closed_open + interval_ms - 1

                    # Số nến mong muốn ban đầu (ít nhất MIN_NEEDED)
                    base_limit = timeframe_limits.get(timeframe, 100)
                    desired_limit = max(base_limit, MIN_NEEDED)

                    # Lấy cửa sổ rộng hơn để chắc ăn
                    lookback = int(max(desired_limit, int(desired_limit * INITIAL_LOOKBACK_MULT)))
                    start_time = end_time - (lookback - 1) * interval_ms

                    logger.info(f"📊 [{i}/{len(self.timeframes)}] Fetching {lookback} {timeframe} candles for {self.trading_pair}")

                    # ---- Lần fetch đầu
                    df = CLIENT.get_klines(
                        symbol=self.trading_pair,
                        interval=timeframe,
                        start_time=start_time,
                        end_time=end_time,
                        limit=lookback
                    )

                    if df is None or len(df) == 0:
                        raise RuntimeError(f"Empty klines for {timeframe}")

                    # Backfill nếu thiếu < MIN_NEEDED (mở rộng cửa sổ lùi)
                    retries = 0
                    while len(df) < MIN_NEEDED and retries < MAX_RETRIES:
                        retries += 1
                        # dịch cửa sổ lùi thêm 3x MIN_NEEDED nến mỗi vòng
                        add_lookback = MIN_NEEDED * 3 * interval_ms
                        new_start = max(0, start_time - add_lookback)
                        new_end = start_time - 1  # nối liền trước cửa sổ cũ

                        logger.warning(f"⚠️ {timeframe} thiếu nến {len(df)}/{MIN_NEEDED}, backfill lần {retries}...")
                        df_more = CLIENT.get_klines(
                            symbol=self.trading_pair,
                            interval=timeframe,
                            start_time=new_start,
                            end_time=new_end,
                            limit=MIN_NEEDED * 3
                        )

                        # Gộp, bỏ trùng, sort theo timestamp
                        if df_more is not None and len(df_more) > 0:
                            df = pd.concat([df_more, df], axis=0).drop_duplicates(subset=["timestamp"]).sort_values(
                                "timestamp")
                        start_time = new_start  # cập nhật để có thể lùi tiếp nếu cần

                    # Xử lý cuối: đảm bảo sort & chỉ giữ gần nhất 'desired_limit' nến (đủ to cho chỉ báo)
                    df = df.sort_values("timestamp")
                    if len(df) < MIN_NEEDED:
                        logger.warning(f"❗ {timeframe} vẫn thiếu nến sau backfill: {len(df)}/{MIN_NEEDED}")

                    if len(df) > desired_limit:
                        df = df.iloc[-desired_limit:]

                    # Convert ra list records
                    records = _df_to_records(df)
                    timeframes_data[timeframe] = records

                    logger.info(
                        f"✅ [{i}/{len(self.timeframes)}] Got {len(records)} {timeframe} candles (>=20 required)")

                except Exception as tf_err:
                    logger.error(f"❌ [{i}/{len(self.timeframes)}] Failed to fetch {timeframe}: {tf_err}")
                    # Fallback: nếu muốn, có thể tạo sample; ở đây mình trả mảng rỗng để bạn dễ debug
                    timeframes_data[timeframe] = []
                    # hoặc: timeframes_data[timeframe] = self._generate_single_timeframe_sample_data(timeframe)

            # Báo cáo tổng thể
            report = {tf: len(candles) for tf, candles in timeframes_data.items()}
            logger.info(f"🎯 Completed crawling {len(timeframes_data)} TFs. Candle counts: {report}")

            return {
                "timeframes": timeframes_data,
                "crawl_timestamp": datetime.now().isoformat(),
                "total_timeframes": len(timeframes_data)
            }

        except Exception as e:
            logger.error(f"Error crawling multi-timeframe data: {e}")
            # Có thể fallback sample toàn bộ nếu muốn
            # return self._generate_multi_timeframe_sample_data()
            return {
                "timeframes": timeframes_data,
                "crawl_timestamp": datetime.now().isoformat(),
                "total_timeframes": len(timeframes_data),
                "error": str(e)
            }

    def _generate_multi_timeframe_sample_data(self) -> Dict[str, Any]:
        """Generate sample OHLCV data for multiple timeframes"""
        try:
            timeframes_data = {}
            
            for timeframe in self.timeframes:
                timeframes_data[timeframe] = self._generate_single_timeframe_sample_data(timeframe)
            
            return {
                "timeframes": timeframes_data,
                "crawl_timestamp": datetime.now().isoformat(),
                "total_timeframes": len(timeframes_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating multi-timeframe sample data: {e}")
            return {"timeframes": {}}
    
    def _generate_single_timeframe_sample_data(self, timeframe: str) -> List[Dict[str, Any]]:
        """Generate sample OHLCV data for a single timeframe - Enhanced for all timeframes"""
        import random
        from datetime import datetime, timedelta
        
        # Enhanced timeframe mapping
        timeframe_minutes = {
            # Minutes
            '1m': 1,     '3m': 3,     '5m': 5,     '15m': 15,   '30m': 30,
            # Hours
            '1h': 60,    '2h': 120,   '4h': 240,   '6h': 360,   '8h': 480,   '12h': 720,
            # Days+
            '1d': 1440,  '3d': 4320,  '1w': 10080, '1M': 43200
        }
        
        minutes_per_candle = timeframe_minutes.get(timeframe, 60)
        
        # Determine appropriate number of candles
        num_candles_map = {
            # Minutes - shorter history for faster timeframes
            '1m': 500,   '3m': 500,   '5m': 300,   '15m': 200,  '30m': 150,
            # Hours - good balance
            '1h': 168,   '2h': 84,    '4h': 42,    '6h': 28,    '8h': 21,    '12h': 14,
            # Days+ - longer history
            '1d': 30,    '3d': 30,    '1w': 52,    '1M': 12
        }
        
        num_candles = num_candles_map.get(timeframe, 100)
        
        data = []
        base_price = 50000  # Starting price
        current_time = datetime.now()
        
        # Volatility scaling based on timeframe
        volatility_multiplier = min(minutes_per_candle / 1440, 3)  # More volatile for longer timeframes
        
        for i in range(num_candles):
            # Simulate realistic price movement
            change = random.uniform(-0.015, 0.015) * volatility_multiplier
            base_price *= (1 + change)
            
            # Generate realistic OHLCV
            open_price = base_price
            high_price = open_price * (1 + random.uniform(0, 0.01 * volatility_multiplier))
            low_price = open_price * (1 - random.uniform(0, 0.01 * volatility_multiplier))
            close_price = random.uniform(low_price, high_price)
            
            # Volume scaling based on timeframe
            volume = random.uniform(50, 500) * volatility_multiplier
            
            # Calculate proper timestamp
            candle_time = current_time - timedelta(minutes=minutes_per_candle * (num_candles - i))
            
            data.append({
                'timestamp': int(candle_time.timestamp() * 1000),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            base_price = close_price
        
        return data
    
    def _generate_sample_data(self) -> List[Dict[str, Any]]:
        """Generate sample OHLCV data for testing - Legacy method for backwards compatibility"""
        return self._generate_single_timeframe_sample_data('1h')
    
    def analyze_data(self, multi_timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze multi-timeframe historical data and calculate indicators
        """
        try:
            timeframes_data = multi_timeframe_data.get("timeframes", {})
            if not timeframes_data:
                return {'error': 'No timeframes data provided'}
            
            # Analyze each timeframe
            multi_analysis = {}
            
            for timeframe, historical_data in timeframes_data.items():
                if not historical_data:
                    continue
                    
                try:
                    # Convert to DataFrame for analysis
                    df = pd.DataFrame(historical_data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df = df.set_index('timestamp')
                    
                    # Calculate analysis for this timeframe
                    timeframe_analysis = self._calculate_futures_analysis(df, historical_data)
                    multi_analysis[timeframe] = timeframe_analysis
                    
                    logger.info(f"Analyzed {timeframe}: Current price {timeframe_analysis.get('current_price', 0):.2f}")
                    
                except Exception as e:
                    logger.error(f"Error analyzing {timeframe} data: {e}")
                    multi_analysis[timeframe] = {'error': f'Analysis error: {e}'}
            
            # Get primary timeframe analysis
            primary_analysis = multi_analysis.get(self.primary_timeframe, {})
            
            # Combine all timeframes for LLM analysis
            combined_analysis = {
                'multi_timeframe': multi_analysis,
                'primary_timeframe': self.primary_timeframe,
                'primary_analysis': primary_analysis,
                'timeframes_data': timeframes_data  # Include raw data for LLM
            }
            
            # Add overall current price from primary timeframe
            if 'current_price' in primary_analysis:
                combined_analysis['current_price'] = primary_analysis['current_price']
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing multi-timeframe data: {e}")
            return {'error': f'Multi-timeframe analysis error: {e}'}
    
    def generate_signal(self, analysis: Dict[str, Any]) -> Action:
        """
        Generate trading signal based on multi-timeframe analysis
        """
        self.trading_pair = self.trading_pair.replace('/', '')
        try:
            # Check for analysis errors
            if 'error' in analysis:
                return Action(action="HOLD", value=0.0, reason=f"Analysis error: {analysis['error']}")
            
            # Use LLM analysis if available and enabled
            if (self.use_llm_analysis and self.llm_service and 
                'timeframes_data' in analysis and analysis['timeframes_data']):
                
                # 🔍 Step 1: Check cache first
                cached_result = self._get_cached_llm_result(self.trading_pair, self.timeframes)
                if cached_result:
                    return Action(
                        action=cached_result.get('action', 'HOLD'),
                        value=cached_result.get('confidence', 0.0),
                        reason=f"[CACHED-MTF] {cached_result.get('reasoning', 'Cached multi-timeframe LLM analysis')}"
                    )
                
                # 🔒 Step 2: Try to acquire lock for LLM analysis
                if not self._acquire_llm_lock(self.trading_pair):
                    # Another worker is processing, wait for cache or fallback
                    time.sleep(3)  # Wait 3 seconds for multi-timeframe
                    cached_result = self._get_cached_llm_result(self.trading_pair, self.timeframes)
                    if cached_result:
                        return Action(
                            action=cached_result.get('action', 'HOLD'),
                            value=cached_result.get('confidence', 0.0),
                            reason=f"[WAITED-MTF] {cached_result.get('reasoning', 'Multi-timeframe LLM analysis from other worker')}"
                        )
                    else:
                        logger.warning("⚠️ No cached multi-timeframe result available, falling back to technical analysis")
                        # Skip to traditional analysis
                        pass
                else:
                    logger.info("🤖 Generating signal using LLM multi-timeframe analysis...")
                    
                    try:
                        # Try to run async LLM analysis safely
                        import concurrent.futures
                        import threading
                        
                        def run_llm_signal():
                            """Run LLM signal generation in a separate thread with new event loop"""
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                # Pass both raw data and indicators analysis
                                return new_loop.run_until_complete(
                                    self._generate_llm_signal_from_multi_timeframes(
                                        analysis['timeframes_data'],
                                        analysis.get('multi_timeframe', {})  # Pass indicators data
                                    )
                                )
                            except Exception as e:
                                logger.error(f"LLM signal generation error: {e}")
                                return None
                            finally:
                                new_loop.close()
                        
                        # Run in thread pool to avoid event loop conflicts
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_llm_signal)
                            try:
                                llm_action = future.result(timeout=60)  # 60 second timeout for LLM
                                if llm_action:
                                    # 💾 Cache the successful multi-timeframe LLM result
                                    cache_data = {
                                        'action': llm_action.action,
                                        'confidence': llm_action.value,
                                        'reasoning': llm_action.reason
                                    }
                                    self._cache_llm_result(self.trading_pair, self.timeframes, cache_data)
                                    
                                    # 🔓 Release lock after successful processing
                                    self._release_llm_lock(self.trading_pair)
                                    return llm_action
                            except concurrent.futures.TimeoutError:
                                logger.warning("LLM multi-timeframe signal generation timed out")
                                self._release_llm_lock(self.trading_pair)
                            except Exception as e:
                                logger.warning(f"LLM multi-timeframe signal generation failed: {e}")
                                self._release_llm_lock(self.trading_pair)
                                
                    except Exception as e:
                        logger.warning(f"Failed to setup multi-timeframe LLM signal generation: {e}")
                        self._release_llm_lock(self.trading_pair)
                
                # Fall through to traditional analysis if LLM fails
                logger.info("Falling back to traditional analysis...")
            
            # Fallback to traditional multi-timeframe technical analysis
            logger.info("Generating signal using traditional multi-timeframe technical analysis...")
            
            multi_analysis = analysis.get('multi_timeframe', {})
            primary_analysis = analysis.get('primary_analysis', {})
            
            if not primary_analysis or 'error' in primary_analysis:
                return Action(action="HOLD", value=0.0, reason="No valid primary timeframe analysis")
            
            # Start with primary timeframe signal
            primary_df = pd.DataFrame({'close': [primary_analysis.get('current_price', 50000)], 'volume': [100]})
            primary_signal = self._generate_futures_signal(primary_analysis, primary_df, allow_llm=False)
            
            # Analyze other timeframes for confirmation
            confirmations = 0
            total_timeframes = 0
            
            for tf, tf_analysis in multi_analysis.items():
                if tf == self.primary_timeframe or 'error' in tf_analysis:
                    continue
                    
                total_timeframes += 1
                tf_df = pd.DataFrame({'close': [tf_analysis.get('current_price', 50000)], 'volume': [100]})
                tf_signal = self._generate_futures_signal(tf_analysis, tf_df, allow_llm=False)
                
                # Check if signals align
                if tf_signal.action == primary_signal.action:
                    confirmations += 1
            
            # Calculate confirmation strength
            confirmation_ratio = confirmations / total_timeframes if total_timeframes > 0 else 1.0
            
            # Adjust confidence based on multi-timeframe confirmation
            adjusted_confidence = primary_signal.value * (0.5 + 0.5 * confirmation_ratio)
            
            reason = f"[MULTI-TF] {primary_signal.reason}"
            if total_timeframes > 0:
                reason += f" | Confirmation: {confirmations}/{total_timeframes} timeframes"
            
            # Create technical analysis recommendation
            current_price = primary_analysis.get('current_price', 50000)
            if primary_signal.action == "BUY":
                entry_price = f"{current_price:.2f}"
                take_profit = f"{current_price * 1.04:.2f}"  # 4% profit
                stop_loss = f"{current_price * 0.98:.2f}"    # 2% loss
            elif primary_signal.action == "SELL":
                entry_price = f"{current_price:.2f}"
                take_profit = f"{current_price * 0.96:.2f}"  # 4% profit (short)
                stop_loss = f"{current_price * 1.02:.2f}"    # 2% loss (short)
            else:
                entry_price = "N/A"
                take_profit = "N/A"
                stop_loss = "N/A"
            
            technical_recommendation = {
                "action": primary_signal.action,
                "confidence": f"{adjusted_confidence*100:.1f}%",
                "entry_price": entry_price,
                "take_profit": take_profit,
                "stop_loss": stop_loss,
                "strategy": "Multi-timeframe technical analysis",
                "risk_reward": "1:2" if primary_signal.action != "HOLD" else "N/A",
                "reasoning": reason
            }
            
            return Action(
                action=primary_signal.action, 
                value=adjusted_confidence, 
                reason=reason,
                recommendation=technical_recommendation
            )
            
        except Exception as e:
            logger.error(f"Error generating multi-timeframe signal: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Signal generation error: {e}")
    
    async def _generate_llm_signal_from_multi_timeframes(self, timeframes_data: Dict[str, List[Dict]], 
                                                         indicators_analysis: Dict[str, Dict[str, Any]] = None) -> Action:
        """Generate signal using LLM with multi-timeframe data and indicators"""
        try:
            if not self.llm_service:
                logger.error("LLM service not available")
                return Action(action="HOLD", value=0.0, reason="LLM service unavailable")
            
            # Clean and prepare timeframes data for LLM
            cleaned_timeframes_data = {}
            for timeframe, data in timeframes_data.items():
                if data:
                    # Take appropriate amount of recent data for each timeframe
                    data_limits = {'1m': 60, '3m': 60, '5m': 60, '15m': 48, '30m': 48, '1h': 24, '2h': 24, '4h': 12, '6h': 12, '8h': 12, '12h': 12, '1d': 7, '3d': 7, '1w': 4, '1M': 4}
                    limit = data_limits.get(timeframe, 24)
                    
                    cleaned_data = []
                    for item in data[-limit:]:  # Take recent data
                        cleaned_item = {}
                        for key, value in item.items():
                            if hasattr(value, 'timestamp'):
                                cleaned_item[key] = int(value.timestamp() * 1000)
                            elif hasattr(value, 'isoformat'):
                                cleaned_item[key] = value.isoformat()
                            else:
                                cleaned_item[key] = float(value) if isinstance(value, (int, float)) else value
                        cleaned_data.append(cleaned_item)
                    
                    cleaned_timeframes_data[timeframe] = cleaned_data
            
            # Get LLM analysis with indicators data
            self.trading_pair = self.trading_pair.replace('/', '')
            symbol = self.trading_pair
            llm_analysis = await self.llm_service.analyze_market(
                symbol=symbol,
                timeframes_data=cleaned_timeframes_data,
                indicators_analysis=indicators_analysis,  # ✅ Pass indicators to LLM
                model=self.llm_model,
                bot_id=self.bot_id  # Pass bot_id for custom prompt
            )
            
            if "error" in llm_analysis:
                logger.error(f"LLM analysis failed: {llm_analysis['error']}")
                return Action(action="HOLD", value=0.0, reason=f"LLM analysis error: {llm_analysis['error']}")
            
            # Parse LLM recommendation
            if llm_analysis.get("parsed", False) and "recommendation" in llm_analysis:
                recommendation = llm_analysis["recommendation"]
                
                action = recommendation.get("action", "HOLD").upper()
                
                # Parse confidence
                confidence_raw = recommendation.get("confidence", 0)
                try:
                    if isinstance(confidence_raw, str):
                        confidence_str = confidence_raw.replace("%", "").strip()
                        confidence = float(confidence_str) / 100.0
                    else:
                        confidence = float(confidence_raw) / 100.0
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse confidence '{confidence_raw}': {e}")
                    confidence = 0.0


                reasoning = recommendation.get("reasoning", "LLM multi-timeframe analysis")
                
                # Extract additional recommendation details
                entry_price = recommendation.get("entry_price", "Market")
                take_profit = recommendation.get("take_profit", "N/A")
                stop_loss = recommendation.get("stop_loss", "N/A")
                strategy = recommendation.get("strategy", "Multi-timeframe analysis")
                risk_reward = recommendation.get("risk_reward", "N/A")
                
                # Handle CLOSE action
                if action == "CLOSE":
                    action = "SELL"
                
                # Validate action
                if action not in ["BUY", "SELL", "HOLD"]:
                    action = "HOLD"
                    confidence = 0.0
                    reasoning = f"Invalid LLM action: {action}"
                
                logger.info(f"🤖 LLM Multi-TF: {action} ({confidence*100:.1f}%) - {reasoning[:50]}...")
                
                # Store full recommendation details
                full_recommendation = {
                    "action": action,
                    "confidence": f"{confidence*100:.1f}%",
                    "entry_price": entry_price,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                    "strategy": strategy,
                    "risk_reward": risk_reward,
                    "reasoning": reasoning
                }
                
                # Create action with embedded recommendation data
                return Action(
                    action=action, 
                    value=confidence, 
                    reason=f"[LLM-MULTI-TF] {reasoning}",
                    recommendation=full_recommendation
                )
            else:
                logger.warning("LLM response could not be parsed properly")
                return Action(action="HOLD", value=0.0, reason="Unparseable LLM response")
                
        except Exception as e:
            logger.error(f"Error in LLM multi-timeframe signal generation: {e}")
            return Action(action="HOLD", value=0.0, reason=f"LLM multi-timeframe signal error: {e}")
    
    def execute_trade(self, signal: Action, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the trading signal using multi-timeframe analysis
        """
        try:
            if signal.action == "HOLD":
                return {
                    'status': 'success',
                    'action': 'HOLD',
                    'reason': signal.reason,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get prices - use recommendation if available, fallback to current price
            current_price = None
            entry_price = None
            take_profit_price = None
            stop_loss_price = None
            
            # First, try to get from recommendation
            if signal.recommendation:
                rec = signal.recommendation
                try:
                    # Parse entry price
                    entry_str = rec.get('entry_price', '').replace(',', '').strip()
                    if entry_str and entry_str != 'Market' and entry_str != 'N/A':
                        entry_price = float(entry_str)
                    
                    # Parse take profit
                    tp_str = rec.get('take_profit', '').replace(',', '').strip()
                    if tp_str and tp_str != 'N/A':
                        take_profit_price = float(tp_str)
                    
                    # Parse stop loss
                    sl_str = rec.get('stop_loss', '').replace(',', '').strip()
                    if sl_str and sl_str != 'N/A':
                        stop_loss_price = float(sl_str)
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse recommendation prices: {e}")
            
            # Fallback to current market price
            if not entry_price:
                primary_analysis = analysis.get('primary_analysis', {})
                if primary_analysis and 'current_price' in primary_analysis:
                    current_price = primary_analysis['current_price']
                elif 'current_price' in analysis:
                    current_price = analysis['current_price']
                entry_price = current_price
            
            if not entry_price:
                return {
                    'status': 'error',
                    'message': 'No entry price available for trade execution'
                }
            
            # For actual trading, would call setup_position with recommendation prices
            # For testing, return comprehensive signal info with recommendation prices
            trade_result = {
                'status': 'success',
                'action': signal.action,
                'confidence': signal.value,
                'reason': signal.reason,
                'entry_price': entry_price,
                'primary_timeframe': analysis.get('primary_timeframe', self.primary_timeframe),
                'timeframes_analyzed': list(analysis.get('multi_timeframe', {}).keys()),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add recommendation prices if available
            if take_profit_price:
                trade_result['take_profit_price'] = take_profit_price
            if stop_loss_price:
                trade_result['stop_loss_price'] = stop_loss_price
            if signal.recommendation:
                trade_result['strategy'] = signal.recommendation.get('strategy', 'N/A')
                trade_result['risk_reward'] = signal.recommendation.get('risk_reward', 'N/A')
            
            return trade_result
            
        except Exception as e:
            logger.error(f"Error executing multi-timeframe trade: {e}")
            return {
                'status': 'error',
                'message': f'Multi-timeframe trade execution error: {e}'
            }

    def check_account_status(self):
        try:
            print("\n💼 CHECKING BINANCE ACCOUNT STATUS...")
            print("=" * 50)

            account_info = self.futures_client.get_account_info()  # no timestamp kwargs
            
            # Handle empty string or None values from API
            available_balance_raw = account_info.get('availableBalance', 0)
            total_wallet_balance_raw = account_info.get('totalWalletBalance', 0)
            
            available_balance = float(available_balance_raw) if available_balance_raw not in [None, ''] else 0.0
            total_wallet_balance = float(total_wallet_balance_raw) if total_wallet_balance_raw not in [None, ''] else 0.0

            mode = "🧪 TESTNET" if self.testnet else "🔴 LIVE"
            print(f"{mode} Account Balance:")
            print(f"   💰 Available: ${available_balance:,.2f} USDT")
            print(f"   💎 Total Wallet: ${total_wallet_balance:,.2f} USDT")

            positions = self.futures_client.get_positions()
            # ... phần còn lại giữ nguyên
            return {
                'available_balance': available_balance,
                'total_balance': total_wallet_balance,
                'active_positions': len([p for p in positions if float(getattr(p, "size", 0)) != 0]),
                'positions': positions
            }

        except Exception as e:
            msg = str(e)
            if "-1021" in msg or "Timestamp" in msg:
                print("🔄 Resync time & retry...")
                # Nếu dùng Cách A:
                try:
                    self.futures_client._sync_server_time()
                    return self.check_account_status()
                except Exception:
                    pass
                # Nếu dùng SDK, ping server time:
                try:
                    _ = self.futures_client.time()  # tùy SDK
                    return self.check_account_status()
                except Exception:
                    pass
            print(f"❌ Failed to check account: {e}")
            return None

    def save_transaction_to_db(self, trade_result: Dict[str, Any]):
        """Save trade transaction to MySQL database with enhanced tracking"""
        try:
            from core.database import get_db
            from core import models
            from sqlalchemy.orm import Session
            from datetime import datetime
            from decimal import Decimal
            
            # Get database session
            db = next(get_db())
            
            # Determine position side
            action = trade_result.get('action', '').upper()
            position_side = 'LONG' if action == 'BUY' else 'SHORT' if action == 'SELL' else None
            
            # Calculate planned risk-reward ratio
            entry_price = float(trade_result.get('entry_price', 0))
            stop_loss = float(trade_result.get('stop_loss', 0)) if trade_result.get('stop_loss') else None
            take_profit = float(trade_result.get('take_profit', 0)) if trade_result.get('take_profit') else None
            
            risk_reward_ratio = None
            if stop_loss and take_profit and entry_price > 0:
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                if risk > 0:
                    risk_reward_ratio = Decimal(str(round(reward / risk, 4)))
            
            # Create transaction record with enhanced fields
            transaction = models.Transaction(
                # Identity & Ownership
                user_id=trade_result.get('user_id'),  # Can be None for marketplace users
                user_principal_id=trade_result.get('user_principal_id'),  # For marketplace
                bot_id=trade_result.get('bot_id', 1),
                subscription_id=trade_result.get('subscription_id'),
                prompt_id=trade_result.get('prompt_id'),  # Track which prompt was used
                
                # Trade Details
                action=action,
                position_side=position_side,
                symbol=trade_result.get('symbol'),
                quantity=Decimal(str(trade_result.get('quantity', 0))),
                entry_price=Decimal(str(entry_price)),
                entry_time=datetime.now(),  # Precise entry time
                leverage=int(trade_result.get('leverage', 1)),
                
                # Risk Management
                stop_loss=Decimal(str(stop_loss)) if stop_loss else None,
                take_profit=Decimal(str(take_profit)) if take_profit else None,
                risk_reward_ratio=risk_reward_ratio,
                
                # Order Info
                order_id=trade_result.get('main_order_id'),
                
                # LLM Strategy
                strategy_used=trade_result.get('strategy_name'),  # From LLM analysis
                confidence=Decimal(str(trade_result.get('confidence', 0))) if trade_result.get('confidence') else None,
                reason=trade_result.get('reason'),
                
                # Status
                status='OPEN',  # Position is now OPEN
                
                # Timestamps
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Extract and save SL/TP order IDs
            sl_order_ids = []
            tp_order_ids = []
            
            # Get SL order ID
            if trade_result.get('stop_loss') and trade_result['stop_loss'].get('order_id'):
                sl_order_id = trade_result['stop_loss']['order_id']
                if sl_order_id and sl_order_id != 'N/A' and sl_order_id != '':
                    sl_order_ids.append(str(sl_order_id))
            
            # Get TP order IDs
            if trade_result.get('take_profit') and trade_result['take_profit'].get('order_ids'):
                tp_ids = trade_result['take_profit']['order_ids']
                if isinstance(tp_ids, list):
                    for tp_id in tp_ids:
                        if tp_id and tp_id != 'N/A' and tp_id != '' and tp_id is not None:
                            tp_order_ids.append(str(tp_id))
                elif tp_ids and tp_ids != 'N/A' and tp_ids != '':
                    tp_order_ids.append(str(tp_ids))
            
            # Save order IDs to transaction
            transaction.sl_order_ids = sl_order_ids if sl_order_ids else None
            transaction.tp_order_ids = tp_order_ids if tp_order_ids else None
            
            logger.info(f"💾 Saving Binance Futures transaction with order tracking:")
            logger.info(f"   Main order ID: '{transaction.order_id}'")
            logger.info(f"   SL order IDs: {sl_order_ids}")
            logger.info(f"   TP order IDs: {tp_order_ids}")
            
            # Add to database
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            
            print(f"✅ Transaction saved to database with ID: {transaction.id} (Status: OPEN)")
            print(f"   Position: {position_side}, Entry: ${entry_price:.2f}, RR: {risk_reward_ratio or 'N/A'}")
            
        except Exception as e:
            print(f"❌ Failed to save transaction to database: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to JSON file if database fails
            try:
                import json
                from datetime import datetime
                
                transaction = {
                    'timestamp': datetime.now().isoformat(),
                    'action': trade_result.get('action'),
                    'position_side': 'LONG' if trade_result.get('action') == 'BUY' else 'SHORT',
                    'symbol': trade_result.get('symbol'),
                    'quantity': trade_result.get('quantity'),
                    'entry_price': trade_result.get('entry_price'),
                    'leverage': trade_result.get('leverage'),
                    'stop_loss': trade_result.get('stop_loss'),
                    'take_profit': trade_result.get('take_profit'),
                    'order_id': trade_result.get('main_order_id'),
                    'confidence': trade_result.get('confidence'),
                    'reason': trade_result.get('reason'),
                    'status': 'OPEN'
                }
                
                # Save to file as fallback
                filename = 'futures_transactions.json'
                try:
                    with open(filename, 'r') as f:
                        transactions = json.load(f)
                except:
                    transactions = []
                
                transactions.append(transaction)
                
                with open(filename, 'w') as f:
                    json.dump(transactions, f, indent=2)
                
                print(f"✅ Transaction saved to {filename} as fallback")
                
            except Exception as fallback_error:
                print(f"❌ Failed to save transaction to file: {fallback_error}")

async def main_execution():
    """Main execution function for real trading"""
    # Test configuration with 5 dynamic timeframes LLM integration  
    test_config = {
        'trading_pair': 'BTCUSDT',
        'testnet': True,
        'leverage': 10,
        'stop_loss_pct': 0.02,  # 2%
        'take_profit_pct': 0.04,  # 4%
        'position_size_pct': 0.1,  # 10% of balance
        
        # 🎯 Optimized 3 timeframes for better performance
        'timeframes': ['30m', '1h', '4h'],  
        'primary_timeframe': '1h',  # Primary timeframe for final decision
        
        'use_llm_analysis': True,  # Enable LLM analysis with full system
        'llm_model': 'openai',  # Primary LLM model to use
        'rsi_period': 14,
        'require_confirmation': True,  # Ask for confirmation before real trades
        'auto_confirm': False  # Auto-confirm trades (for Celery/automated execution)
    }
    
    # 🏦 PRODUCTION MODE: Exchange keys from database only
    # All Binance API keys MUST be stored in database with user principal ID
    
    # User Principal ID (REQUIRED)
    test_principal_id = "ok7jr-d6ktf-idahj-ucbcb-pg5tt-2ayc4-kjkjm-xm6qd-h4uxv-vbnrz-bqe"  # Example ICP Principal ID
    
    # LLM API keys (optional - can come from environment or config)
    llm_api_keys = {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'claude_api_key': os.getenv('CLAUDE_API_KEY'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY')
    }
    
    print("🚀 Testing Binance Futures Bot with 5 Dynamic Timeframes")
    print(f"🤖 LLM Model: {test_config['llm_model']}")
    print(f"💱 Trading Pair: {test_config['trading_pair']}")
    print(f"⚡ Leverage: {test_config['leverage']}x")
    print(f"📊 Timeframes: {test_config['timeframes']} (Total: {len(test_config['timeframes'])})")
    print(f"🎯 Primary Timeframe: {test_config['primary_timeframe']}")
    print(f"🧪 Testnet: {test_config['testnet']}")
    print(f"🔑 API Key Mode: 🏦 Database Only (Production)")
    print(f"🆔 Principal ID: {test_principal_id}")
    print(f"⚠️  Exchange keys MUST be in database for this principal ID")
    
    # Initialize bot with database-only approach
    print("\n🏦 Initializing bot with DATABASE API KEYS ONLY...")
    print(f"   Loading encrypted exchange keys for Principal ID: {test_principal_id}")
    print(f"   ⚠️  If this fails, you need to store Binance API keys in database first")
    
    try:
        # ONLY database lookup - no fallback
        bot = BinanceFuturesBot(test_config, api_keys=llm_api_keys, user_principal_id=test_principal_id)
        print("✅ Bot initialized with DATABASE KEYS successfully!")
        print("🔐 API Key Source: 🏦 Database (Encrypted Storage)")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print("\n📝 To fix this:")
        print(f"   1. Start MySQL: docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=password mysql")
        print(f"   2. Run migrations: python migrations/migration_runner.py")
        print(f"   3. Store API keys via API:")
        print(f"      curl -X POST 'http://localhost:8000/exchange-credentials/credentials' \\")
        print(f"        -H 'Content-Type: application/json' \\")
        print(f"        -d '{{\"principal_id\": \"{test_principal_id}\", \"exchange\": \"BINANCE\", \"api_key\": \"your_key\", \"api_secret\": \"your_secret\", \"is_testnet\": true}}'")
        print(f"   4. Run bot again")
        return
    
    print("\n📋 Bot Configuration Summary:")
    print(f"   API Source: Database + Encryption (Production Mode)")
    print(f"   Exchange Keys: Loaded from database for principal {test_principal_id}")
    print(f"   LLM Keys: Environment variables")
    print(f"   Testnet Mode: {'ON' if test_config['testnet'] else 'OFF'}")
    print(f"   LLM Analysis: {'ON' if test_config['use_llm_analysis'] else 'OFF'}")
    
    # Test the complete 5-timeframe trading cycle
    try:
        print("\n🔄 Running complete 5-timeframe futures trading cycle...")
        print(f"🔑 Using exchange API keys from: 🏦 Encrypted Database (Principal: {test_principal_id})")
        
        # 0. Check account status first
        print("=" * 70)
        account_status = bot.check_account_status()
        
        # 1. Crawl 5 timeframes data
        multi_timeframe_data = bot.crawl_data()
        if not multi_timeframe_data.get("timeframes"):
            print("❌ Failed to crawl multi-timeframe data")
            exit(1)
        
        timeframes_crawled = list(multi_timeframe_data['timeframes'].keys())
        print(f"📈 Successfully crawled {len(timeframes_crawled)} timeframes: {timeframes_crawled}")
        
        for tf, data in multi_timeframe_data['timeframes'].items():
            print(f"   📊 {tf}: {len(data)} candles")
        
        # 2. Analyze all 5 timeframes
        analysis = bot.analyze_data(multi_timeframe_data)
        if 'error' in analysis:
            print(f"❌ Analysis error: {analysis['error']}")
            exit(1)
        
        print(f"🔍 Analyzed {len(analysis.get('multi_timeframe', {}))} timeframes")
        
        # 3. Generate signal using 5-timeframe context
        signal = bot.generate_signal(analysis)
        
        # 4. Execute real trade with position management
        print(f"\n🚀 Step 4: Executing REAL TRADE...")
        if signal.action != "HOLD":
            print(f"⚠️  ABOUT TO PLACE REAL ORDER ON BINANCE!")
            print(f"   Action: {signal.action}")
            print(f"   Confidence: {signal.value*100:.1f}%")
            print(f"   Reason: {signal.reason}")
            
            # Ask for confirmation for safety (in testing)
            # In production or auto mode, skip confirmation
            if test_config.get('require_confirmation', True) and not test_config.get('auto_confirm', False):
                confirm = input(f"\n❓ Confirm {signal.action} trade? (yes/no): ")
                if confirm.lower() != 'yes':
                    trade_result = {
                        'status': 'cancelled',
                        'message': 'Trade cancelled by user'
                    }
                else:
                    trade_result = await bot.setup_position(signal, analysis)
            else:
                # Auto-confirm or no confirmation required
                if test_config.get('auto_confirm', False):
                    print(f"🤖 AUTO-CONFIRMED {signal.action} trade (Celery mode)")
                trade_result = await bot.setup_position(signal, analysis)
        else:
            trade_result = await bot.setup_position(signal, analysis)
        
        # 5. Save transaction if successful
        if trade_result.get('status') == 'success' and signal.action != "HOLD":
            bot.save_transaction_to_db(trade_result)
        
        # Create comprehensive result for 5 timeframes
        result = {
            'status': 'success',
            'bot_name': 'BinanceFuturesBot',
            'trading_pair': bot.trading_pair,
            'total_timeframes': len(timeframes_crawled),
            'timeframes': timeframes_crawled,
            'primary_timeframe': bot.primary_timeframe,
            'data_summary': {
                tf: {
                    'candles': len(data),
                    'price_range': f"{min(d['close'] for d in data):.2f} - {max(d['close'] for d in data):.2f}"
                }
                for tf, data in multi_timeframe_data['timeframes'].items()
            },
            'analysis_summary': {
                'current_price': analysis.get('current_price'),
                'timeframes_analyzed': len(analysis.get('multi_timeframe', {})),
                'primary_analysis': {
                    'rsi': analysis.get('primary_analysis', {}).get('rsi'),
                    'macd': analysis.get('primary_analysis', {}).get('macd'),
                    'trend_bullish': analysis.get('primary_analysis', {}).get('trend_bullish')
                }
            },
            'signal': {
                'action': signal.action,
                'confidence': f"{signal.value*100:.1f}%",
                'reason': signal.reason
            },
            'trade_result': trade_result,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add LLM recommendation if available
        if signal.recommendation:
            result['recommendation'] = signal.recommendation
            
            # Add price comparison
            current_price = analysis.get('current_price', 0)
            if current_price and 'entry_price' in trade_result:
                result['price_comparison'] = {
                    'current_market_price': current_price,
                    'recommended_entry_price': trade_result['entry_price'],
                    'price_difference': trade_result['entry_price'] - current_price,
                    'using_recommendation': True
                }
        
        print(f"\n📊 5-TIMEFRAME FUTURES TRADING RESULT:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Error during 5-timeframe futures trading cycle: {e}")
        import traceback
        traceback.print_exc()

# Factory function to create bot for production use
def create_futures_bot_for_user(user_principal_id: str, config: Dict[str, Any] = None) -> 'BinanceFuturesBot':
    """
    Factory function to create BinanceFuturesBot with API keys from database
    
    Args:
        user_principal_id: ICP Principal ID of the user
        config: Bot configuration (optional)
        
    Returns:
        Configured BinanceFuturesBot instance
    """
    default_config = {
        'trading_pair': 'BTCUSDT',
        'testnet': True,  # Default to testnet for safety
        'leverage': 10,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.04,
        'position_size_pct': 0.05,
        'timeframes': ['1h', '4h', '1d'],
        'primary_timeframe': '1h',
        'use_llm_analysis': True,
        'llm_model': 'openai'
    }
    
    # Merge with provided config
    if config:
        default_config.update(config)
    
    # Create bot with principal ID (will load API keys from database)
    return BinanceFuturesBot(default_config, user_principal_id=user_principal_id)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_execution())
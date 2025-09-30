"""
Binance Futures Trading Bot with RPA + LLM Image Analysis
Advanced futures trading bot using RPA for chart capture and LLM for image analysis
Uses RPA to capture trading charts and OpenAI/Claude/Gemini for intelligent trading decisions
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
import uuid
import subprocess
from datetime import datetime
from dataclasses import dataclass

# Import necessary modules
from bots.bot_sdk import CustomBot, Action
from services.llm_integration import create_llm_service
from bot_files.capital_management import CapitalManagement, RiskMetrics, PositionSizeRecommendation
from core.api_key_manager import get_bot_api_keys

# Import for image analysis
from services.image_analysis import analyze_image_with_openai
from core.schemas import PayLoadAnalysis

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
        logger.info(f"testnet = {testnet}")
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
            logger.error(f"⚠️ Futures API request failed: {e}")
            if e.response is not None:
                try:
                    data = e.response.json()
                    logger.error(f"❌ Binance API error {data.get('code')}: {data.get('msg')}")
                    if data.get("code") == -1021:  # Timestamp error
                        logger.warning("⏱️ Timestamp error (-1021), resyncing server time and retrying...")
                        self._sync_server_time()
                        return self._make_request(method, endpoint, params, signed, recv_window)
                    elif data.get("code") in [-1001, -1003]:  # Internal error / Rate limit
                        time.sleep(1)
                        return self._make_request(method, endpoint, params, signed, recv_window)
                except Exception:
                    logger.error(f"❌ Non-JSON response: {e.response.text}")
            raise
    
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
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> FuturesOrderInfo:
        """Create futures market order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity
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
        from decimal import Decimal, ROUND_DOWN, getcontext
        getcontext().prec = 28

        try:
            # --- normalize inputs to Decimal
            stop_price = Decimal(str(stop_price))
            take_profit_price = Decimal(str(take_profit_price))
            total_qty = Decimal(str(quantity))

            # Get current price for validation
            current_ticker = self.get_ticker(symbol)
            current_price = Decimal(str(current_ticker['price']))

            # fetch symbol filters from exchangeInfo (robust: try best-effort)
            try:
                ei = self._make_request("GET", "/fapi/v1/exchangeInfo", {"symbol": symbol}, signed=False)
                # ei may contain 'symbols' list
                sym = None
                if isinstance(ei, dict) and "symbols" in ei:
                    sym = next((s for s in ei["symbols"] if s.get("symbol") == symbol), None)
                elif isinstance(ei, dict) and ei.get("symbol") == symbol:
                    sym = ei
            except Exception:
                sym = None

            if sym:
                price_filter = next((f for f in sym.get("filters", []) if f.get("filterType") == "PRICE_FILTER"), {})
                lot_filter = next((f for f in sym.get("filters", []) if f.get("filterType") == "LOT_SIZE"), {})
                min_notional_filter = next((f for f in sym.get("filters", []) if f.get("filterType") == "MIN_NOTIONAL"), None)

                tick_size = Decimal(str(price_filter.get("tickSize", "0.1")))
                step_size = Decimal(str(lot_filter.get("stepSize", "0.001")))
                min_qty = Decimal(str(lot_filter.get("minQty", "0.001")))
                min_notional = Decimal(str(min_notional_filter.get("notional", "0"))) if min_notional_filter else Decimal("0")
            else:
                # safe defaults (adjust if your asset differs)
                tick_size = Decimal("0.1")
                step_size = Decimal("0.001")
                min_qty = Decimal("0.001")
                min_notional = Decimal("0")

            # helpers
            def floor_to_step(v: Decimal, step: Decimal) -> Decimal:
                return (v // step) * step

            def format_for_api(v: Decimal, step: Decimal) -> str:
                # determine decimal places from step (e.g. 0.001 -> 3 decimals)
                exp = -step.as_tuple().exponent
                if exp < 0:
                    exp = 0
                quant = Decimal('1e-{}'.format(exp))
                return str(v.quantize(quant, rounding=ROUND_DOWN))

            # Validate total qty meets min requirements
            total_qty = floor_to_step(total_qty, step_size)
            if total_qty <= 0 or total_qty < min_qty:
                raise ValueError(f"Quantity {total_qty} invalid after rounding — below min_qty {min_qty}")

            # Validate total notional if required
            if min_notional > 0 and (total_qty * current_price) < min_notional:
                raise ValueError(f"Order notional {total_qty * current_price} below min_notional {min_notional}")

            # safe split: avoid creating parts smaller than step_size
            half = Decimal('0.5')
            partial_qty = floor_to_step(total_qty * half, step_size)
            remaining_qty = total_qty - partial_qty

            # If split produces too-small piece, fallback to single TP
            if partial_qty < step_size or remaining_qty < step_size:
                partial_qty = total_qty
                remaining_qty = Decimal('0')

            # adjust stop / tp prices to tick size
            stop_price = floor_to_step(stop_price, tick_size)
            tp1_price = floor_to_step(take_profit_price, tick_size)

            # compute tp2 based on side (keep previous logic)
            if side == "BUY":
                tp2_price = tp1_price * Decimal('0.98')
            else:
                tp2_price = tp1_price * Decimal('1.02')

            # ensure tp2 relationship to current price (fallback rules)
            current_price = Decimal(str(self.get_ticker(symbol)['price']))
            if side == "BUY" and tp2_price >= current_price:
                tp2_price = (current_price * Decimal('0.99'))
            elif side == "SELL" and tp2_price <= current_price:
                tp2_price = (current_price * Decimal('1.01'))

            tp2_price = floor_to_step(tp2_price, tick_size)

            logger.info(f"Creating managed orders with total_qty={total_qty}, partial_qty={partial_qty}, remaining_qty={remaining_qty}")
            created_orders = []

            # Build params with correct formatting
            stop_params = {
                'symbol': symbol,
                'side': side,
                'type': 'STOP_MARKET',
                'quantity': format_for_api(total_qty, step_size),
                'stopPrice': format_for_api(stop_price, tick_size),
                'timeInForce': 'GTC'
            }
            if reduce_only:
                stop_params['reduceOnly'] = 'true'

            # send stop order first
            stop_response = self._make_request("POST", "/fapi/v1/order", stop_params, signed=True)
            created_orders.append(stop_response)

            # TP1
            tp1_params = {
                'symbol': symbol,
                'side': side,
                'type': 'TAKE_PROFIT_MARKET',
                'quantity': format_for_api(partial_qty, step_size),
                'stopPrice': format_for_api(tp1_price, tick_size),
                'timeInForce': 'GTC'
            }
            if reduce_only:
                tp1_params['reduceOnly'] = 'true'

            tp1_response = self._make_request("POST", "/fapi/v1/order", tp1_params, signed=True)
            created_orders.append(tp1_response)

            # TP2 (only if there's remaining_qty)
            tp2_response = None
            if remaining_qty >= step_size:
                # check min notional for tp2
                if min_notional > 0 and (remaining_qty * tp2_price) < min_notional:
                    # if tp2 would violate min_notional, skip tp2
                    logger.warning("Skipping TP2 because notional < min_notional after normalization.")
                else:
                    tp2_params = {
                        'symbol': symbol,
                        'side': side,
                        'type': 'TAKE_PROFIT_MARKET',
                        'quantity': format_for_api(remaining_qty, step_size),
                        'stopPrice': format_for_api(tp2_price, tick_size),
                        'timeInForce': 'GTC'
                    }
                    if reduce_only:
                        tp2_params['reduceOnly'] = 'true'
                    tp2_response = self._make_request("POST", "/fapi/v1/order", tp2_params, signed=True)
                    created_orders.append(tp2_response)

            logger.info(f"✅ Managed Orders Created:")
            logger.info(f"🛡️ Stop Loss: {stop_response.get('orderId')} (Full: {format_for_api(total_qty, step_size)})")
            logger.info(f"🎯 Take Profit 1: {tp1_response.get('orderId')} (Partial: {format_for_api(partial_qty, step_size)} @ ${format_for_api(tp1_price, tick_size)})")
            if tp2_response:
                logger.info(f"🎯 Take Profit 2: {tp2_response.get('orderId')} (Profit: {format_for_api(remaining_qty, step_size)} @ ${format_for_api(tp2_price, tick_size)})")

            return {
                'stop_loss_order': {
                    'order_id': stop_response.get('orderId'),
                    'quantity': float(total_qty),
                    'price': float(stop_price)
                },
                'take_profit_orders': [
                    {
                        'order_id': tp1_response.get('orderId'),
                        'quantity': float(partial_qty),
                        'price': float(tp1_price),
                        'type': 'partial'
                    }
                ] + ([{
                        'order_id': tp2_response.get('orderId'),
                        'quantity': float(remaining_qty),
                        'price': float(tp2_price),
                        'type': 'profit'
                    }] if tp2_response else [])
            }

        except Exception as e:
            # try to cancel any created orders to avoid "dangling" orders
            try:
                if 'created_orders' in locals():
                    for o in created_orders:
                        try:
                            self.cancel_order(symbol, int(o.get('orderId')))
                        except Exception:
                            pass
            except Exception:
                pass

            logger.error(f"Failed to create managed orders: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"Binance API response: {e.response.text}")
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

class BinanceFuturesRPABot(CustomBot):
    """Advanced Binance Futures Trading Bot with RPA + LLM Image Analysis"""
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str] = None, user_principal_id: str = None, subscription_id: int = None):
        """Initialize Futures Trading Bot with RPA"""
        super().__init__(config, api_keys)
        
        # Futures specific configuration
        self.trading_pair = config.get('trading_pair', 'BTC_USDT')
        self.leverage = config.get('leverage', 5)  # Safer default leverage
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)  # 2% stop loss
        self.take_profit_pct = config.get('take_profit_pct', 0.04)  # 4% take profit
        self.position_size_pct = config.get('position_size_pct', 0.1)  # 10% of balance
        self.testnet = config.get('testnet', True)  # Add testnet attribute
        
        # RPA configuration
        self.rpa_timeout = config.get('rpa_timeout', 300)
        self.screenshot_dir = config.get('screenshot_dir', '/app/screenshots')
        self.robot_file = config.get('robot_file', os.path.abspath("binance.robot"))
        self.driver_path = config.get('driver_path', os.path.abspath("drivers"))
        
        # Strategy configuration
        self.main_indicators = config.get('main_indicators', ['RSI', 'MACD', 'Volume'])
        self.sub_indicators = config.get('sub_indicators', [])
        
        # Timeframe configuration
        self.timeframes = config.get('timeframes', ['1h', '4h'])
        self.primary_timeframe = config.get('primary_timeframe', '1h')
        
        # LLM configuration
        self.llm_model = config.get('llm_model', 'openai')  # Default to OpenAI
        self.use_llm_analysis = config.get('use_llm_analysis', True)  # Enable LLM by default
        
        # Initialize futures client - ONLY database lookup for exchange keys
        if not user_principal_id:
            raise ValueError("user_principal_id is required - all exchange API keys must come from database")
        
        # Store user principal ID for this bot instance
        self.user_principal_id = user_principal_id
        logger.info(f"Bot initialized for principal ID: {self.user_principal_id}")
        logger.info(f"robot file with name {self.robot_file}")
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
        client_testnet = True
        
        logger.info(f"✅ Loaded encrypted Binance API keys from database for principal ID: {user_principal_id}")
        
        self.futures_client = BinanceFuturesIntegration(
            api_key=client_api_key,
            api_secret=client_api_secret,
            testnet=client_testnet
        )
        
        # Initialize LLM service
        self.llm_service = None
        if self.use_llm_analysis:
            try:
                # LLM keys can come from api_keys parameter or environment variables
                llm_config = {
                    'openai_api_key': os.getenv('OPENAI_API_KEY'),
                    'claude_api_key': os.getenv('CLAUDE_API_KEY'),
                    'gemini_api_key': os.getenv('GEMINI_API_KEY'),
                    'openai_model': config.get('openai_model', 'gpt-4o'),
                    'claude_model': config.get('claude_model', 'claude-3-5-sonnet-20241022'),
                    'gemini_model': config.get('gemini_model', 'gemini-1.5-pro')
                }
                self.llm_service = create_llm_service(llm_config)
                logger.info(f"LLM service initialized with model: {self.llm_model}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
                self.use_llm_analysis = False
                logger.warning("LLM analysis disabled")
        
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
        
        logger.info(f"Initialized BinanceFuturesRPABot for {self.trading_pair} with {self.leverage}x leverage")
        logger.info(f"RPA Configuration: {self.robot_file}")
        logger.info(f"Main Indicators: {self.main_indicators}")
        logger.info(f"Sub Indicators: {self.sub_indicators}")
    
    def capture_chart_data(self) -> List[str]:
        """Sử dụng RPA để chụp biểu đồ trading view"""
        try:
            session_id = str(uuid.uuid4())
            trading_pair = self.trading_pair
            
            # Add driver path to environment
            os.environ["PATH"] += os.pathsep + self.driver_path
            
            env = os.environ.copy()
            env["BROWSER"] = "chrome"
            
            logger.info(f"Starting RPA process with session ID: {session_id}")
            logger.info(f"Trading pair: {trading_pair}, Timeframes: {self.timeframes}")
            logger.info(f"Main indicators: {self.main_indicators}, Sub indicators: {self.sub_indicators}")
            
            # Run RPA process
            result = subprocess.run([
                "robot",
                "--variable", f"session_id:{session_id}",
                "--variable", f"trading_pair:{trading_pair}",
                "--variable", f"timeframe:{json.dumps(self.timeframes)}",
                "--variable", f"main_indicators:{json.dumps(self.main_indicators)}",
                "--variable", f"sub_indicators:{json.dumps(self.sub_indicators)}",
                self.robot_file
            ], capture_output=True, text=True, env=env, timeout=self.rpa_timeout)
            
            logger.info(f"RPA process completed with return code: {result.returncode}")
            logger.info(f"RPA process completed with result: {result}")
            
            if result.returncode != 0:
                logger.error(f"RPA process failed: {result.stderr}")
                return []
            
            # Read image paths from file
            image_path_file = os.path.join(self.screenshot_dir, f"{session_id}_image.txt")
            
            # Wait for file to be created
            max_retries = 10
            retry_delay = 0.5
            
            for attempt in range(max_retries):
                if os.path.exists(image_path_file):
                    with open(image_path_file, "r") as f:
                        content = f.read().strip()
                        image_paths = [line.strip() for line in content.splitlines() if line.strip()]
                    
                    # Clean up the file
                    os.remove(image_path_file)
                    
                    if not image_paths:
                        logger.warning("No images found in the session file")
                        return []
                    
                    logger.info(f"Successfully captured {len(image_paths)} images")
                    return image_paths
                
                logger.info(f"Waiting for session file... Attempt {attempt + 1}/{max_retries}")
                time.sleep(retry_delay)
            
            logger.error("Timeout waiting for RPA screenshot file")
            return []
            
        except subprocess.TimeoutExpired:
            logger.error(f"RPA process timed out after {self.rpa_timeout} seconds")
            return []
        except Exception as e:
            logger.error(f"Error in RPA chart capture: {e}")
            return []
    
    async def analyze_images_with_llm(self, image_paths: List[str]) -> Action:
        """Phân tích hình ảnh với LLM và tạo tín hiệu giao dịch"""
        try:
            if not image_paths:
                return Action(action="HOLD", value=0.0, reason="No images to analyze")
            
            bot_config = PayLoadAnalysis(
                bot_name="BinanceFuturesRPABot",
                trading_pair=self.trading_pair,
                timeframes=self.timeframes,
                primary_timeframe=self.primary_timeframe,
                strategies=self.main_indicators + self.sub_indicators,
                custom_prompt="Analyze the trading charts and provide a trading recommendation with entry, stop loss, and take profit levels."
            )
            
            analysis_result = analyze_image_with_openai(image_paths, bot_config)
            logger.info(f"Image analysis result: {analysis_result}")
            if 'analysis_result' in analysis_result and analysis_result['analysis_result']:
                # Nếu có kết quả phân tích từ LLM
                llm_result = analysis_result['analysis_result'].get("recommendation", {})
                logger.info(f"LLM Analysis Result: {llm_result}")
                action_str = llm_result.get('action', 'HOLD')
                confidence = float(llm_result.get('confidence', 50)) / 100.0
                reason = llm_result.get('reasoning', 'No reason provided')
                
                return Action(
                    action=action_str,
                    value=confidence,
                    reason=reason,
                    recommendation=llm_result
                )
            else:
                logger.info("No analysis result from LLM, defaulting to HOLD")
                # Fallback parsing nếu không có analysis_result
                return self._parse_llm_image_analysis(analysis_result.get('raw_response', ''))
            
        except Exception as e:
            logger.error(f"Error in LLM image analysis: {e}")
            return Action(action="HOLD", value=0.0, reason=f"LLM analysis error: {e}")
    
    def _parse_llm_image_analysis(self, analysis_text: str) -> Action:
        """Phân tích kết quả từ LLM và chuyển thành Action"""
        try:
            # Simple keyword-based parsing - you can enhance this with more sophisticated NLP
            analysis_lower = analysis_text.lower()
            
            # Extract action
            if "buy" in analysis_lower or "long" in analysis_lower:
                action = "BUY"
            elif "sell" in analysis_lower or "short" in analysis_lower:
                action = "SELL"
            else:
                action = "HOLD"
            
            # Extract confidence (simple heuristic)
            confidence = 0.5  # Default
            if "strong" in analysis_lower:
                confidence = 0.8
            elif "weak" in analysis_lower:
                confidence = 0.3
            
            # Extract entry, stop loss, and take profit from the analysis
            # This is a simple implementation - you might want to use more sophisticated parsing
            entry_price = None
            stop_loss = None
            take_profit = None
            
            # Look for price patterns in the text
            import re
            price_pattern = r'\$?(\d+\.?\d*)'
            prices = re.findall(price_pattern, analysis_text)
            if len(prices) >= 3:
                try:
                    entry_price = float(prices[0])
                    stop_loss = float(prices[1])
                    take_profit = float(prices[2])
                except (ValueError, IndexError):
                    pass
            
            # Create recommendation dictionary
            recommendation = {
                "action": action,
                "confidence": f"{confidence*100:.1f}%",
                "entry_price": f"{entry_price}" if entry_price else "Market",
                "stop_loss": f"{stop_loss}" if stop_loss else "N/A",
                "take_profit": f"{take_profit}" if take_profit else "N/A",
                "strategy": "RPA+LLM Image Analysis",
                "risk_reward": "1:2" if stop_loss and take_profit and entry_price else "N/A",
                "reasoning": analysis_text[:200] + "..." if len(analysis_text) > 200 else analysis_text
            }
            
            logger.info(f"LLM Analysis Result: {action} with {confidence*100:.1f}% confidence")
            
            return Action(
                action=action,
                value=confidence,
                reason=analysis_text,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Error parsing LLM analysis: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Error parsing LLM analysis: {e}")
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """Execute futures trading algorithm using RPA + LLM"""
        try:
            logger.info("Executing RPA + LLM algorithm...")
            
            # Bước 1: Chụp biểu đồ bằng RPA
            image_paths = self.capture_chart_data()
            
            if not image_paths:
                return Action(action="HOLD", value=0.0, reason="Failed to capture chart data")
            
            # Bước 2: Phân tích hình ảnh với LLM
            # Chạy async trong sync context
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                action = loop.run_until_complete(self.analyze_images_with_llm(image_paths))
                return action
            finally:
                loop.close()
                # Clean up images
                self.cleanup_images(image_paths)
                
        except Exception as e:
            logger.error(f"Error in RPA+LLM algorithm: {e}")
            return Action(action="HOLD", value=0.0, reason=f"RPA+LLM algorithm error: {e}")
    
    def cleanup_images(self, image_paths: List[str]):
        """Dọn dẹp ảnh đã sử dụng"""
        for img_path in image_paths:
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                    logger.debug(f"Cleaned up image: {img_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up image {img_path}: {e}")
    
    async def setup_position(self, action: Action, analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Setup futures position with intelligent capital management and stop loss/take profit"""
        try:
            if action.action == "HOLD":
                return {
                    'status': 'success',
                    'action': 'HOLD',
                    'reason': action.reason
                }
            
            # Get account information for capital management
            account_info = self.futures_client.get_account_info()
            available_balance = float(account_info.get('availableBalance', 0))
            
            if available_balance <= 0:
                return {'status': 'error', 'message': 'No available balance for trading'}
            
            # Calculate risk metrics for position sizing
            risk_metrics = self.capital_manager.calculate_risk_metrics(account_info)
            
            # Get current price for fallback
            logger.info(f"first trading pair: {self.trading_pair}")
            symbol = normalize_symbol(self.trading_pair)
            logger.info(f"Fetching current price for {symbol}...")
            current_ticker = self.futures_client.get_ticker(symbol)
            current_price = float(current_ticker['price'])
            
            # Prepare market data for capital management
            market_data = {
                'current_price': current_price,
                'atr': 0,  # Not used in RPA mode
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
                    
                    # Parse take profit
                    tp_str = rec.get('take_profit', '').replace(',', '').strip()
                    if tp_str and tp_str != 'N/A':
                        take_profit_target = float(tp_str)
                    
                    # Parse stop loss
                    sl_str = rec.get('stop_loss', '').replace(',', '').strip()
                    if sl_str and sl_str != 'N/A':
                        stop_loss_target = float(sl_str)
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse recommendation prices in setup_position: {e}")
                if take_profit_target:
                    take_profit_target = normalize_price(take_profit_target, current_price)
                if stop_loss_target:
                    stop_loss_target = normalize_price(stop_loss_target, current_price)
                if entry_price:
                    entry_price = normalize_price(entry_price, current_price)
            
            # Fallback to current market price
            if not entry_price:
                if current_price <= 0:
                    return {'status': 'error', 'message': 'Invalid current price'}
                entry_price = current_price
            
            # Setup leverage
            raw_symbol = self.trading_pair
            symbol = raw_symbol.replace("/", "").replace("_", "").upper()
            if not self.futures_client.set_leverage(symbol, self.leverage):
                logger.warning(f"Failed to set leverage, continuing with current leverage")
            
            # Calculate position size using capital management recommendation
            position_value = available_balance * optimal_position_size_pct * self.leverage
            quantity = position_value / entry_price
            
            # Round to proper precision
            quantity = round(quantity, 3)
            quantity_str = f"{quantity:.3f}"
            # test_quantity = 0.001
            # quantity_str = f"{test_quantity:.3f}"
            
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
                logger.info(f"stop loss target is {stop_loss_target}, take profit target is {take_profit_target}")
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
            logger.info(f"action is {action.action}, side is {sl_side}")
            # 🔗 Place OCO order (One-Cancels-Other) with STOP_MARKET and TAKE_PROFIT_MARKET
            try:
                # Get current market price for validation
                current_market_price = current_price
                
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
                logger.info(
                    f"Placing managed orders with SL @ ${adjusted_stop_price:.2f} and TP @ ${adjusted_tp_price:.2f}"
                    f" for {quantity_str} {symbol} ({sl_side})"
                )
                try:
                    managed_orders = self.futures_client.create_managed_orders(
                        symbol=symbol,
                        side=sl_side,
                        quantity=quantity_str,
                        stop_price=f"{adjusted_stop_price:.2f}",
                        take_profit_price=f"{adjusted_tp_price:.2f}",
                        reduce_only=True
                    )
                    sl_order = managed_orders['stop_loss_order']
                    tp_orders = managed_orders['take_profit_orders']
                except Exception as e:
                    logger.error(f"Failed to create managed orders: {e}")
                    # Place individual orders as fallback
                    sl_order = self.futures_client.create_stop_loss_order(...)
                    tp_orders = [self.futures_client.create_take_profit_order(...)]
                
                logger.info(f"✅ Managed Orders placed successfully:")
                logger.info(f"🛡️ Stop Loss: {sl_order.get('order_id', 'N/A')} @ ${adjusted_stop_price:.2f}")
                logger.info(f"🎯 Take Profit 1: {tp_orders[0].get('order_id', 'N/A')} (50% @ ${tp_orders[0].get('price', 'N/A')})")
                # logger.info(f"🎯 Take Profit 2: {tp_orders[1].get('order_id', 'N/A')} (50% @ ${tp_orders[1].get('price', 'N/A')})")
                if tp_orders and len(tp_orders) > 1:
                    logger.info(f"🎯 Take Profit 2: {tp_orders[1].get('order_id', 'N/A')} (50% @ ${tp_orders[1].get('price', 'N/A')})")
                else:
                    logger.info("🎯 Take Profit 2: Not placed (remaining quantity too small)")
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
                    'order_ids': [tp.get('order_id') for tp in tp_orders] if tp_orders else [None],
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

    def check_account_status(self):
        try:
            print("\n💼 CHECKING BINANCE ACCOUNT STATUS...")
            print("=" * 50)

            account_info = self.futures_client.get_account_info()
            available_balance = float(account_info.get('availableBalance', 0))
            total_wallet_balance = float(account_info.get('totalWalletBalance', 0))

            mode = "🧪 TESTNET" if self.testnet else "🔴 LIVE"
            print(f"{mode} Account Balance:")
            print(f"   💰 Available: ${available_balance:,.2f} USDT")
            print(f"   💎 Total Wallet: ${total_wallet_balance:,.2f} USDT")

            positions = self.futures_client.get_positions()
            active_positions = len([p for p in positions if float(getattr(p, "size", 0)) != 0])
            
            print(f"   📊 Active Positions: {active_positions}")
            
            return {
                'available_balance': available_balance,
                'total_balance': total_wallet_balance,
                'active_positions': active_positions,
                'positions': positions
            }

        except Exception as e:
            msg = str(e)
            if "-1021" in msg or "Timestamp" in msg:
                print("🔄 Resync time & retry...")
                try:
                    self.futures_client._sync_server_time()
                    return self.check_account_status()
                except Exception:
                    pass
            print(f"❌ Failed to check account: {e}")
            return None

    def save_transaction_to_db(self, trade_result: Dict[str, Any]):
        """Save trade transaction to database"""
        try:
            # This would connect to your database and save transaction
            # For now, save to local JSON file for tracking
            import json
            from datetime import datetime
            
            transaction = {
                'timestamp': datetime.now().isoformat(),
                'action': trade_result.get('action'),
                'symbol': trade_result.get('symbol'),
                'quantity': trade_result.get('quantity'),
                'entry_price': trade_result.get('entry_price'),
                'leverage': trade_result.get('leverage'),
                'stop_loss': trade_result.get('stop_loss'),
                'take_profit': trade_result.get('take_profit'),
                'order_id': trade_result.get('main_order_id'),
                'confidence': trade_result.get('confidence'),
                'reason': trade_result.get('reason')
            }
            
            # Save to file
            filename = 'futures_rpa_transactions.json'
            try:
                with open(filename, 'r') as f:
                    transactions = json.load(f)
            except:
                transactions = []
            
            transactions.append(transaction)
            
            with open(filename, 'w') as f:
                json.dump(transactions, f, indent=2)
            
            print(f"✅ Transaction saved to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save transaction: {e}")

async def main_rpa_execution():
    """Main execution function for RPA trading"""
    # Test configuration for RPA + LLM
    test_config = {
        'trading_pair': 'BTCUSDT',
        'testnet': True,
        'leverage': 10,
        'stop_loss_pct': 0.02,  # 2%
        'take_profit_pct': 0.04,  # 4%
        'position_size_pct': 0.1,  # 10% of balance
        
        # RPA configuration
        'rpa_timeout': 300,
        'screenshot_dir': '/app/screenshots',
        'robot_file': os.path.abspath("binance.robot"),
        'driver_path': os.path.abspath("drivers"),
        
        # Strategy configuration
        'main_indicators': ['RSI', 'MACD', 'Volume'],
        'sub_indicators': ['Moving Average'],
        'timeframes': ['1h', '4h'],
        
        'use_llm_analysis': True,
        'llm_model': 'openai',
        'require_confirmation': True,
        'auto_confirm': False
    }
    
    # User Principal ID (REQUIRED)
    test_principal_id = "your_principal_id_here"
    
    # LLM API keys
    llm_api_keys = {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'claude_api_key': os.getenv('CLAUDE_API_KEY'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY')
    }
    
    print("🚀 Testing Binance Futures RPA Bot with LLM Image Analysis")
    print(f"🤖 LLM Model: {test_config['llm_model']}")
    print(f"💱 Trading Pair: {test_config['trading_pair']}")
    print(f"⚡ Leverage: {test_config['leverage']}x")
    print(f"📊 RPA Indicators: {test_config['main_indicators']}")
    print(f"🧪 Testnet: {test_config['testnet']}")
    
    # Initialize bot
    try:
        bot = BinanceFuturesRPABot(test_config, api_keys=llm_api_keys, user_principal_id=test_principal_id)
        print("✅ Bot initialized successfully!")
        
    except Exception as e:
        print(f"❌ Failed to initialize bot: {e}")
        return
    
    # Test the complete RPA trading cycle
    try:
        print("\n🔄 Running complete RPA + LLM trading cycle...")
        
        # 0. Check account status first
        print("=" * 70)
        account_status = bot.check_account_status()
        
        # 1. Execute RPA + LLM algorithm
        action = bot.execute_algorithm(pd.DataFrame(), '1h')
        
        print(f"📊 RPA+LLM Analysis Result: {action.action} with {action.value*100:.1f}% confidence")
        print(f"📝 Reason: {action.reason}")
        
        # 2. Execute trade if not HOLD
        if action.action != "HOLD":
            print(f"\n🚀 Step 2: Executing REAL TRADE...")
            print(f"⚠️  ABOUT TO PLACE REAL ORDER ON BINANCE!")
            print(f"   Action: {action.action}")
            print(f"   Confidence: {action.value*100:.1f}%")
            print(f"   Reason: {action.reason}")
            
            # Ask for confirmation for safety
            if test_config.get('require_confirmation', True) and not test_config.get('auto_confirm', False):
                confirm = input(f"\n❓ Confirm {action.action} trade? (yes/no): ")
                if confirm.lower() != 'yes':
                    trade_result = {
                        'status': 'cancelled',
                        'message': 'Trade cancelled by user'
                    }
                else:
                    trade_result = await bot.setup_position(action)
            else:
                trade_result = await bot.setup_position(action)
        else:
            trade_result = await bot.setup_position(action)
        
        # 3. Save transaction if successful
        if trade_result.get('status') == 'success' and action.action != "HOLD":
            bot.save_transaction_to_db(trade_result)
        
        # Create comprehensive result
        result = {
            'status': 'success',
            'bot_name': 'BinanceFuturesRPABot',
            'trading_pair': bot.trading_pair,
            'action': action.action,
            'confidence': f"{action.value*100:.1f}%",
            'reason': action.reason,
            'trade_result': trade_result,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n📊 RPA+LLM TRADING RESULT:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Error during RPA+LLM trading cycle: {e}")
        import traceback
        traceback.print_exc()

# Factory function to create RPA bot for production use
def create_rpa_bot_for_user(user_principal_id: str, config: Dict[str, Any] = None) -> 'BinanceFuturesRPABot':
    """
    Factory function to create BinanceFuturesRPABot with API keys from database
    
    Args:
        user_principal_id: ICP Principal ID of the user
        config: Bot configuration (optional)
        
    Returns:
        Configured BinanceFuturesRPABot instance
    """
    default_config = {
        'trading_pair': 'BTCUSDT',
        'testnet': True,
        'leverage': 10,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.04,
        'position_size_pct': 0.05,
        'rpa_timeout': 300,
        'screenshot_dir': '/app/screenshots',
        'main_indicators': ['RSI', 'MACD', 'Volume'],
        'sub_indicators': [],
        'timeframes': ['1h', '4h'],
        'use_llm_analysis': True,
        'llm_model': 'openai'
    }
    
    # Merge with provided config
    if config:
        default_config.update(config)
    
    # Create bot with principal ID
    return BinanceFuturesRPABot(default_config, user_principal_id=user_principal_id)
def normalize_symbol(symbol: str) -> str:
    return symbol.replace("/", "").replace("_", "").upper()

def normalize_price(target: float, current_price: float) -> float:
    """Scale target nếu bị lệch quá xa so với giá thị trường"""
    if target <= 0:
        return current_price
    
    # Nếu target < 1000 trong khi giá > 10000 -> nhân lên 1000 lần
    if current_price > 10000 and target < 1000:
        return target * 1000
    
    # Nếu target > 100000 trong khi giá ~10000 -> chia xuống
    if current_price < 10000 and target > 100000:
        return target / 1000
    
    return target

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_rpa_execution())
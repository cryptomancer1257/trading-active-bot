"""
Binance Integration Module
Handles real trading operations with Binance API
"""

import hashlib
import hmac
import time
import requests
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OrderInfo:
    order_id: int
    client_order_id: str
    symbol: str
    side: str
    type: str
    quantity: str
    price: str
    status: str
    executed_qty: str

@dataclass
class BalanceInfo:
    asset: str
    free: str
    locked: str

class BinanceIntegration:
    """Real Binance API integration for trading operations"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # API endpoints
        if testnet:
            self.base_url = "https://testnet.binance.vision"
        else:
            self.base_url = "https://api.binance.com"
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for API requests"""
        # Sort parameters by key to ensure consistent signature
        sorted_params = sorted(params.items())
        query_string = '&'.join([f"{key}={value}" for key, value in sorted_params])
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"Query string for signature: {query_string}")
        logger.debug(f"Generated signature: {signature}")
        
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, signed: bool = False) -> Dict[str, Any]:
        """Make authenticated request to Binance API - FIXED VERSION"""
        if params is None:
            params = {}
        
        if signed:
            # Use server time to avoid timestamp issues
            server_time = self._get_server_time()
            params['timestamp'] = server_time
            
            # Add recvWindow for POST requests to allow some clock skew
            if method == "POST":
                params['recvWindow'] = 60000  # 60 seconds window
            
            # Create query string manually to avoid encoding issues
            sorted_params = sorted(params.items())
            query_string = '&'.join([f"{key}={value}" for key, value in sorted_params])
            
            # Generate signature
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Create final query string with signature
            final_query = f"{query_string}&signature={signature}"
            
            logger.debug(f"Query string for signature: {query_string}")
            logger.debug(f"Generated signature: {signature}")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            # Headers with proper Content-Type
            headers = {
                'X-MBX-APIKEY': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            if method == "GET":
                if signed:
                    response = self.session.get(f"{url}?{final_query}", headers=headers, timeout=10)
                else:
                    response = self.session.get(url, params=params, timeout=10)
            elif method == "POST":
                if signed:
                    # Send as raw data to avoid any encoding issues
                    response = self.session.post(url, data=final_query, headers=headers, timeout=10)
                else:
                    response = self.session.post(url, data=params, headers=headers, timeout=10)
            elif method == "DELETE":
                if signed:
                    response = self.session.delete(url, data=final_query, headers=headers, timeout=10)
                else:
                    response = self.session.delete(url, data=params, headers=headers, timeout=10)
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            # Check for Binance API errors before raising for status
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    logger.error(f"Binance API error: {error_data}")
                    raise Exception(f"Binance API error: {error_data.get('msg', 'Unknown error')}")
                except ValueError:
                    logger.error(f"Binance API error - raw response: {response.text}")
                    raise Exception(f"Binance API error: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            raise Exception("Request timeout - please try again")
        except requests.exceptions.RequestException as e:
            logger.error(f"Binance API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    raise Exception(f"Binance API error: {error_data.get('msg', str(e))}")
                except ValueError:
                    pass
            raise Exception(f"Binance API error: {e}")
    
    def _get_server_time(self) -> int:
        """Get Binance server time to avoid timestamp issues"""
        try:
            response = self._make_request("GET", "/api/v3/time")
            server_time = response['serverTime']
            logger.debug(f"Server time: {server_time}")
            return server_time
        except Exception as e:
            logger.warning(f"Failed to get server time, using local time: {e}")
            # Add small buffer to local time to prevent timing issues
            local_time = int(time.time() * 1000)
            return local_time - 1000  # Subtract 1 second buffer
    
    def test_connectivity(self) -> bool:
        """Test connection to Binance API"""
        try:
            response = self._make_request("GET", "/api/v3/ping")
            return True
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            return self._make_request("GET", "/api/v3/account", signed=True)
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    def get_balance(self, asset: str = "USDT") -> BalanceInfo:
        """Get balance for specific asset"""
        try:
            account_info = self.get_account_info()
            
            # Check if balances exist and is a list
            if 'balances' not in account_info:
                logger.warning(f"No 'balances' key in account info for {asset}")
                return BalanceInfo(asset=asset, free="0", locked="0")
                
            balances = account_info['balances']
            if not isinstance(balances, list) or len(balances) == 0:
                logger.warning(f"Empty or invalid balances list for {asset}")
                return BalanceInfo(asset=asset, free="0", locked="0")
            
            for balance in balances:
                if balance.get('asset') == asset:
                    return BalanceInfo(
                        asset=balance['asset'],
                        free=balance.get('free', '0'),
                        locked=balance.get('locked', '0')
                    )
            
            # Asset not found - return zero balance instead of error
            logger.info(f"Asset {asset} not found in account, returning zero balance")
            return BalanceInfo(asset=asset, free="0", locked="0")
            
        except Exception as e:
            logger.error(f"Failed to get balance for {asset}: {e}")
            # Return zero balance instead of raising exception
            return BalanceInfo(asset=asset, free="0", locked="0")
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        try:
            response = self._make_request("GET", "/api/v3/ticker/price", {
                'symbol': symbol
            })
            return float(response['price'])
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information including filters"""
        try:
            response = self._make_request("GET", "/api/v3/exchangeInfo")
            for symbol_info in response['symbols']:
                if symbol_info['symbol'] == symbol:
                    return symbol_info
            raise Exception(f"Symbol {symbol} not found")
        except Exception as e:
            logger.error(f"Failed to get symbol info: {e}")
            raise
    
    def calculate_quantity(self, symbol: str, side: str, amount: float, price: float) -> Tuple[str, Dict[str, Any]]:
        """Calculate proper quantity based on symbol filters"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            
            # Get LOT_SIZE filter
            lot_size_filter = None
            min_notional_filter = None
            
            for filter_info in symbol_info['filters']:
                if filter_info['filterType'] == 'LOT_SIZE':
                    lot_size_filter = filter_info
                elif filter_info['filterType'] == 'MIN_NOTIONAL':
                    min_notional_filter = filter_info
            
            if not lot_size_filter:
                raise Exception("LOT_SIZE filter not found")
            
            # Calculate quantity
            if side == "BUY":
                quantity = amount / price
            else:  # SELL
                quantity = amount
            
            # Apply step size
            step_size = float(lot_size_filter['stepSize'])
            min_qty = float(lot_size_filter['minQty'])
            max_qty = float(lot_size_filter['maxQty'])
            
            # Round down to step size
            quantity = max(min_qty, quantity - (quantity % step_size))
            
            # Check constraints
            if quantity > max_qty:
                quantity = max_qty
            
            # Check minimum notional
            if min_notional_filter:
                min_notional = float(min_notional_filter['minNotional'])
                if quantity * price < min_notional:
                    quantity = min_notional / price
                    quantity = max(min_qty, quantity - (quantity % step_size))
            
            # Format quantity to appropriate precision
            step_size_str = lot_size_filter['stepSize']
            if '.' in step_size_str:
                precision = len(step_size_str.split('.')[1].rstrip('0'))
            else:
                precision = 0
            
            quantity_str = f"{quantity:.{precision}f}"
            
            return quantity_str, {
                'calculated_quantity': quantity,
                'min_qty': min_qty,
                'max_qty': max_qty,
                'step_size': step_size,
                'precision': precision
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate quantity: {e}")
            raise
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> OrderInfo:
        """Create market order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity
            }
            
            response = self._make_request("POST", "/api/v3/order", params, signed=True)
            
            return OrderInfo(
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
            logger.error(f"Failed to create market order: {e}")
            raise
    
    def create_limit_order(self, symbol: str, side: str, quantity: str, price: str) -> OrderInfo:
        """Create limit order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'LIMIT',
                'timeInForce': 'GTC',
                'quantity': quantity,
                'price': price
            }
            
            response = self._make_request("POST", "/api/v3/order", params, signed=True)
            
            return OrderInfo(
                order_id=response['orderId'],
                client_order_id=response['clientOrderId'],
                symbol=response['symbol'],
                side=response['side'],
                type=response['type'],
                quantity=response['origQty'],
                price=response['price'],
                status=response['status'],
                executed_qty=response['executedQty']
            )
            
        except Exception as e:
            logger.error(f"Failed to create limit order: {e}")
            raise
    
    def create_stop_loss_order(self, symbol: str, side: str, quantity: str, stop_price: str) -> OrderInfo:
        """Create stop loss order"""
        try:
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'STOP_MARKET',
                'quantity': quantity,
                'stopPrice': stop_price
            }
            
            response = self._make_request("POST", "/api/v3/order", params, signed=True)
            
            return OrderInfo(
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
            logger.error(f"Failed to create stop loss order: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """Cancel an order"""
        try:
            params = {
                'symbol': symbol,
                'orderId': order_id
            }
            
            self._make_request("DELETE", "/api/v3/order", params, signed=True)
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status"""
        try:
            params = {
                'symbol': symbol,
                'orderId': order_id
            }
            
            return self._make_request("GET", "/api/v3/order", params, signed=True)
            
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            raise
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """Get kline/candlestick data"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = self._make_request("GET", "/api/v3/klines", params)
            
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
            logger.error(f"Failed to get klines: {e}")
            raise

def validate_binance_credentials(api_key: str, api_secret: str, testnet: bool = True) -> Tuple[bool, str]:
    """Validate Binance API credentials"""
    try:
        client = BinanceIntegration(api_key, api_secret, testnet)
        
        # Test connectivity
        if not client.test_connectivity():
            return False, "Failed to connect to Binance API"
        
        # Test account access
        account_info = client.get_account_info()
        if not account_info:
            return False, "Failed to get account information"
        
        # Check trading permissions
        if not account_info.get('canTrade', False):
            return False, "Account does not have trading permissions"
        
        return True, "Credentials validated successfully"
        
    except Exception as e:
        return False, f"Validation failed: {str(e)}" 
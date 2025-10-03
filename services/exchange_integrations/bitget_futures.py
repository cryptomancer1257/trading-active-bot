"""
Bitget Futures Exchange Integration
"""

import hashlib
import hmac
import time
import base64
import requests
import pandas as pd
import logging
from typing import Dict, Any, List

from .base_futures_exchange import BaseFuturesExchange, FuturesOrderInfo, FuturesPosition

logger = logging.getLogger(__name__)

class BitgetFuturesIntegration(BaseFuturesExchange):
    """Bitget Futures API Integration (V2 API)"""
    
    @property
    def exchange_name(self) -> str:
        return "BITGET"
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str = "", testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.passphrase = passphrase
        
        # Bitget API endpoints
        if testnet:
            self.base_url = "https://api.bitget.com"  # Bitget doesn't have separate testnet URL
        else:
            self.base_url = "https://api.bitget.com"
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Generate Bitget signature"""
        message = timestamp + method.upper() + request_path + body
        mac = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False):
        """Make authenticated request to Bitget API"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        timestamp = str(int(time.time() * 1000))
        
        headers = {
            "Content-Type": "application/json",
            "ACCESS-KEY": self.api_key,
            "ACCESS-TIMESTAMP": timestamp
        }
        
        if self.passphrase:
            headers["ACCESS-PASSPHRASE"] = self.passphrase
        
        body = ""
        if signed:
            if method == "POST":
                import json
                body = json.dumps(params) if params else ""
            
            request_path = endpoint
            if method == "GET" and params:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                request_path = f"{endpoint}?{query_string}"
            
            signature = self._generate_signature(timestamp, method, request_path, body)
            headers["ACCESS-SIGN"] = signature
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != '00000':
                raise Exception(f"Bitget API error: {data.get('msg', 'Unknown error')}")
            
            return data.get('data', {})
            
        except Exception as e:
            logger.error(f"Bitget API request failed: {e}")
            raise
    
    def test_connectivity(self) -> bool:
        """Test Bitget API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/api/v2/public/time", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Bitget connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get Bitget account information"""
        try:
            params = {'productType': 'USDT-FUTURES'}
            result = self._make_request("GET", "/api/v2/mix/account/accounts", params, signed=True)
            
            if result:
                total_balance = float(result.get('crossedAvailable', 0))
                return {
                    'totalWalletBalance': total_balance,
                    'availableBalance': total_balance,
                    'raw_response': result
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get Bitget account info: {e}")
            raise
    
    def get_position_info(self, symbol: str = None) -> List[FuturesPosition]:
        """Get Bitget position information"""
        try:
            params = {'productType': 'USDT-FUTURES'}
            if symbol:
                params['symbol'] = symbol
            
            result = self._make_request("GET", "/api/v2/mix/position/all-positions", params, signed=True)
            
            positions = []
            for pos in result:
                size = float(pos.get('total', 0))
                if size != 0:
                    positions.append(FuturesPosition(
                        symbol=pos['symbol'],
                        side="LONG" if pos['holdSide'] == 'long' else "SHORT",
                        size=str(size),
                        entry_price=pos.get('openPriceAvg', '0'),
                        mark_price=pos.get('markPrice', '0'),
                        pnl=pos.get('unrealizedPL', '0'),
                        percentage=str(float(pos.get('unrealizedPL', 0)) / float(pos.get('margin', 1)) * 100)
                    ))
            
            return positions
        except Exception as e:
            logger.error(f"Failed to get Bitget position info: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        try:
            params = {'symbol': symbol, 'productType': 'USDT-FUTURES'}
            result = self._make_request("GET", "/api/v2/mix/market/ticker", params)
            
            if result:
                return {
                    'symbol': result['symbol'],
                    'price': result['last']
                }
            raise Exception(f"No ticker data for {symbol}")
        except Exception as e:
            logger.error(f"Failed to get ticker: {e}")
            raise
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        try:
            params = {
                'symbol': symbol,
                'productType': 'USDT-FUTURES',
                'marginCoin': 'USDT',
                'leverage': str(leverage)
            }
            self._make_request("POST", "/api/v2/mix/account/set-leverage", params, signed=True)
            logger.info(f"Set leverage {leverage}x for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            return False
    
    def get_symbol_precision(self, symbol: str) -> dict:
        """Get symbol precision"""
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        
        try:
            params = {'productType': 'USDT-FUTURES'}
            result = self._make_request("GET", "/api/v2/mix/market/contracts", params)
            
            for contract in result:
                if contract['symbol'] == symbol:
                    precision_info = {
                        'quantityPrecision': int(contract.get('volumePlace', 3)),
                        'pricePrecision': int(contract.get('pricePlace', 2)),
                        'stepSize': contract.get('sizeMultiplier', '1'),
                        'tickSize': contract.get('priceEndStep', '0.01')
                    }
                    
                    self._symbol_info_cache[symbol] = precision_info
                    return precision_info
            
            return {'quantityPrecision': 3, 'pricePrecision': 2, 'stepSize': '1', 'tickSize': '0.01'}
        except Exception as e:
            logger.error(f"Failed to get symbol precision: {e}")
            return {'quantityPrecision': 3, 'pricePrecision': 2, 'stepSize': '1', 'tickSize': '0.01'}
    
    def round_quantity(self, quantity: float, symbol: str) -> str:
        """Round quantity to proper precision"""
        precision_info = self.get_symbol_precision(symbol)
        decimals = precision_info['quantityPrecision']
        return f"{quantity:.{decimals}f}"
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> FuturesOrderInfo:
        """Create Bitget market order"""
        try:
            params = {
                'symbol': symbol,
                'productType': 'USDT-FUTURES',
                'marginMode': 'crossed',
                'marginCoin': 'USDT',
                'side': 'buy' if side == 'BUY' else 'sell',
                'orderType': 'market',
                'size': quantity
            }
            
            result = self._make_request("POST", "/api/v2/mix/order/place-order", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=result.get('orderId', ''),
                client_order_id=result.get('clientOid', ''),
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity,
                price='0',
                status='PENDING',
                executed_qty='0'
            )
        except Exception as e:
            logger.error(f"Failed to create market order: {e}")
            raise
    
    def create_stop_loss_order(self, symbol: str, side: str, quantity: str, 
                              stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
        """Create stop loss order"""
        try:
            params = {
                'symbol': symbol,
                'productType': 'USDT-FUTURES',
                'marginCoin': 'USDT',
                'planType': 'loss_plan',
                'side': 'buy' if side == 'BUY' else 'sell',
                'triggerPrice': stop_price,
                'size': quantity,
                'reduceOnly': 'YES' if reduce_only else 'NO'
            }
            
            result = self._make_request("POST", "/api/v2/mix/order/place-plan-order", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=result.get('orderId', ''),
                client_order_id=result.get('clientOid', ''),
                symbol=symbol,
                side=side,
                type='STOP_MARKET',
                quantity=quantity,
                price=stop_price,
                status='PENDING',
                executed_qty='0'
            )
        except Exception as e:
            logger.error(f"Failed to create stop loss order: {e}")
            raise
    
    def create_take_profit_order(self, symbol: str, side: str, quantity: str, 
                                stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
        """Create take profit order"""
        try:
            params = {
                'symbol': symbol,
                'productType': 'USDT-FUTURES',
                'marginCoin': 'USDT',
                'planType': 'profit_plan',
                'side': 'buy' if side == 'BUY' else 'sell',
                'triggerPrice': stop_price,
                'size': quantity,
                'reduceOnly': 'YES' if reduce_only else 'NO'
            }
            
            result = self._make_request("POST", "/api/v2/mix/order/place-plan-order", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=result.get('orderId', ''),
                client_order_id=result.get('clientOid', ''),
                symbol=symbol,
                side=side,
                type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                price=stop_price,
                status='PENDING',
                executed_qty='0'
            )
        except Exception as e:
            logger.error(f"Failed to create take profit order: {e}")
            raise
    
    def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """Get all open orders for symbol"""
        try:
            params = {'symbol': symbol, 'productType': 'USDT-FUTURES'}
            result = self._make_request("GET", "/api/v2/mix/order/orders-pending", params, signed=True)
            return result.get('entrustedList', [])
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a specific order"""
        try:
            params = {
                'symbol': symbol,
                'productType': 'USDT-FUTURES',
                'orderId': order_id
            }
            self._make_request("POST", "/api/v2/mix/order/cancel-order", params, signed=True)
            logger.info(f"❌ Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol"""
        try:
            params = {'symbol': symbol, 'productType': 'USDT-FUTURES'}
            self._make_request("POST", "/api/v2/mix/order/cancel-all-orders", params, signed=True)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                   start_time: int = None, end_time: int = None) -> pd.DataFrame:
        """Get Bitget kline data"""
        try:
            # Convert interval format
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1H', '4h': '4H', '12h': '12H', '1d': '1D', '1w': '1W'
            }
            
            bitget_interval = interval_map.get(interval, '1H')
            
            params = {
                'symbol': symbol,
                'productType': 'USDT-FUTURES',
                'granularity': bitget_interval,
                'limit': str(min(limit, 1000))
            }
            
            if start_time:
                params['startTime'] = str(start_time)
            if end_time:
                params['endTime'] = str(end_time)
            
            result = self._make_request("GET", "/api/v2/mix/market/candles", params)
            
            if not result:
                raise Exception("No kline data returned")
            
            # Bitget returns [timestamp, open, high, low, close, volume, ...]
            data = []
            for item in result:
                data.append({
                    'timestamp': int(item[0]),
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5])
                })
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to get klines: {e}")
            raise
    
    def _sync_server_time(self):
        """Sync with Bitget server time"""
        try:
            response = requests.get(f"{self.base_url}/api/v2/public/time", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '00000':
                    server_time = int(data['data'])
                    local_time = int(time.time() * 1000)
                    self._time_offset = server_time - local_time
                    logger.info(f"⏱️ Bitget server time synced, offset={self._time_offset} ms")
        except Exception as e:
            logger.warning(f"⚠️ Failed to sync Bitget server time: {e}")
            self._time_offset = 0
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for Bitget (BTCUSDT -> BTCUSDT)"""
        return symbol.replace('/', '').upper()


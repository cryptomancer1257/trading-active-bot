"""
OKX Futures Exchange Integration
"""

import hashlib
import hmac
import time
import base64
import requests
import pandas as pd
import logging
from typing import Dict, Any, List
from datetime import datetime

from .base_futures_exchange import BaseFuturesExchange, FuturesOrderInfo, FuturesPosition

logger = logging.getLogger(__name__)

class OKXFuturesIntegration(BaseFuturesExchange):
    """OKX Futures API Integration (V5 API)"""
    
    @property
    def exchange_name(self) -> str:
        return "OKX"
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str = "", testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.passphrase = passphrase  # OKX requires passphrase
        
        # OKX API endpoints
        if testnet:
            self.base_url = "https://www.okx.com"  # OKX uses same URL with demo trading flag
        else:
            self.base_url = "https://www.okx.com"
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Generate OKX signature"""
        message = timestamp + method + request_path + body
        mac = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False):
        """Make authenticated request to OKX API"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        
        headers = {
            "Content-Type": "application/json",
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-TIMESTAMP": timestamp
        }
        
        if self.passphrase:
            headers["OK-ACCESS-PASSPHRASE"] = self.passphrase
        
        body = ""
        if signed:
            if method == "POST":
                import json
                body = json.dumps(params) if params else ""
            else:
                body = ""
            
            request_path = endpoint
            if method == "GET" and params:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                request_path = f"{endpoint}?{query_string}"
            
            signature = self._generate_signature(timestamp, method, request_path, body)
            headers["OK-ACCESS-SIGN"] = signature
        
        # Demo trading flag for testnet
        if self.testnet:
            headers["x-simulated-trading"] = "1"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != '0':
                raise Exception(f"OKX API error: {data.get('msg', 'Unknown error')}")
            
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"OKX API request failed: {e}")
            raise
    
    def test_connectivity(self) -> bool:
        """Test OKX API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/api/v5/public/time", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OKX connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get OKX account information"""
        try:
            result = self._make_request("GET", "/api/v5/account/balance", signed=True)
            
            if result and len(result) > 0:
                account = result[0]
                total_equity = float(account.get('totalEq', 0))
                
                return {
                    'totalWalletBalance': total_equity,
                    'availableBalance': total_equity,
                    'raw_response': result
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get OKX account info: {e}")
            raise
    
    def get_position_info(self, symbol: str = None) -> List[FuturesPosition]:
        """Get OKX position information"""
        try:
            params = {'instType': 'SWAP'}
            if symbol:
                params['instId'] = self._to_okx_symbol(symbol)
            
            result = self._make_request("GET", "/api/v5/account/positions", params, signed=True)
            
            positions = []
            for pos in result:
                size = float(pos.get('pos', 0))
                if size != 0:
                    positions.append(FuturesPosition(
                        symbol=self._from_okx_symbol(pos['instId']),
                        side="LONG" if pos['posSide'] == 'long' else "SHORT",
                        size=str(abs(size)),
                        entry_price=pos.get('avgPx', '0'),
                        mark_price=pos.get('markPx', '0'),
                        pnl=pos.get('upl', '0'),
                        percentage=str(float(pos.get('uplRatio', 0)) * 100)
                    ))
            
            return positions
        except Exception as e:
            logger.error(f"Failed to get OKX position info: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        try:
            params = {'instId': self._to_okx_symbol(symbol)}
            result = self._make_request("GET", "/api/v5/market/ticker", params)
            
            if result and len(result) > 0:
                return {
                    'symbol': symbol,
                    'price': result[0]['last']
                }
            raise Exception(f"No ticker data for {symbol}")
        except Exception as e:
            logger.error(f"Failed to get ticker: {e}")
            raise
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        try:
            params = {
                'instId': self._to_okx_symbol(symbol),
                'lever': str(leverage),
                'mgnMode': 'cross'
            }
            self._make_request("POST", "/api/v5/account/set-leverage", params, signed=True)
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
            params = {'instType': 'SWAP', 'instId': self._to_okx_symbol(symbol)}
            result = self._make_request("GET", "/api/v5/public/instruments", params)
            
            if result and len(result) > 0:
                info = result[0]
                precision_info = {
                    'quantityPrecision': int(info.get('lotSz', '1')),
                    'pricePrecision': int(info.get('tickSz', '0.01')),
                    'stepSize': info.get('lotSz', '1'),
                    'tickSize': info.get('tickSz', '0.01')
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
        step_size = float(precision_info['stepSize'])
        rounded_qty = round(quantity / step_size) * step_size
        return str(int(rounded_qty)) if rounded_qty.is_integer() else str(rounded_qty)
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> FuturesOrderInfo:
        """Create OKX market order"""
        try:
            params = {
                'instId': self._to_okx_symbol(symbol),
                'tdMode': 'cross',
                'side': 'buy' if side == 'BUY' else 'sell',
                'ordType': 'market',
                'sz': quantity
            }
            
            result = self._make_request("POST", "/api/v5/trade/order", params, signed=True)
            
            if result and len(result) > 0:
                order = result[0]
                return FuturesOrderInfo(
                    order_id=order.get('ordId', ''),
                    client_order_id=order.get('clOrdId', ''),
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=quantity,
                    price='0',
                    status=order.get('sCode', 'PENDING'),
                    executed_qty='0'
                )
            raise Exception("Failed to create order")
        except Exception as e:
            logger.error(f"Failed to create market order: {e}")
            raise
    
    def create_stop_loss_order(self, symbol: str, side: str, quantity: str, 
                              stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
        """Create stop loss order"""
        try:
            params = {
                'instId': self._to_okx_symbol(symbol),
                'tdMode': 'cross',
                'side': 'buy' if side == 'BUY' else 'sell',
                'ordType': 'conditional',
                'sz': quantity,
                'slTriggerPx': stop_price,
                'slOrdPx': '-1',  # Market price
                'reduceOnly': reduce_only
            }
            
            result = self._make_request("POST", "/api/v5/trade/order-algo", params, signed=True)
            
            if result and len(result) > 0:
                order = result[0]
                return FuturesOrderInfo(
                    order_id=order.get('algoId', ''),
                    client_order_id=order.get('clOrdId', ''),
                    symbol=symbol,
                    side=side,
                    type='STOP_MARKET',
                    quantity=quantity,
                    price=stop_price,
                    status='PENDING',
                    executed_qty='0'
                )
            raise Exception("Failed to create stop loss order")
        except Exception as e:
            logger.error(f"Failed to create stop loss order: {e}")
            raise
    
    def create_take_profit_order(self, symbol: str, side: str, quantity: str, 
                                stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
        """Create take profit order"""
        try:
            params = {
                'instId': self._to_okx_symbol(symbol),
                'tdMode': 'cross',
                'side': 'buy' if side == 'BUY' else 'sell',
                'ordType': 'conditional',
                'sz': quantity,
                'tpTriggerPx': stop_price,
                'tpOrdPx': '-1',
                'reduceOnly': reduce_only
            }
            
            result = self._make_request("POST", "/api/v5/trade/order-algo", params, signed=True)
            
            if result and len(result) > 0:
                order = result[0]
                return FuturesOrderInfo(
                    order_id=order.get('algoId', ''),
                    client_order_id=order.get('clOrdId', ''),
                    symbol=symbol,
                    side=side,
                    type='TAKE_PROFIT_MARKET',
                    quantity=quantity,
                    price=stop_price,
                    status='PENDING',
                    executed_qty='0'
                )
            raise Exception("Failed to create take profit order")
        except Exception as e:
            logger.error(f"Failed to create take profit order: {e}")
            raise
    
    def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """Get all open orders for symbol"""
        try:
            params = {'instType': 'SWAP', 'instId': self._to_okx_symbol(symbol)}
            result = self._make_request("GET", "/api/v5/trade/orders-pending", params, signed=True)
            return result
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a specific order"""
        try:
            params = {
                'instId': self._to_okx_symbol(symbol),
                'ordId': order_id
            }
            self._make_request("POST", "/api/v5/trade/cancel-order", params, signed=True)
            logger.info(f"❌ Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol"""
        try:
            orders = self.get_open_orders(symbol)
            for order in orders:
                self.cancel_order(symbol, order.get('ordId', ''))
            return True
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                   start_time: int = None, end_time: int = None) -> pd.DataFrame:
        """Get OKX kline data"""
        try:
            # Convert interval format
            interval_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1H', '2h': '2H', '4h': '4H', '6h': '6H', '12h': '12H',
                '1d': '1D', '1w': '1W', '1M': '1M'
            }
            
            okx_interval = interval_map.get(interval, '1H')
            
            params = {
                'instId': self._to_okx_symbol(symbol),
                'bar': okx_interval,
                'limit': str(min(limit, 300))
            }
            
            if start_time:
                params['after'] = str(start_time)
            if end_time:
                params['before'] = str(end_time)
            
            result = self._make_request("GET", "/api/v5/market/candles", params)
            
            if not result:
                raise Exception("No kline data returned")
            
            # OKX returns [timestamp, open, high, low, close, volume, volCcy, volCcyQuote, confirm]
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
        """Sync with OKX server time"""
        try:
            response = requests.get(f"{self.base_url}/api/v5/public/time", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '0' and data.get('data'):
                    server_time = int(data['data'][0]['ts'])
                    local_time = int(time.time() * 1000)
                    self._time_offset = server_time - local_time
                    logger.info(f"⏱️ OKX server time synced, offset={self._time_offset} ms")
        except Exception as e:
            logger.warning(f"⚠️ Failed to sync OKX server time: {e}")
            self._time_offset = 0
    
    def _to_okx_symbol(self, symbol: str) -> str:
        """Convert symbol to OKX format (BTCUSDT -> BTC-USDT-SWAP)"""
        base_symbol = symbol.replace('/', '').replace('USDT', '-USDT')
        return f"{base_symbol}-SWAP"
    
    def _from_okx_symbol(self, okx_symbol: str) -> str:
        """Convert OKX symbol back to standard format"""
        return okx_symbol.replace('-SWAP', '').replace('-', '')
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for OKX"""
        return symbol.replace('/', '').upper()


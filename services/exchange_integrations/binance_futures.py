"""
Binance Futures Exchange Integration
"""

import hashlib
import hmac
import time
import requests
import pandas as pd
import logging
from typing import Dict, Any, List, Optional

from .base_futures_exchange import BaseFuturesExchange, FuturesOrderInfo, FuturesPosition

logger = logging.getLogger(__name__)

class BinanceFuturesIntegration(BaseFuturesExchange):
    """Binance Futures API Integration"""
    
    @property
    def exchange_name(self) -> str:
        return "BINANCE"
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        
        # Binance Futures endpoints
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
    
    def _generate_signature(self, params: dict) -> str:
        """Generate HMAC SHA256 signature"""
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, 
                     signed: bool = False, recv_window: int = 50000):
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
            if hasattr(e, "response") and e.response is not None:
                try:
                    data = e.response.json()
                    if data.get("code") == -1021:
                        logger.warning("⏱️ Timestamp error (-1021), resyncing...")
                        self._sync_server_time()
                        return self._make_request(method, endpoint, params, signed, recv_window)
                except Exception:
                    pass
            logger.error(f"Binance API request failed: {e}")
            raise Exception(f"Binance API request failed: {e}")
    
    def test_connectivity(self) -> bool:
        """Test Binance Futures API connectivity"""
        try:
            response = self._make_request("GET", "/fapi/v1/ping")
            return response == {}
        except Exception as e:
            logger.error(f"Binance connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get Binance futures account information"""
        try:
            return self._make_request("GET", "/fapi/v2/account", signed=True)
        except Exception as e:
            logger.error(f"Failed to get Binance account info: {e}")
            raise
    
    def get_position_info(self, symbol: str = None) -> List[FuturesPosition]:
        """Get Binance position information"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            
            positions = self._make_request("GET", "/fapi/v2/positionRisk", params, signed=True)
            
            result = []
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    result.append(FuturesPosition(
                        symbol=pos['symbol'],
                        side="LONG" if float(pos['positionAmt']) > 0 else "SHORT",
                        size=pos['positionAmt'],
                        entry_price=pos['entryPrice'],
                        mark_price=pos['markPrice'],
                        pnl=pos['unRealizedProfit'],
                        percentage=pos.get('percentage', '0')
                    ))
            
            return result
        except Exception as e:
            logger.error(f"Failed to get Binance position info: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        try:
            params = {'symbol': symbol}
            response = self._make_request("GET", "/fapi/v1/ticker/price", params)
            return response
        except Exception as e:
            logger.error(f"Failed to get ticker price: {e}")
            raise
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        try:
            params = {'symbol': symbol, 'leverage': leverage}
            response = self._make_request("POST", "/fapi/v1/leverage", params, signed=True)
            logger.info(f"Set leverage {leverage}x for {symbol}: {response}")
            return True
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            return False
    
    def get_symbol_precision(self, symbol: str) -> dict:
        """Get quantity and price precision for a symbol"""
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        
        try:
            response = self._make_request("GET", "/fapi/v1/exchangeInfo", signed=False)
            
            for sym_info in response.get('symbols', []):
                if sym_info['symbol'] == symbol:
                    precision_info = {
                        'quantityPrecision': sym_info['quantityPrecision'],
                        'pricePrecision': sym_info['pricePrecision'],
                        'stepSize': '0.01',
                        'tickSize': '0.01'
                    }
                    
                    for filter_item in sym_info.get('filters', []):
                        if filter_item['filterType'] == 'LOT_SIZE':
                            precision_info['stepSize'] = filter_item['stepSize']
                        elif filter_item['filterType'] == 'PRICE_FILTER':
                            precision_info['tickSize'] = filter_item['tickSize']
                    
                    self._symbol_info_cache[symbol] = precision_info
                    return precision_info
            
            logger.warning(f"Symbol {symbol} not found, using defaults")
            return {'quantityPrecision': 3, 'pricePrecision': 2, 'stepSize': '0.001', 'tickSize': '0.01'}
            
        except Exception as e:
            logger.error(f"Failed to get symbol precision: {e}")
            return {'quantityPrecision': 3, 'pricePrecision': 2, 'stepSize': '0.001', 'tickSize': '0.01'}
    
    def round_quantity(self, quantity: float, symbol: str) -> str:
        """Round quantity to proper precision"""
        precision_info = self.get_symbol_precision(symbol)
        decimals = precision_info['quantityPrecision']
        step_size = float(precision_info['stepSize'])
        
        rounded_qty = round(quantity / step_size) * step_size
        qty_str = f"{rounded_qty:.{decimals}f}"
        
        return qty_str
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> FuturesOrderInfo:
        """Create Binance futures market order"""
        try:
            quantity_float = float(quantity)
            rounded_quantity = self.round_quantity(quantity_float, symbol)
            
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': rounded_quantity
            }
            
            response = self._make_request("POST", "/fapi/v1/order", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=str(response['orderId']),
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
    
    def create_stop_loss_order(self, symbol: str, side: str, quantity: str, 
                              stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
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
                order_id=str(response['orderId']),
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
    
    def create_take_profit_order(self, symbol: str, side: str, quantity: str, 
                                stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
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
                order_id=str(response['orderId']),
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
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a specific order"""
        try:
            params = {'symbol': symbol, 'orderId': int(order_id)}
            self._make_request("DELETE", "/fapi/v1/order", params, signed=True)
            logger.info(f"❌ Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol"""
        try:
            params = {'symbol': symbol}
            response = self._make_request("DELETE", "/fapi/v1/allOpenOrders", params, signed=True)
            logger.info(f"Cancelled all orders for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                   start_time: int = None, end_time: int = None) -> pd.DataFrame:
        """Get Binance futures kline data"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit,
                'startTime': start_time,
                'endTime': end_time
            }
            
            response = self._make_request("GET", "/fapi/v1/klines", params)
            
            df = pd.DataFrame(response, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to get klines: {e}")
            raise
    
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


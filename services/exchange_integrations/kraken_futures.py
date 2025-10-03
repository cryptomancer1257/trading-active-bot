"""
Kraken Futures Exchange Integration
"""

import hashlib
import hmac
import base64
import time
import requests
import pandas as pd
import logging
from typing import Dict, Any, List
from urllib.parse import urlencode

from .base_futures_exchange import BaseFuturesExchange, FuturesOrderInfo, FuturesPosition

logger = logging.getLogger(__name__)

class KrakenFuturesIntegration(BaseFuturesExchange):
    """Kraken Futures API Integration"""
    
    @property
    def exchange_name(self) -> str:
        return "KRAKEN"
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        
        # Kraken Futures endpoints
        if testnet:
            self.base_url = "https://demo-futures.kraken.com"
        else:
            self.base_url = "https://futures.kraken.com"
    
    def _generate_signature(self, endpoint: str, nonce: str, data: str = "") -> str:
        """Generate Kraken Futures signature"""
        message = data + nonce + endpoint
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            message.encode('utf-8'),
            hashlib.sha512
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False):
        """Make authenticated request to Kraken Futures API"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        if signed:
            nonce = str(int(time.time() * 1000))
            data = urlencode(params) if params else ""
            
            signature = self._generate_signature(endpoint, nonce, data)
            
            headers["APIKey"] = self.api_key
            headers["Nonce"] = nonce
            headers["Authent"] = signature
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('result') != 'success' and 'error' in data:
                raise Exception(f"Kraken API error: {data.get('error', 'Unknown error')}")
            
            return data
            
        except Exception as e:
            logger.error(f"Kraken API request failed: {e}")
            raise
    
    def test_connectivity(self) -> bool:
        """Test Kraken API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/derivatives/api/v3/instruments", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Kraken connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get Kraken account information"""
        try:
            result = self._make_request("GET", "/derivatives/api/v3/accounts", signed=True)
            
            if result and 'accounts' in result:
                account = result['accounts'][0] if result['accounts'] else {}
                balance = float(account.get('balanceValue', 0))
                
                return {
                    'totalWalletBalance': balance,
                    'availableBalance': balance,
                    'raw_response': result
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get Kraken account info: {e}")
            raise
    
    def get_position_info(self, symbol: str = None) -> List[FuturesPosition]:
        """Get Kraken position information"""
        try:
            result = self._make_request("GET", "/derivatives/api/v3/openpositions", signed=True)
            
            positions = []
            for pos in result.get('openPositions', []):
                if symbol and pos['symbol'] != symbol:
                    continue
                
                size = float(pos.get('size', 0))
                if size != 0:
                    positions.append(FuturesPosition(
                        symbol=pos['symbol'],
                        side="LONG" if size > 0 else "SHORT",
                        size=str(abs(size)),
                        entry_price=pos.get('price', '0'),
                        mark_price='0',
                        pnl=pos.get('unrealizedFunding', '0'),
                        percentage='0'
                    ))
            
            return positions
        except Exception as e:
            logger.error(f"Failed to get Kraken position info: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        try:
            result = self._make_request("GET", "/derivatives/api/v3/tickers")
            
            for ticker in result.get('tickers', []):
                if ticker['symbol'] == symbol:
                    return {
                        'symbol': symbol,
                        'price': str(ticker['last'])
                    }
            raise Exception(f"No ticker data for {symbol}")
        except Exception as e:
            logger.error(f"Failed to get ticker: {e}")
            raise
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage - Kraken uses fixed leverage per symbol"""
        logger.warning("Kraken Futures has fixed leverage per contract, cannot be changed via API")
        return True
    
    def get_symbol_precision(self, symbol: str) -> dict:
        """Get symbol precision"""
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        
        try:
            result = self._make_request("GET", "/derivatives/api/v3/instruments")
            
            for instrument in result.get('instruments', []):
                if instrument['symbol'] == symbol:
                    precision_info = {
                        'quantityPrecision': 0,
                        'pricePrecision': 1,
                        'stepSize': '1',
                        'tickSize': str(instrument.get('tickSize', 0.5))
                    }
                    
                    self._symbol_info_cache[symbol] = precision_info
                    return precision_info
            
            return {'quantityPrecision': 0, 'pricePrecision': 1, 'stepSize': '1', 'tickSize': '0.5'}
        except Exception as e:
            logger.error(f"Failed to get symbol precision: {e}")
            return {'quantityPrecision': 0, 'pricePrecision': 1, 'stepSize': '1', 'tickSize': '0.5'}
    
    def round_quantity(self, quantity: float, symbol: str) -> str:
        """Round quantity - Kraken uses integer contracts"""
        return str(int(quantity))
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> FuturesOrderInfo:
        """Create Kraken market order"""
        try:
            params = {
                'orderType': 'mkt',
                'symbol': symbol,
                'side': 'buy' if side == 'BUY' else 'sell',
                'size': int(float(quantity))
            }
            
            result = self._make_request("POST", "/derivatives/api/v3/sendorder", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=result.get('sendStatus', {}).get('order_id', ''),
                client_order_id='',
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity,
                price='0',
                status=result.get('sendStatus', {}).get('status', 'PENDING'),
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
                'orderType': 'stp',
                'symbol': symbol,
                'side': 'buy' if side == 'BUY' else 'sell',
                'size': int(float(quantity)),
                'stopPrice': stop_price,
                'reduceOnly': reduce_only
            }
            
            result = self._make_request("POST", "/derivatives/api/v3/sendorder", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=result.get('sendStatus', {}).get('order_id', ''),
                client_order_id='',
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
                'orderType': 'take_profit',
                'symbol': symbol,
                'side': 'buy' if side == 'BUY' else 'sell',
                'size': int(float(quantity)),
                'stopPrice': stop_price,
                'reduceOnly': reduce_only
            }
            
            result = self._make_request("POST", "/derivatives/api/v3/sendorder", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=result.get('sendStatus', {}).get('order_id', ''),
                client_order_id='',
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
            result = self._make_request("GET", "/derivatives/api/v3/openorders", signed=True)
            orders = result.get('openOrders', [])
            
            if symbol:
                orders = [o for o in orders if o.get('symbol') == symbol]
            
            return orders
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a specific order"""
        try:
            params = {'order_id': order_id}
            self._make_request("POST", "/derivatives/api/v3/cancelorder", params, signed=True)
            logger.info(f"❌ Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol"""
        try:
            params = {'symbol': symbol}
            self._make_request("POST", "/derivatives/api/v3/cancelallorders", params, signed=True)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                   start_time: int = None, end_time: int = None) -> pd.DataFrame:
        """Get Kraken kline data"""
        try:
            # Kraken uses resolution in minutes
            interval_map = {
                '1m': '1', '5m': '5', '15m': '15', '30m': '30',
                '1h': '60', '4h': '240', '1d': '1440'
            }
            
            resolution = interval_map.get(interval, '60')
            
            params = {
                'symbol': symbol,
                'resolution': resolution
            }
            
            if limit:
                params['limit'] = str(min(limit, 1000))
            
            result = self._make_request("GET", "/api/charts/v1/trade", params)
            
            if not result or 'candles' not in result:
                raise Exception("No kline data returned")
            
            # Kraken returns {time, open, high, low, close, volume}
            data = []
            for candle in result['candles']:
                data.append({
                    'timestamp': int(candle['time']),
                    'open': float(candle['open']),
                    'high': float(candle['high']),
                    'low': float(candle['low']),
                    'close': float(candle['close']),
                    'volume': float(candle.get('volume', 0))
                })
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to get klines: {e}")
            raise
    
    def _sync_server_time(self):
        """Kraken Futures doesn't require time sync"""
        self._time_offset = 0
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for Kraken (BTCUSDT -> PF_XBTUSD)"""
        # Kraken uses specific notation like PF_XBTUSD for BTC perpetual
        symbol_map = {
            'BTCUSDT': 'PF_XBTUSD',
            'ETHUSDT': 'PF_ETHUSD',
            'BTCUSD': 'PF_XBTUSD',
            'ETHUSD': 'PF_ETHUSD'
        }
        
        normalized = symbol.replace('/', '').upper()
        return symbol_map.get(normalized, f"PF_{normalized}")


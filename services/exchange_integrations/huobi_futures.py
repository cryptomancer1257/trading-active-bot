"""
Huobi (HTX) Futures Exchange Integration
Note: Huobi rebranded to HTX but API remains similar
"""

import hashlib
import hmac
import base64
import time
import requests
import pandas as pd
import logging
from typing import Dict, Any, List
from datetime import datetime
from urllib.parse import urlencode

from .base_futures_exchange import BaseFuturesExchange, FuturesOrderInfo, FuturesPosition

logger = logging.getLogger(__name__)

class HuobiFuturesIntegration(BaseFuturesExchange):
    """Huobi/HTX Futures API Integration"""
    
    @property
    def exchange_name(self) -> str:
        return "HUOBI"
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        
        # Huobi Futures endpoints
        if testnet:
            self.base_url = "https://api.hbdm.vn"  # Demo trading
        else:
            self.base_url = "https://api.hbdm.com"
    
    def _generate_signature(self, method: str, host: str, path: str, params: dict) -> str:
        """Generate Huobi signature"""
        sorted_params = sorted(params.items())
        encode_params = urlencode(sorted_params)
        
        payload = f"{method}\n{host}\n{path}\n{encode_params}"
        
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False):
        """Make authenticated request to Huobi API"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        host = "api.hbdm.com"
        
        if signed:
            timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            auth_params = {
                'AccessKeyId': self.api_key,
                'SignatureMethod': 'HmacSHA256',
                'SignatureVersion': '2',
                'Timestamp': timestamp
            }
            
            params.update(auth_params)
            signature = self._generate_signature(method, host, endpoint, params)
            params['Signature'] = signature
        
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                raise Exception(f"Huobi API error: {data.get('err_msg', 'Unknown error')}")
            
            return data.get('data', {})
            
        except Exception as e:
            logger.error(f"Huobi API request failed: {e}")
            raise
    
    def test_connectivity(self) -> bool:
        """Test Huobi API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/timestamp", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Huobi connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get Huobi account information"""
        try:
            result = self._make_request("POST", "/linear-swap-api/v1/swap_account_info", signed=True)
            
            if result:
                total_balance = sum(float(item.get('margin_balance', 0)) for item in result)
                return {
                    'totalWalletBalance': total_balance,
                    'availableBalance': total_balance,
                    'raw_response': result
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get Huobi account info: {e}")
            raise
    
    def get_position_info(self, symbol: str = None) -> List[FuturesPosition]:
        """Get Huobi position information"""
        try:
            params = {}
            if symbol:
                params['contract_code'] = symbol
            
            result = self._make_request("POST", "/linear-swap-api/v1/swap_position_info", params, signed=True)
            
            positions = []
            for pos in result:
                size = float(pos.get('volume', 0))
                if size != 0:
                    positions.append(FuturesPosition(
                        symbol=pos['contract_code'],
                        side="LONG" if pos['direction'] == 'buy' else "SHORT",
                        size=str(size),
                        entry_price=pos.get('cost_open', '0'),
                        mark_price='0',  # Huobi doesn't provide mark price directly
                        pnl=pos.get('profit_unreal', '0'),
                        percentage=str(float(pos.get('profit_rate', 0)) * 100)
                    ))
            
            return positions
        except Exception as e:
            logger.error(f"Failed to get Huobi position info: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        try:
            params = {'contract_code': symbol}
            result = self._make_request("GET", "/linear-swap-ex/market/detail/merged", params)
            
            if result:
                return {
                    'symbol': symbol,
                    'price': str(result['close'])
                }
            raise Exception(f"No ticker data for {symbol}")
        except Exception as e:
            logger.error(f"Failed to get ticker: {e}")
            raise
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        try:
            params = {
                'contract_code': symbol,
                'lever_rate': leverage
            }
            self._make_request("POST", "/linear-swap-api/v1/swap_switch_lever_rate", params, signed=True)
            logger.info(f"Set leverage {leverage}x for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            return False
    
    def get_symbol_precision(self, symbol: str) -> dict:
        """Get symbol precision"""
        # Huobi uses standard precision, simplified for now
        return {'quantityPrecision': 0, 'pricePrecision': 2, 'stepSize': '1', 'tickSize': '0.01'}
    
    def round_quantity(self, quantity: float, symbol: str) -> str:
        """Round quantity - Huobi uses contracts (integers)"""
        return str(int(quantity))
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> FuturesOrderInfo:
        """Create Huobi market order"""
        try:
            params = {
                'contract_code': symbol,
                'direction': 'buy' if side == 'BUY' else 'sell',
                'offset': 'open',
                'lever_rate': 10,
                'order_price_type': 'optimal_5',
                'volume': int(float(quantity))
            }
            
            result = self._make_request("POST", "/linear-swap-api/v1/swap_order", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=str(result.get('order_id', '')),
                client_order_id=str(result.get('client_order_id', '')),
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
        raise NotImplementedError("Huobi stop loss orders require different implementation")
    
    def create_take_profit_order(self, symbol: str, side: str, quantity: str, 
                                stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
        """Create take profit order"""
        raise NotImplementedError("Huobi take profit orders require different implementation")
    
    def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """Get all open orders for symbol"""
        try:
            params = {'contract_code': symbol}
            result = self._make_request("POST", "/linear-swap-api/v1/swap_openorders", params, signed=True)
            return result.get('orders', [])
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a specific order"""
        try:
            params = {
                'contract_code': symbol,
                'order_id': order_id
            }
            self._make_request("POST", "/linear-swap-api/v1/swap_cancel", params, signed=True)
            logger.info(f"❌ Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol"""
        try:
            params = {'contract_code': symbol}
            self._make_request("POST", "/linear-swap-api/v1/swap_cancelall", params, signed=True)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                   start_time: int = None, end_time: int = None) -> pd.DataFrame:
        """Get Huobi kline data"""
        try:
            # Convert interval format
            interval_map = {
                '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
                '1h': '60min', '4h': '4hour', '1d': '1day', '1w': '1week'
            }
            
            huobi_interval = interval_map.get(interval, '60min')
            
            params = {
                'contract_code': symbol,
                'period': huobi_interval,
                'size': min(limit, 2000)
            }
            
            result = self._make_request("GET", "/linear-swap-ex/market/history/kline", params)
            
            if not result:
                raise Exception("No kline data returned")
            
            # Huobi returns {id, open, close, high, low, amount, vol, count}
            data = []
            for item in result:
                data.append({
                    'timestamp': item['id'] * 1000,  # Convert to ms
                    'open': float(item['open']),
                    'high': float(item['high']),
                    'low': float(item['low']),
                    'close': float(item['close']),
                    'volume': float(item['amount'])
                })
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to get klines: {e}")
            raise
    
    def _sync_server_time(self):
        """Sync with Huobi server time"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/timestamp", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    server_time = data['data']
                    local_time = int(time.time() * 1000)
                    self._time_offset = server_time - local_time
                    logger.info(f"⏱️ Huobi server time synced, offset={self._time_offset} ms")
        except Exception as e:
            logger.warning(f"⚠️ Failed to sync Huobi server time: {e}")
            self._time_offset = 0
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for Huobi (BTCUSDT -> BTC-USDT)"""
        base = symbol.replace('/', '').replace('USDT', '')
        return f"{base}-USDT"


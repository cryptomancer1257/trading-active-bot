"""
Bybit Futures Exchange Integration
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

class BybitFuturesIntegration(BaseFuturesExchange):
    """Bybit Futures API Integration (V5 API)"""
    
    @property
    def exchange_name(self) -> str:
        return "BYBIT"
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        
        # Bybit V5 API endpoints
        if testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
    
    def _generate_signature(self, params: str, timestamp: str) -> str:
        """Generate HMAC SHA256 signature for Bybit V5"""
        param_str = str(timestamp) + self.api_key + "5000" + params
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False):
        """Make authenticated request to Bybit V5 API"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        timestamp = str(int(time.time() * 1000))
        
        headers = {
            "Content-Type": "application/json",
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": "5000"
        }
        
        if signed:
            if method == "POST":
                import json
                param_str = json.dumps(params)
            else:
                param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            
            signature = self._generate_signature(param_str, timestamp)
            headers["X-BAPI-SIGN"] = signature
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                import json
                response = requests.post(url, headers=headers, json=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('retCode') != 0:
                raise Exception(f"Bybit API error: {data.get('retMsg', 'Unknown error')}")
            
            return data.get('result', {})
            
        except Exception as e:
            logger.error(f"Bybit API request failed: {e}")
            raise Exception(f"Bybit API request failed: {e}")
    
    def test_connectivity(self) -> bool:
        """Test Bybit API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/v5/market/time", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Bybit connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get Bybit futures account information"""
        try:
            params = {'accountType': 'UNIFIED'}  # or 'CONTRACT' for futures-only
            result = self._make_request("GET", "/v5/account/wallet-balance", params, signed=True)
            
            # Normalize to common format
            if result and 'list' in result and len(result['list']) > 0:
                account = result['list'][0]
                total_balance = float(account.get('totalWalletBalance', 0))
                available_balance = float(account.get('totalAvailableBalance', 0))
                
                return {
                    'totalWalletBalance': total_balance,
                    'availableBalance': available_balance,
                    'totalMarginBalance': total_balance,
                    'raw_response': result
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get Bybit account info: {e}")
            raise
    
    def get_position_info(self, symbol: str = None) -> List[FuturesPosition]:
        """Get Bybit position information"""
        try:
            params = {
                'category': 'linear',  # Linear futures
                'settleCoin': 'USDT'
            }
            if symbol:
                params['symbol'] = symbol
            
            result = self._make_request("GET", "/v5/position/list", params, signed=True)
            
            positions = []
            for pos in result.get('list', []):
                size = float(pos.get('size', 0))
                if size != 0:
                    positions.append(FuturesPosition(
                        symbol=pos['symbol'],
                        side="LONG" if pos['side'] == 'Buy' else "SHORT",
                        size=str(size),
                        entry_price=pos.get('avgPrice', '0'),
                        mark_price=pos.get('markPrice', '0'),
                        pnl=pos.get('unrealisedPnl', '0'),
                        percentage=str(float(pos.get('unrealisedPnl', 0)) / float(pos.get('positionValue', 1)) * 100)
                    ))
            
            return positions
        except Exception as e:
            logger.error(f"Failed to get Bybit position info: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        try:
            params = {'category': 'linear', 'symbol': symbol}
            result = self._make_request("GET", "/v5/market/tickers", params)
            
            if result and 'list' in result and len(result['list']) > 0:
                ticker = result['list'][0]
                return {
                    'symbol': ticker['symbol'],
                    'price': ticker['lastPrice']
                }
            raise Exception(f"No ticker data for {symbol}")
        except Exception as e:
            logger.error(f"Failed to get ticker: {e}")
            raise
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'buyLeverage': str(leverage),
                'sellLeverage': str(leverage)
            }
            self._make_request("POST", "/v5/position/set-leverage", params, signed=True)
            logger.info(f"✅ Set leverage {leverage}x for {symbol}")
            return True
        except Exception as e:
            error_msg = str(e).lower()
            # "leverage not modified" means leverage is already at desired level - this is OK
            if 'leverage not modified' in error_msg:
                logger.info(f"✅ Leverage already at {leverage}x for {symbol}")
                return True
            # Other errors
            logger.error(f"❌ Failed to set leverage: {e}")
            return False
    
    def get_symbol_precision(self, symbol: str) -> dict:
        """Get quantity and price precision for symbol including minimum quantities"""
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        
        try:
            params = {'category': 'linear', 'symbol': symbol}
            result = self._make_request("GET", "/v5/market/instruments-info", params)
            
            if result and 'list' in result and len(result['list']) > 0:
                info = result['list'][0]
                lot_filter = info.get('lotSizeFilter', {})
                price_filter = info.get('priceFilter', {})
                
                # Extract minimum and maximum quantities
                min_order_qty = float(lot_filter.get('minOrderQty', '0.001'))
                max_order_qty = float(lot_filter.get('maxOrderQty', '1000'))
                qty_step = float(lot_filter.get('qtyStep', '0.001'))
                
                precision_info = {
                    'quantityPrecision': len(str(qty_step).split('.')[-1]),
                    'pricePrecision': len(str(float(price_filter.get('tickSize', '0.01'))).split('.')[-1]),
                    'stepSize': str(qty_step),
                    'tickSize': price_filter.get('tickSize', '0.01'),
                    'minQty': min_order_qty,
                    'maxQty': max_order_qty,
                    'minNotional': float(lot_filter.get('minNotionalValue', '5'))  # Minimum order value in USDT
                }
                
                logger.info(f"📐 {symbol} Bybit precision: minQty={min_order_qty}, step={qty_step}, minNotional=${precision_info['minNotional']}")
                
                self._symbol_info_cache[symbol] = precision_info
                return precision_info
            
            return {
                'quantityPrecision': 3, 
                'pricePrecision': 2, 
                'stepSize': '0.001', 
                'tickSize': '0.01',
                'minQty': 0.001,
                'maxQty': 1000,
                'minNotional': 5
            }
        except Exception as e:
            logger.error(f"Failed to get symbol precision: {e}")
            return {
                'quantityPrecision': 3, 
                'pricePrecision': 2, 
                'stepSize': '0.001', 
                'tickSize': '0.01',
                'minQty': 0.001,
                'maxQty': 1000,
                'minNotional': 5
            }
    
    def round_quantity(self, quantity: float, symbol: str) -> str:
        """Round quantity to proper precision"""
        precision_info = self.get_symbol_precision(symbol)
        decimals = precision_info['quantityPrecision']
        step_size = float(precision_info['stepSize'])
        
        rounded_qty = round(quantity / step_size) * step_size
        return f"{rounded_qty:.{decimals}f}"
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> FuturesOrderInfo:
        """Create Bybit market order"""
        try:
            quantity_float = float(quantity)
            rounded_quantity = self.round_quantity(quantity_float, symbol)
            
            params = {
                'category': 'linear',
                'symbol': symbol,
                'side': 'Buy' if side == 'BUY' else 'Sell',
                'orderType': 'Market',
                'qty': rounded_quantity,
                'timeInForce': 'GTC'
            }
            
            result = self._make_request("POST", "/v5/order/create", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=result.get('orderId', ''),
                client_order_id=result.get('orderLinkId', ''),
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=rounded_quantity,
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
            # triggerDirection: 1=rise to trigger, 2=fall to trigger
            # For SL closing LONG (side=SELL): price falls → triggerDirection=2
            # For SL closing SHORT (side=BUY): price rises → triggerDirection=1
            trigger_direction = 2 if side == 'SELL' else 1
            
            params = {
                'category': 'linear',
                'symbol': symbol,
                'side': 'Buy' if side == 'BUY' else 'Sell',
                'orderType': 'Market',
                'qty': quantity,
                'triggerPrice': stop_price,
                'triggerDirection': trigger_direction,
                'triggerBy': 'MarkPrice',
                'reduceOnly': reduce_only,
                'timeInForce': 'GTC'
            }
            
            result = self._make_request("POST", "/v5/order/create", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=result.get('orderId', ''),
                client_order_id=result.get('orderLinkId', ''),
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
            # triggerDirection: 1=rise to trigger, 2=fall to trigger
            # For TP closing LONG (side=SELL): price rises → triggerDirection=1
            # For TP closing SHORT (side=BUY): price falls → triggerDirection=2
            trigger_direction = 1 if side == 'SELL' else 2
            
            params = {
                'category': 'linear',
                'symbol': symbol,
                'side': 'Buy' if side == 'BUY' else 'Sell',
                'orderType': 'Market',
                'qty': quantity,
                'triggerPrice': stop_price,
                'triggerDirection': trigger_direction,
                'triggerBy': 'MarkPrice',
                'reduceOnly': reduce_only,
                'timeInForce': 'GTC'
            }
            
            result = self._make_request("POST", "/v5/order/create", params, signed=True)
            
            return FuturesOrderInfo(
                order_id=result.get('orderId', ''),
                client_order_id=result.get('orderLinkId', ''),
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
            params = {'category': 'linear', 'symbol': symbol}
            result = self._make_request("GET", "/v5/order/realtime", params, signed=True)
            return result.get('list', [])
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a specific order"""
        try:
            params = {
                'category': 'linear',
                'symbol': symbol,
                'orderId': order_id
            }
            self._make_request("POST", "/v5/order/cancel", params, signed=True)
            logger.info(f"❌ Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol"""
        try:
            params = {'category': 'linear', 'symbol': symbol}
            self._make_request("POST", "/v5/order/cancel-all", params, signed=True)
            logger.info(f"Cancelled all orders for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                   start_time: int = None, end_time: int = None) -> pd.DataFrame:
        """Get Bybit kline data"""
        try:
            # Convert interval format (1h -> 60, 4h -> 240)
            interval_map = {
                '1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30',
                '1h': '60', '2h': '120', '4h': '240', '6h': '360',
                '12h': '720', '1d': 'D', '1w': 'W', '1M': 'M'
            }
            
            bybit_interval = interval_map.get(interval, '60')
            
            params = {
                'category': 'linear',
                'symbol': symbol,
                'interval': bybit_interval,
                'limit': min(limit, 1000)
            }
            
            if start_time:
                params['start'] = start_time
            if end_time:
                params['end'] = end_time
            
            result = self._make_request("GET", "/v5/market/kline", params)
            
            if not result or 'list' not in result:
                raise Exception("No kline data returned")
            
            # Bybit returns [timestamp, open, high, low, close, volume, turnover]
            data = []
            for item in result['list']:
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
        """Sync with Bybit server time"""
        try:
            response = requests.get(f"{self.base_url}/v5/market/time", timeout=5)
            if response.status_code == 200:
                data = response.json()
                server_time = int(data['result']['timeSecond']) * 1000
                local_time = int(time.time() * 1000)
                self._time_offset = server_time - local_time
                logger.info(f"⏱️ Bybit server time synced, offset={self._time_offset} ms")
        except Exception as e:
            logger.warning(f"⚠️ Failed to sync Bybit server time: {e}")
            self._time_offset = 0
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for Bybit (e.g., BTC/USDT -> BTCUSDT)"""
        return symbol.replace('/', '').upper()


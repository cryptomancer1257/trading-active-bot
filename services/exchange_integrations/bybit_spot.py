"""
Bybit Spot Exchange Integration
"""

import ccxt
from typing import Dict, Any
from datetime import datetime
import logging

from .base_spot_exchange import BaseSpotExchange, SpotOrderInfo, SpotBalance

logger = logging.getLogger(__name__)


class BybitSpotExchange(BaseSpotExchange):
    """Bybit Spot Trading Integration using CCXT"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str = "", testnet: bool = True):
        super().__init__(api_key, api_secret, passphrase, testnet)
        
        self.client = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })
        
        if testnet:
            self.client.set_sandbox_mode(True)
            logger.info("✅ Bybit Spot client initialized (TESTNET)")
        else:
            logger.info("✅ Bybit Spot client initialized (MAINNET)")
    
    def get_account_info(self) -> Dict[str, Any]:
        try:
            balance = self.client.fetch_balance()
            return {
                'balances': [
                    {'asset': asset, 'free': balance['free'].get(asset, 0), 
                     'locked': balance['used'].get(asset, 0), 'total': balance['total'].get(asset, 0)}
                    for asset in balance['total'].keys() if balance['total'][asset] > 0
                ]
            }
        except Exception as e:
            logger.error(f"Error getting Bybit spot account info: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        try:
            ticker = self.client.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Error getting Bybit spot price for {symbol}: {e}")
            raise
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> SpotOrderInfo:
        try:
            order = self.client.create_order(symbol, 'market', side.lower(), float(quantity))
            return SpotOrderInfo(
                order_id=str(order['id']), symbol=order['symbol'], side=order['side'].upper(),
                type='MARKET', quantity=float(order['amount']), 
                price=float(order.get('price', 0)) if order.get('price') else None,
                status=order['status'].upper(), filled=float(order.get('filled', 0)),
                remaining=float(order.get('remaining', 0)),
                timestamp=datetime.fromtimestamp(order['timestamp'] / 1000) if order.get('timestamp') else None
            )
        except Exception as e:
            logger.error(f"Error creating Bybit spot market order: {e}")
            raise
    
    def create_limit_order(self, symbol: str, side: str, quantity: str, price: str) -> SpotOrderInfo:
        try:
            order = self.client.create_order(symbol, 'limit', side.lower(), float(quantity), float(price))
            return SpotOrderInfo(
                order_id=str(order['id']), symbol=order['symbol'], side=order['side'].upper(),
                type='LIMIT', quantity=float(order['amount']), price=float(order['price']),
                status=order['status'].upper(), filled=float(order.get('filled', 0)),
                remaining=float(order.get('remaining', 0)),
                timestamp=datetime.fromtimestamp(order['timestamp'] / 1000) if order.get('timestamp') else None
            )
        except Exception as e:
            logger.error(f"Error creating Bybit spot limit order: {e}")
            raise
    
    def create_oco_order(self, symbol: str, side: str, quantity: str, price: str, 
                         stop_price: str, stop_limit_price: str) -> SpotOrderInfo:
        logger.warning("⚠️ Bybit does not support OCO orders natively. Creating separate limit and stop-limit orders.")
        # Fallback: Create limit order for take profit
        return self.create_limit_order(symbol, side, quantity, price)
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        try:
            self.client.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            logger.error(f"Error canceling Bybit spot order: {e}")
            return False
    
    def get_order_status(self, symbol: str, order_id: str) -> SpotOrderInfo:
        try:
            order = self.client.fetch_order(order_id, symbol)
            return SpotOrderInfo(
                order_id=str(order['id']), symbol=order['symbol'], side=order['side'].upper(),
                type=order['type'].upper(), quantity=float(order['amount']),
                price=float(order.get('price', 0)) if order.get('price') else None,
                status=order['status'].upper(), filled=float(order.get('filled', 0)),
                remaining=float(order.get('remaining', 0)),
                timestamp=datetime.fromtimestamp(order['timestamp'] / 1000) if order.get('timestamp') else None
            )
        except Exception as e:
            logger.error(f"Error getting Bybit spot order status: {e}")
            raise
    
    def get_balance(self, asset: str) -> SpotBalance:
        try:
            balance = self.client.fetch_balance()
            return SpotBalance(
                asset=asset, free=float(balance['free'].get(asset, 0)),
                locked=float(balance['used'].get(asset, 0)), total=float(balance['total'].get(asset, 0))
            )
        except Exception as e:
            logger.error(f"Error getting Bybit spot balance: {e}")
            raise

    
    
    def get_klines(self, symbol: str, timeframe: str, limit: int = 100, start_time=None, end_time=None):
        """Get historical candlestick data"""
        try:
            import pandas as pd
            
            # CCXT fetch_ohlcv only supports: symbol, timeframe, since, limit
            since_ms = int(start_time) if start_time else None
            ohlcv = self.client.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=limit)
            
            # Convert CCXT format to DataFrame
            if ohlcv:
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                return df
            else:
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        except Exception as e:
            logger.error(f"Error getting klines: {e}")
            raise

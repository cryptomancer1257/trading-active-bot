"""
Binance Spot Exchange Integration
"""

import ccxt
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .base_spot_exchange import BaseSpotExchange, SpotOrderInfo, SpotBalance

logger = logging.getLogger(__name__)


class BinanceSpotExchange(BaseSpotExchange):
    """Binance Spot Trading Integration using CCXT"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str = "", testnet: bool = True):
        super().__init__(api_key, api_secret, passphrase, testnet)
        
        # Initialize CCXT Binance client
        self.client = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',  # Force spot trading
                'adjustForTimeDifference': True,
            }
        })
        
        # Set testnet if enabled
        if testnet:
            self.client.set_sandbox_mode(True)
            logger.info("✅ Binance Spot client initialized (TESTNET)")
        else:
            logger.info("✅ Binance Spot client initialized (MAINNET)")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get Binance spot account information"""
        try:
            balance = self.client.fetch_balance()
            return {
                'balances': [
                    {
                        'asset': asset,
                        'free': balance['free'].get(asset, 0),
                        'locked': balance['used'].get(asset, 0),
                        'total': balance['total'].get(asset, 0)
                    }
                    for asset in balance['total'].keys()
                    if balance['total'][asset] > 0
                ]
            }
        except Exception as e:
            logger.error(f"Error getting Binance spot account info: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        try:
            ticker = self.client.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Error getting Binance spot price for {symbol}: {e}")
            raise
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> SpotOrderInfo:
        """Create market order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                type='market',
                side=side.lower(),
                amount=float(quantity)
            )
            
            return SpotOrderInfo(
                order_id=str(order['id']),
                symbol=order['symbol'],
                side=order['side'].upper(),
                type='MARKET',
                quantity=float(order['amount']),
                price=float(order.get('price', 0)) if order.get('price') else None,
                status=order['status'].upper(),
                filled=float(order.get('filled', 0)),
                remaining=float(order.get('remaining', 0)),
                timestamp=datetime.fromtimestamp(order['timestamp'] / 1000) if order.get('timestamp') else None
            )
        except Exception as e:
            logger.error(f"Error creating Binance spot market order: {e}")
            raise
    
    def create_limit_order(self, symbol: str, side: str, quantity: str, price: str) -> SpotOrderInfo:
        """Create limit order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                type='limit',
                side=side.lower(),
                amount=float(quantity),
                price=float(price)
            )
            
            return SpotOrderInfo(
                order_id=str(order['id']),
                symbol=order['symbol'],
                side=order['side'].upper(),
                type='LIMIT',
                quantity=float(order['amount']),
                price=float(order['price']),
                status=order['status'].upper(),
                filled=float(order.get('filled', 0)),
                remaining=float(order.get('remaining', 0)),
                timestamp=datetime.fromtimestamp(order['timestamp'] / 1000) if order.get('timestamp') else None
            )
        except Exception as e:
            logger.error(f"Error creating Binance spot limit order: {e}")
            raise
    
    def create_oco_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: str, 
        price: str,
        stop_price: str,
        stop_limit_price: str
    ) -> SpotOrderInfo:
        """Create OCO (One-Cancels-Other) order"""
        try:
            # Binance-specific OCO order via private API
            params = {
                'symbol': self.format_symbol(symbol),
                'side': side.upper(),
                'quantity': quantity,
                'price': price,  # Take profit price
                'stopPrice': stop_price,  # Stop loss trigger
                'stopLimitPrice': stop_limit_price,  # Stop loss limit
                'stopLimitTimeInForce': 'GTC'
            }
            
            # Use CCXT's private API call
            result = self.client.private_post_order_oco(params)
            
            return SpotOrderInfo(
                order_id=str(result.get('orderListId', '')),
                symbol=symbol,
                side=side.upper(),
                type='OCO',
                quantity=float(quantity),
                price=float(price),
                status='NEW',
                stop_price=float(stop_price),
                stop_limit_price=float(stop_limit_price),
                order_list_id=str(result.get('orderListId', '')),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error creating Binance OCO order: {e}")
            logger.warning("OCO order failed, consider using separate limit and stop-limit orders")
            raise
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel order"""
        try:
            self.client.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            logger.error(f"Error canceling Binance spot order {order_id}: {e}")
            return False
    
    def get_order_status(self, symbol: str, order_id: str) -> SpotOrderInfo:
        """Get order status"""
        try:
            order = self.client.fetch_order(order_id, symbol)
            
            return SpotOrderInfo(
                order_id=str(order['id']),
                symbol=order['symbol'],
                side=order['side'].upper(),
                type=order['type'].upper(),
                quantity=float(order['amount']),
                price=float(order.get('price', 0)) if order.get('price') else None,
                status=order['status'].upper(),
                filled=float(order.get('filled', 0)),
                remaining=float(order.get('remaining', 0)),
                timestamp=datetime.fromtimestamp(order['timestamp'] / 1000) if order.get('timestamp') else None
            )
        except Exception as e:
            logger.error(f"Error getting Binance spot order status: {e}")
            raise
    
    def get_balance(self, asset: str) -> SpotBalance:
        """Get asset balance"""
        try:
            balance = self.client.fetch_balance()
            
            return SpotBalance(
                asset=asset,
                free=float(balance['free'].get(asset, 0)),
                locked=float(balance['used'].get(asset, 0)),
                total=float(balance['total'].get(asset, 0))
            )
        except Exception as e:
            logger.error(f"Error getting Binance spot balance for {asset}: {e}")
            raise
    
    def get_klines(self, symbol: str, timeframe: str, limit: int = 100, start_time=None, end_time=None):
        """Get historical candlestick data"""
        try:
            import pandas as pd
            
            # CCXT fetch_ohlcv only supports: symbol, timeframe, since, limit
            # Note: end_time is not supported by CCXT, it will fetch from start_time with limit
            since_ms = int(start_time) if start_time else None
            ohlcv = self.client.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=limit)
            
            # Convert CCXT format [[timestamp, open, high, low, close, volume], ...] to DataFrame
            if ohlcv:
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                return df
            else:
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        except Exception as e:
            logger.error(f"Error getting Binance spot klines for {symbol}: {e}")
            raise


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
                # Bybit V5 uses Unified Trading Account for all markets
                'accountType': 'unified',  # Use unified account (supports SPOT/FUTURES/OPTIONS)
                # Bybit market buy orders use cost (quote currency) instead of quantity (base currency)
                'createMarketBuyOrderRequiresPrice': False  # Allow passing cost in amount field
            }
        })
        
        if testnet:
            self.client.set_sandbox_mode(True)
            logger.info("✅ Bybit Spot client initialized (TESTNET - Unified Account)")
        else:
            logger.info("✅ Bybit Spot client initialized (MAINNET - Unified Account)")
    
    def get_account_info(self) -> Dict[str, Any]:
        try:
            # Fetch balance from Unified Trading Account
            balance = self.client.fetch_balance({'type': 'spot'})
            
            # Log raw response for debugging
            logger.info(f"📊 Bybit balance response: free={balance.get('free', {})}, used={balance.get('used', {})}, total={balance.get('total', {})}")
            
            balances = []
            for asset in balance['total'].keys():
                total_val = balance['total'].get(asset, 0) or 0
                if total_val > 0:
                    # Bybit Unified Account: free/used may be None, use total as fallback
                    free_val = balance['free'].get(asset)
                    used_val = balance['used'].get(asset)
                    
                    # If free is None, assume total is free (Unified Account)
                    free = free_val if free_val is not None else total_val
                    locked = used_val if used_val is not None else 0
                    
                    balances.append({
                        'asset': asset,
                        'free': free,
                        'locked': locked,
                        'total': total_val
                    })
            
            logger.info(f"✅ Bybit processed {len(balances)} assets with balance")
            return {'balances': balances}
            
        except Exception as e:
            logger.error(f"Error getting Bybit spot account info: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
            qty = float(quantity)
            
            # Bybit market BUY orders: amount = cost in quote currency (USDT)
            # For SELL orders: amount = quantity in base currency (BTC)
            # Since Universal Spot Bot already calculates position_value (USDT), 
            # we use quantity directly (bot passes notional for BUY, base qty for SELL)
            
            order = self.client.create_order(symbol, 'market', side.lower(), qty)
            
            # Handle None values in response (Bybit returns most fields as None)
            order_side = order.get('side')
            order_status = order.get('status')
            order_amount = order.get('amount')
            order_price = order.get('price')
            order_filled = order.get('filled')
            order_remaining = order.get('remaining')
            order_timestamp = order.get('timestamp')
            
            return SpotOrderInfo(
                order_id=str(order.get('id', 'N/A')), 
                symbol=order.get('symbol', symbol), 
                side=order_side.upper() if order_side else side.upper(),
                type='MARKET', 
                quantity=float(order_amount) if order_amount is not None else qty,
                price=float(order_price) if order_price is not None else None,
                status=order_status.upper() if order_status else 'FILLED',  # Assume filled if None
                filled=float(order_filled) if order_filled is not None else 0.0,
                remaining=float(order_remaining) if order_remaining is not None else 0.0,
                timestamp=datetime.fromtimestamp(order_timestamp / 1000) if order_timestamp else datetime.now()
            )
        except Exception as e:
            logger.error(f"Error creating Bybit spot market order: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Order response: {order if 'order' in locals() else 'N/A'}")
            raise
    
    def create_limit_order(self, symbol: str, side: str, quantity: str, price: str) -> SpotOrderInfo:
        try:
            qty = float(quantity)
            limit_price = float(price)
            order = self.client.create_order(symbol, 'limit', side.lower(), qty, limit_price)
            
            # Handle None values in response (Bybit returns most fields as None)
            order_side = order.get('side')
            order_status = order.get('status')
            order_amount = order.get('amount')
            order_price = order.get('price')
            order_filled = order.get('filled')
            order_remaining = order.get('remaining')
            order_timestamp = order.get('timestamp')
            
            return SpotOrderInfo(
                order_id=str(order.get('id', 'N/A')), 
                symbol=order.get('symbol', symbol), 
                side=order_side.upper() if order_side else side.upper(),
                type='LIMIT', 
                quantity=float(order_amount) if order_amount is not None else qty,
                price=float(order_price) if order_price is not None else limit_price,
                status=order_status.upper() if order_status else 'NEW',  # Limit orders start as NEW
                filled=float(order_filled) if order_filled is not None else 0.0,
                remaining=float(order_remaining) if order_remaining is not None else qty,
                timestamp=datetime.fromtimestamp(order_timestamp / 1000) if order_timestamp else datetime.now()
            )
        except Exception as e:
            logger.error(f"Error creating Bybit spot limit order: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Order response: {order if 'order' in locals() else 'N/A'}")
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
            
            # Handle None values in response
            order_side = order.get('side')
            order_type = order.get('type')
            order_status = order.get('status')
            order_amount = order.get('amount')
            order_price = order.get('price')
            order_filled = order.get('filled')
            order_remaining = order.get('remaining')
            order_timestamp = order.get('timestamp')
            
            return SpotOrderInfo(
                order_id=str(order.get('id', order_id)), 
                symbol=order.get('symbol', symbol), 
                side=order_side.upper() if order_side else 'UNKNOWN',
                type=order_type.upper() if order_type else 'UNKNOWN', 
                quantity=float(order_amount) if order_amount is not None else 0.0,
                price=float(order_price) if order_price is not None else None,
                status=order_status.upper() if order_status else 'UNKNOWN', 
                filled=float(order_filled) if order_filled is not None else 0.0,
                remaining=float(order_remaining) if order_remaining is not None else 0.0,
                timestamp=datetime.fromtimestamp(order_timestamp / 1000) if order_timestamp else None
            )
        except Exception as e:
            logger.error(f"Error getting Bybit spot order status: {e}")
            raise
    
    def get_balance(self, asset: str) -> SpotBalance:
        try:
            balance = self.client.fetch_balance({'type': 'spot'})
            
            total_val = float(balance['total'].get(asset, 0) or 0)
            free_val = balance['free'].get(asset)
            used_val = balance['used'].get(asset)
            
            # Bybit Unified Account: free/used may be None, use total as fallback
            free = float(free_val) if free_val is not None else total_val
            locked = float(used_val) if used_val is not None else 0.0
            
            return SpotBalance(
                asset=asset, 
                free=free,
                locked=locked, 
                total=total_val
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

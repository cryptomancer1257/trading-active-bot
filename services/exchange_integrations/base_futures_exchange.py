"""
Base Abstract Class for Futures Exchange Integration
Provides unified interface for all futures exchanges
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@dataclass
class FuturesOrderInfo:
    """Unified futures order information across all exchanges"""
    order_id: str
    client_order_id: str
    symbol: str
    side: str
    type: str
    quantity: str
    price: str
    status: str
    executed_qty: str
    time_in_force: str = "GTC"
    
@dataclass
class FuturesPosition:
    """Unified futures position information across all exchanges"""
    symbol: str
    side: str  # LONG or SHORT
    size: str
    entry_price: str
    mark_price: str
    pnl: str
    percentage: str

class BaseFuturesExchange(ABC):
    """
    Abstract base class for futures exchange integration
    All exchange implementations must inherit from this class
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self._time_offset = 0
        self._symbol_info_cache = {}
        
        logger.info(f"Initialized {self.__class__.__name__} {'TESTNET' if testnet else 'PRODUCTION'}")
    
    @property
    @abstractmethod
    def exchange_name(self) -> str:
        """Return exchange name (e.g., 'BINANCE', 'BYBIT')"""
        pass
    
    @abstractmethod
    def test_connectivity(self) -> bool:
        """Test API connectivity"""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """Get futures account information"""
        pass
    
    @abstractmethod
    def get_position_info(self, symbol: str = None) -> List[FuturesPosition]:
        """Get position information"""
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        pass
    
    @abstractmethod
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        pass
    
    @abstractmethod
    def get_symbol_precision(self, symbol: str) -> dict:
        """Get quantity and price precision for symbol"""
        pass
    
    @abstractmethod
    def round_quantity(self, quantity: float, symbol: str) -> str:
        """Round quantity to proper precision"""
        pass
    
    @abstractmethod
    def create_market_order(self, symbol: str, side: str, quantity: str) -> FuturesOrderInfo:
        """Create futures market order"""
        pass
    
    @abstractmethod
    def create_stop_loss_order(self, symbol: str, side: str, quantity: str, 
                              stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
        """Create stop loss order"""
        pass
    
    @abstractmethod
    def create_take_profit_order(self, symbol: str, side: str, quantity: str, 
                                stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
        """Create take profit order"""
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """Get all open orders for symbol"""
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a specific order"""
        pass
    
    @abstractmethod
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol"""
        pass
    
    @abstractmethod
    def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                   start_time: int = None, end_time: int = None) -> pd.DataFrame:
        """Get futures kline/candlestick data"""
        pass
    
    def get_positions(self):
        """Alias for get_position_info for compatibility"""
        return self.get_position_info()
    
    def create_managed_orders(self, symbol: str, side: str, quantity: str,
                            stop_price: str, take_profit_price: str,
                            reduce_only: bool = True) -> Dict[str, Any]:
        """
        Create managed orders (SL + TP) - Default implementation
        Intelligently handles small positions by skipping split when necessary
        """
        try:
            # Cancel existing orders first
            existing_orders = self.get_open_orders(symbol)
            for order in existing_orders:
                if order.get('type') in ['STOP_MARKET', 'TAKE_PROFIT_MARKET']:
                    self.cancel_order(symbol, str(order.get('orderId', order.get('order_id', ''))))
            
            # Get exchange minimums
            precision_info = self.get_symbol_precision(symbol)
            min_qty = precision_info.get('minQty', 0.001)
            step_size = float(precision_info.get('stepSize', '0.001'))
            
            total_qty = float(quantity)
            
            # Check if quantity is large enough to split (each half must exceed minimum)
            # We need at least 2.2x minimum to safely split (with some buffer)
            can_split = (total_qty / 2.0) >= (min_qty * 1.1)
            
            if not can_split:
                logger.warning(f"⚠️ Quantity {total_qty} too small to split (min={min_qty}). Creating single TP order instead.")
            
            # Create stop loss (always full quantity)
            stop_response = self.create_stop_loss_order(
                symbol=symbol,
                side=side,
                quantity=f"{total_qty:.5f}",
                stop_price=stop_price,
                reduce_only=reduce_only
            )
            
            # Create take profit orders
            tp1_price = float(take_profit_price)
            tp_orders = []
            
            if can_split:
                # Split into two TP orders for partial profit taking
                partial_qty = round((total_qty * 0.5) / step_size) * step_size
                remaining_qty = round((total_qty - partial_qty) / step_size) * step_size
                
                # Safety check: ensure both parts meet minimum
                if partial_qty >= min_qty and remaining_qty >= min_qty:
                    tp1_response = self.create_take_profit_order(
                        symbol=symbol,
                        side=side,
                        quantity=f"{partial_qty:.5f}",
                        stop_price=f"{tp1_price:.2f}",
                        reduce_only=reduce_only
                    )
                    
                    tp2_price = tp1_price * 1.02  # 2% higher
                    tp2_response = self.create_take_profit_order(
                        symbol=symbol,
                        side=side,
                        quantity=f"{remaining_qty:.5f}",
                        stop_price=f"{tp2_price:.2f}",
                        reduce_only=reduce_only
                    )
                    
                    tp_orders = [
                        {
                            'order_id': tp1_response.order_id,
                            'quantity': partial_qty,
                            'price': tp1_price,
                            'type': 'partial'
                        },
                        {
                            'order_id': tp2_response.order_id,
                            'quantity': remaining_qty,
                            'price': tp2_price,
                            'type': 'profit'
                        }
                    ]
                    logger.info(f"✅ Split TP: {partial_qty} @ ${tp1_price:.2f} + {remaining_qty} @ ${tp2_price:.2f}")
                else:
                    # Fallback to single TP
                    can_split = False
            
            if not can_split:
                # Create single take profit order with full quantity
                tp_response = self.create_take_profit_order(
                    symbol=symbol,
                    side=side,
                    quantity=f"{total_qty:.5f}",
                    stop_price=f"{tp1_price:.2f}",
                    reduce_only=reduce_only
                )
                
                tp_orders = [
                    {
                        'order_id': tp_response.order_id,
                        'quantity': total_qty,
                        'price': tp1_price,
                        'type': 'full'
                    }
                ]
                logger.info(f"✅ Single TP: {total_qty} @ ${tp1_price:.2f}")
            
            logger.info(f"✅ Managed Orders Created on {self.exchange_name}")
            
            return {
                'stop_loss_order': {
                    'order_id': stop_response.order_id,
                    'quantity': total_qty,
                    'price': stop_price
                },
                'take_profit_orders': tp_orders
            }
        except Exception as e:
            logger.error(f"Failed to create managed orders on {self.exchange_name}: {e}")
            raise
    
    @abstractmethod
    def _sync_server_time(self):
        """Sync local time with exchange server time"""
        pass
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize trading pair format for specific exchange
        Override this in exchange-specific implementations if needed
        """
        return symbol.replace('/', '').upper()


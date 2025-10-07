"""
Base Spot Exchange Interface
Abstract base class for spot trading across different exchanges
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SpotOrderInfo:
    """Spot order information"""
    order_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    type: str  # 'MARKET', 'LIMIT', 'OCO'
    quantity: float
    price: Optional[float] = None
    status: str = 'NEW'
    filled: float = 0.0
    remaining: float = 0.0
    timestamp: Optional[datetime] = None
    
    # OCO specific fields
    stop_price: Optional[float] = None
    stop_limit_price: Optional[float] = None
    order_list_id: Optional[str] = None  # For OCO orders


@dataclass
class SpotBalance:
    """Spot account balance"""
    asset: str
    free: float
    locked: float
    total: float


class BaseSpotExchange(ABC):
    """
    Abstract base class for spot exchange integrations
    Provides unified interface for spot trading across different exchanges
    """
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str = "", testnet: bool = True):
        """
        Initialize spot exchange client
        
        Args:
            api_key: Exchange API key
            api_secret: Exchange API secret
            passphrase: API passphrase (required for OKX, Bitget)
            testnet: Use testnet/demo trading
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.testnet = testnet
        self.exchange_name = self.__class__.__name__.replace('SpotExchange', '').upper()
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information and balances
        
        Returns:
            Dict containing account info with balances
        """
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            
        Returns:
            Current price as float
        """
        pass
    
    @abstractmethod
    def create_market_order(self, symbol: str, side: str, quantity: str) -> SpotOrderInfo:
        """
        Create market order (instant execution at market price)
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            
        Returns:
            SpotOrderInfo with order details
        """
        pass
    
    @abstractmethod
    def create_limit_order(self, symbol: str, side: str, quantity: str, price: str) -> SpotOrderInfo:
        """
        Create limit order (executes at specified price)
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Limit price
            
        Returns:
            SpotOrderInfo with order details
        """
        pass
    
    @abstractmethod
    def create_oco_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: str, 
        price: str,
        stop_price: str,
        stop_limit_price: str
    ) -> SpotOrderInfo:
        """
        Create OCO (One-Cancels-Other) order for take-profit and stop-loss
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Take-profit limit price
            stop_price: Stop-loss trigger price
            stop_limit_price: Stop-loss limit price
            
        Returns:
            SpotOrderInfo with OCO order details
            
        Note:
            Not all exchanges support OCO orders. Check exchange capabilities.
        """
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel an open order
        
        Args:
            symbol: Trading pair
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_order_status(self, symbol: str, order_id: str) -> SpotOrderInfo:
        """
        Get order status
        
        Args:
            symbol: Trading pair
            order_id: Order ID
            
        Returns:
            SpotOrderInfo with current order status
        """
        pass
    
    @abstractmethod
    def get_balance(self, asset: str) -> SpotBalance:
        """
        Get balance for specific asset
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'USDT')
            
        Returns:
            SpotBalance with asset balance details
        """
        pass
    
    @abstractmethod
    def get_klines(self, symbol: str, timeframe: str, limit: int = 100):
        """
        Get historical candlestick data
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Timeframe (e.g., '1h', '4h', '1d')
            limit: Number of candles to fetch
            
        Returns:
            List of OHLCV data
        """
        pass
    
    def format_symbol(self, symbol: str) -> str:
        """
        Format symbol to exchange-specific format
        Default: BTCUSDT format (most exchanges use this)
        Override in exchange-specific implementations if needed
        
        Args:
            symbol: Symbol in standard format (e.g., 'BTC/USDT')
            
        Returns:
            Exchange-specific symbol format
        """
        return symbol.replace('/', '')
    
    def __repr__(self):
        return f"{self.exchange_name}SpotExchange(testnet={self.testnet})"


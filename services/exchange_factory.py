"""
Exchange Factory Module
Manages multiple cryptocurrency exchanges and provides unified interface
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import pandas as pd
from datetime import datetime
from dataclasses import dataclass

from services.binance_integration import BinanceIntegration, OrderInfo, BalanceInfo

logger = logging.getLogger(__name__)

@dataclass
class ExchangeCapabilities:
    """Exchange capabilities and features"""
    spot_trading: bool = True
    futures_trading: bool = False
    margin_trading: bool = False
    stop_loss_orders: bool = True
    take_profit_orders: bool = True
    advanced_orders: bool = False
    api_key_permissions: List[str] = None

class BaseExchange(ABC):
    """Abstract base class for all exchange integrations"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.exchange_name = self.__class__.__name__.replace('Integration', '').upper()
        
    @abstractmethod
    def test_connectivity(self) -> bool:
        """Test connection to exchange API"""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        pass
    
    @abstractmethod
    def get_balance(self, asset: str) -> BalanceInfo:
        """Get balance for specific asset"""
        pass
    
    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information for symbol"""
        pass
    
    @abstractmethod
    def create_market_order(self, symbol: str, side: str, quantity: str) -> OrderInfo:
        """Create market order"""
        pass
    
    @abstractmethod
    def create_limit_order(self, symbol: str, side: str, quantity: str, price: str) -> OrderInfo:
        """Create limit order"""
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        """Cancel order"""
        pass
    
    @abstractmethod
    def get_klines(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        """Get historical price data"""
        pass
    
    @abstractmethod
    def calculate_quantity(self, symbol: str, side: str, amount: float, price: float) -> Tuple[str, Dict[str, Any]]:
        """Calculate proper quantity based on exchange rules"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> ExchangeCapabilities:
        """Get exchange capabilities"""
        pass

class BinanceAdapter(BaseExchange):
    """Binance exchange adapter"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.client = BinanceIntegration(api_key, api_secret, testnet)
    
    def test_connectivity(self) -> bool:
        return self.client.test_connectivity()
    
    def get_account_info(self) -> Dict[str, Any]:
        return self.client.get_account_info()
    
    def get_balance(self, asset: str) -> BalanceInfo:
        return self.client.get_balance(asset)
    
    def get_current_price(self, symbol: str) -> float:
        return self.client.get_current_price(symbol)
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information for symbol"""
        try:
            price = self.client.get_current_price(symbol)
            return {
                'symbol': symbol,
                'price': str(price),
                'last_price': str(price)
            }
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            raise
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> OrderInfo:
        return self.client.create_market_order(symbol, side, quantity)
    
    def create_limit_order(self, symbol: str, side: str, quantity: str, price: str) -> OrderInfo:
        return self.client.create_limit_order(symbol, side, quantity, price)
    
    def create_stop_loss_order(self, symbol: str, side: str, quantity: str, stop_price: str) -> OrderInfo:
        return self.client.create_stop_loss_order(symbol, side, quantity, stop_price)
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        return self.client.cancel_order(symbol, order_id)
    
    def get_klines(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        return self.client.get_klines(symbol, interval, limit)
    
    def calculate_quantity(self, symbol: str, side: str, amount: float, price: float) -> Tuple[str, Dict[str, Any]]:
        return self.client.calculate_quantity(symbol, side, amount, price)
    
    @property
    def capabilities(self) -> ExchangeCapabilities:
        return ExchangeCapabilities(
            spot_trading=True,
            futures_trading=True,
            margin_trading=True,
            stop_loss_orders=True,
            take_profit_orders=True,
            advanced_orders=True,
            api_key_permissions=["spot", "futures", "margin"]
        )

class CoinbaseAdapter(BaseExchange):
    """Coinbase Pro exchange adapter"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.base_url = "https://api-public.sandbox.pro.coinbase.com" if testnet else "https://api.pro.coinbase.com"
        # Initialize Coinbase Pro client here
        try:
            import cbpro
            self.client = cbpro.AuthenticatedClient(
                key=api_key,
                secret=api_secret,
                passphrase="",  # Would need passphrase parameter
                sandbox=testnet
            )
        except ImportError:
            logger.warning("cbpro library not installed. Coinbase functionality limited.")
            self.client = None
    
    def test_connectivity(self) -> bool:
        try:
            if not self.client:
                return False
            accounts = self.client.get_accounts()
            return isinstance(accounts, list)
        except Exception as e:
            logger.error(f"Coinbase connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        try:
            if not self.client:
                raise Exception("Coinbase client not initialized")
            accounts = self.client.get_accounts()
            return {"accounts": accounts}
        except Exception as e:
            logger.error(f"Failed to get Coinbase account info: {e}")
            raise
    
    def get_balance(self, asset: str) -> BalanceInfo:
        try:
            if not self.client:
                raise Exception("Coinbase client not initialized")
            accounts = self.client.get_accounts()
            for account in accounts:
                if account['currency'] == asset:
                    return BalanceInfo(
                        asset=account['currency'],
                        free=account['available'],
                        locked=account['hold']
                    )
            raise Exception(f"Asset {asset} not found")
        except Exception as e:
            logger.error(f"Failed to get Coinbase balance: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        try:
            if not self.client:
                raise Exception("Coinbase client not initialized")
            # Convert BTC/USDT to BTC-USD format
            cb_symbol = symbol.replace('/', '-').replace('USDT', 'USD')
            ticker = self.client.get_product_ticker(cb_symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"Failed to get Coinbase price: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information for symbol"""
        try:
            price = self.get_current_price(symbol)
            return {
                'symbol': symbol,
                'price': str(price),
                'last_price': str(price)
            }
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            raise
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> OrderInfo:
        try:
            if not self.client:
                raise Exception("Coinbase client not initialized")
            cb_symbol = symbol.replace('/', '-').replace('USDT', 'USD')
            
            order = self.client.place_market_order(
                product_id=cb_symbol,
                side=side.lower(),
                size=quantity
            )
            
            return OrderInfo(
                order_id=int(order['id']),
                client_order_id=order.get('client_oid', ''),
                symbol=symbol,
                side=side,
                type='market',
                quantity=quantity,
                price='0',
                status=order['status'],
                executed_qty=order.get('filled_size', '0')
            )
        except Exception as e:
            logger.error(f"Failed to create Coinbase market order: {e}")
            raise
    
    def create_limit_order(self, symbol: str, side: str, quantity: str, price: str) -> OrderInfo:
        try:
            if not self.client:
                raise Exception("Coinbase client not initialized")
            cb_symbol = symbol.replace('/', '-').replace('USDT', 'USD')
            
            order = self.client.place_limit_order(
                product_id=cb_symbol,
                side=side.lower(),
                size=quantity,
                price=price
            )
            
            return OrderInfo(
                order_id=int(order['id']),
                client_order_id=order.get('client_oid', ''),
                symbol=symbol,
                side=side,
                type='limit',
                quantity=quantity,
                price=price,
                status=order['status'],
                executed_qty=order.get('filled_size', '0')
            )
        except Exception as e:
            logger.error(f"Failed to create Coinbase limit order: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        try:
            if not self.client:
                return False
            result = self.client.cancel_order(str(order_id))
            return True
        except Exception as e:
            logger.error(f"Failed to cancel Coinbase order: {e}")
            return False
    
    def get_klines(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        try:
            if not self.client:
                raise Exception("Coinbase client not initialized")
            cb_symbol = symbol.replace('/', '-').replace('USDT', 'USD')
            
            # Convert interval to Coinbase format
            granularity_map = {
                '1m': 60, '5m': 300, '15m': 900, '1h': 3600, '1d': 86400
            }
            granularity = granularity_map.get(interval, 3600)
            
            data = self.client.get_product_historic_rates(
                cb_symbol, granularity=granularity
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=['timestamp', 'low', 'high', 'open', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('timestamp')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].head(limit)
        except Exception as e:
            logger.error(f"Failed to get Coinbase klines: {e}")
            raise
    
    def calculate_quantity(self, symbol: str, side: str, amount: float, price: float) -> Tuple[str, Dict[str, Any]]:
        # Simplified calculation for Coinbase
        if side == "BUY":
            quantity = amount / price
        else:
            quantity = amount
        
        # Round to 8 decimal places
        quantity = round(quantity, 8)
        quantity_str = f"{quantity:.8f}".rstrip('0').rstrip('.')
        
        return quantity_str, {
            'calculated_quantity': quantity,
            'precision': 8
        }
    
    @property
    def capabilities(self) -> ExchangeCapabilities:
        return ExchangeCapabilities(
            spot_trading=True,
            futures_trading=False,
            margin_trading=False,
            stop_loss_orders=True,
            take_profit_orders=False,
            advanced_orders=False,
            api_key_permissions=["view", "trade"]
        )

class KrakenAdapter(BaseExchange):
    """Kraken exchange adapter"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        try:
            import krakenex
            self.client = krakenex.API(key=api_key, secret=api_secret)
        except ImportError:
            logger.warning("krakenex library not installed. Kraken functionality limited.")
            self.client = None
    
    def test_connectivity(self) -> bool:
        try:
            if not self.client:
                return False
            response = self.client.query_public('Time')
            return 'error' not in response or len(response['error']) == 0
        except Exception as e:
            logger.error(f"Kraken connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        try:
            if not self.client:
                raise Exception("Kraken client not initialized")
            balance = self.client.query_private('Balance')
            return balance
        except Exception as e:
            logger.error(f"Failed to get Kraken account info: {e}")
            raise
    
    def get_balance(self, asset: str) -> BalanceInfo:
        try:
            account_info = self.get_account_info()
            if 'error' in account_info and account_info['error']:
                raise Exception(f"Kraken API error: {account_info['error']}")
            
            # Kraken uses different asset names (ZUSD instead of USDT)
            kraken_asset = asset
            if asset == 'USDT':
                kraken_asset = 'USDT'
            elif asset == 'BTC':
                kraken_asset = 'XXBT'
            
            balance = account_info.get('result', {}).get(kraken_asset, '0')
            
            return BalanceInfo(
                asset=asset,
                free=balance,
                locked='0'  # Kraken doesn't separate free/locked in balance call
            )
        except Exception as e:
            logger.error(f"Failed to get Kraken balance: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        try:
            if not self.client:
                raise Exception("Kraken client not initialized")
            
            # Convert to Kraken format (BTCUSD, ETHUSD, etc.)
            kraken_symbol = symbol.replace('/', '').replace('USDT', 'USD')
            if 'BTC' in kraken_symbol:
                kraken_symbol = kraken_symbol.replace('BTC', 'XBT')
            
            response = self.client.query_public('Ticker', {'pair': kraken_symbol})
            if 'error' in response and response['error']:
                raise Exception(f"Kraken API error: {response['error']}")
            
            ticker_data = list(response['result'].values())[0]
            return float(ticker_data['c'][0])  # Last trade price
        except Exception as e:
            logger.error(f"Failed to get Kraken price: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information for symbol"""
        try:
            price = self.get_current_price(symbol)
            return {
                'symbol': symbol,
                'price': str(price),
                'last_price': str(price)
            }
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            raise
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> OrderInfo:
        try:
            if not self.client:
                raise Exception("Kraken client not initialized")
            
            kraken_symbol = symbol.replace('/', '').replace('USDT', 'USD')
            if 'BTC' in kraken_symbol:
                kraken_symbol = kraken_symbol.replace('BTC', 'XBT')
            
            order_data = {
                'pair': kraken_symbol,
                'type': side.lower(),
                'ordertype': 'market',
                'volume': quantity
            }
            
            response = self.client.query_private('AddOrder', order_data)
            if 'error' in response and response['error']:
                raise Exception(f"Kraken order error: {response['error']}")
            
            return OrderInfo(
                order_id=int(response['result']['txid'][0], 16),  # Convert hex to int
                client_order_id='',
                symbol=symbol,
                side=side,
                type='market',
                quantity=quantity,
                price='0',
                status='pending',
                executed_qty='0'
            )
        except Exception as e:
            logger.error(f"Failed to create Kraken market order: {e}")
            raise
    
    def create_limit_order(self, symbol: str, side: str, quantity: str, price: str) -> OrderInfo:
        try:
            if not self.client:
                raise Exception("Kraken client not initialized")
            
            kraken_symbol = symbol.replace('/', '').replace('USDT', 'USD')
            if 'BTC' in kraken_symbol:
                kraken_symbol = kraken_symbol.replace('BTC', 'XBT')
            
            order_data = {
                'pair': kraken_symbol,
                'type': side.lower(),
                'ordertype': 'limit',
                'volume': quantity,
                'price': price
            }
            
            response = self.client.query_private('AddOrder', order_data)
            if 'error' in response and response['error']:
                raise Exception(f"Kraken order error: {response['error']}")
            
            return OrderInfo(
                order_id=int(response['result']['txid'][0], 16),
                client_order_id='',
                symbol=symbol,
                side=side,
                type='limit',
                quantity=quantity,
                price=price,
                status='pending',
                executed_qty='0'
            )
        except Exception as e:
            logger.error(f"Failed to create Kraken limit order: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> bool:
        try:
            if not self.client:
                return False
            
            response = self.client.query_private('CancelOrder', {'txid': hex(order_id)})
            return 'error' not in response or len(response.get('error', [])) == 0
        except Exception as e:
            logger.error(f"Failed to cancel Kraken order: {e}")
            return False
    
    def get_klines(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        try:
            if not self.client:
                raise Exception("Kraken client not initialized")
            
            kraken_symbol = symbol.replace('/', '').replace('USDT', 'USD')
            if 'BTC' in kraken_symbol:
                kraken_symbol = kraken_symbol.replace('BTC', 'XBT')
            
            # Convert interval to Kraken format
            interval_map = {
                '1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60, '4h': 240, '1d': 1440
            }
            kraken_interval = interval_map.get(interval, 60)
            
            response = self.client.query_public('OHLC', {
                'pair': kraken_symbol,
                'interval': kraken_interval
            })
            
            if 'error' in response and response['error']:
                raise Exception(f"Kraken API error: {response['error']}")
            
            ohlc_data = list(response['result'].values())[0]
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlc_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].head(limit)
        except Exception as e:
            logger.error(f"Failed to get Kraken klines: {e}")
            raise
    
    def calculate_quantity(self, symbol: str, side: str, amount: float, price: float) -> Tuple[str, Dict[str, Any]]:
        if side == "BUY":
            quantity = amount / price
        else:
            quantity = amount
        
        # Round to 8 decimal places for Kraken
        quantity = round(quantity, 8)
        quantity_str = f"{quantity:.8f}".rstrip('0').rstrip('.')
        
        return quantity_str, {
            'calculated_quantity': quantity,
            'precision': 8
        }
    
    @property
    def capabilities(self) -> ExchangeCapabilities:
        return ExchangeCapabilities(
            spot_trading=True,
            futures_trading=True,
            margin_trading=True,
            stop_loss_orders=True,
            take_profit_orders=True,
            advanced_orders=True,
            api_key_permissions=["query", "trade"]
        )

class ExchangeFactory:
    """Factory for creating exchange adapters"""
    
    _exchanges = {
        'BINANCE': BinanceAdapter,
        'COINBASE': CoinbaseAdapter,
        'KRAKEN': KrakenAdapter
    }
    
    @classmethod
    def create_exchange(cls, exchange_name: str, api_key: str, api_secret: str, 
                       testnet: bool = True, **kwargs) -> BaseExchange:
        """Create exchange adapter instance"""
        exchange_name = exchange_name.upper()
        
        if exchange_name not in cls._exchanges:
            available = ', '.join(cls._exchanges.keys())
            raise ValueError(f"Unsupported exchange: {exchange_name}. Available: {available}")
        
        exchange_class = cls._exchanges[exchange_name]
        
        try:
            # Pass additional parameters if needed
            if exchange_name == 'COINBASE' and 'passphrase' in kwargs:
                # Handle Coinbase passphrase if provided
                pass
            
            return exchange_class(api_key, api_secret, testnet)
        except Exception as e:
            logger.error(f"Failed to create {exchange_name} adapter: {e}")
            raise
    
    @classmethod
    def register_exchange(cls, name: str, exchange_class: type):
        """Register a new exchange adapter"""
        if not issubclass(exchange_class, BaseExchange):
            raise ValueError("Exchange class must inherit from BaseExchange")
        
        cls._exchanges[name.upper()] = exchange_class
        logger.info(f"Registered new exchange: {name.upper()}")
    
    @classmethod
    def get_supported_exchanges(cls) -> List[str]:
        """Get list of supported exchanges"""
        return list(cls._exchanges.keys())
    
    @classmethod
    def get_exchange_capabilities(cls, exchange_name: str) -> ExchangeCapabilities:
        """Get capabilities for specific exchange"""
        exchange_name = exchange_name.upper()
        if exchange_name not in cls._exchanges:
            raise ValueError(f"Unsupported exchange: {exchange_name}")
        
        # Create temporary instance to get capabilities
        try:
            temp_instance = cls._exchanges[exchange_name]("", "", True)
            return temp_instance.capabilities
        except Exception:
            # Return default capabilities if instantiation fails
            return ExchangeCapabilities()

def validate_exchange_credentials(exchange_name: str, api_key: str, api_secret: str, 
                                testnet: bool = True, **kwargs) -> Tuple[bool, str]:
    """Validate exchange credentials"""
    try:
        exchange = ExchangeFactory.create_exchange(exchange_name, api_key, api_secret, testnet, **kwargs)
        
        if not exchange.test_connectivity():
            return False, f"Failed to connect to {exchange_name}"
        
        # Test account access
        account_info = exchange.get_account_info()
        if not account_info:
            return False, f"Failed to get {exchange_name} account information"
        
        return True, f"{exchange_name} credentials validated successfully"
        
    except Exception as e:
        return False, f"{exchange_name} validation failed: {str(e)}" 
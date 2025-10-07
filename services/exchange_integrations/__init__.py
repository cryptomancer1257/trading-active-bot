"""
Exchange Integrations for Multi-Exchange Futures and Spot Trading
Supports: Binance, Bybit, OKX, Bitget, Huobi, Kraken
"""

# Futures imports
from .base_futures_exchange import BaseFuturesExchange, FuturesOrderInfo, FuturesPosition
from .exchange_factory import create_futures_exchange

# Spot imports
from .base_spot_exchange import BaseSpotExchange, SpotOrderInfo, SpotBalance
from .exchange_factory import create_spot_exchange

__all__ = [
    # Futures
    'BaseFuturesExchange',
    'FuturesOrderInfo', 
    'FuturesPosition',
    'create_futures_exchange',
    # Spot
    'BaseSpotExchange',
    'SpotOrderInfo',
    'SpotBalance',
    'create_spot_exchange'
]


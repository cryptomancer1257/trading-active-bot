"""
Exchange Factory for Multi-Exchange Futures Trading
Dynamically creates exchange integration based on exchange name
"""

import logging
from typing import Optional, Dict, Any

from .base_futures_exchange import BaseFuturesExchange
from .binance_futures import BinanceFuturesIntegration
from .bybit_futures import BybitFuturesIntegration
from .okx_futures import OKXFuturesIntegration
from .bitget_futures import BitgetFuturesIntegration
from .huobi_futures import HuobiFuturesIntegration
from .kraken_futures import KrakenFuturesIntegration

logger = logging.getLogger(__name__)

# Exchange registry mapping
EXCHANGE_REGISTRY = {
    'BINANCE': BinanceFuturesIntegration,
    'BYBIT': BybitFuturesIntegration,
    'OKX': OKXFuturesIntegration,
    'BITGET': BitgetFuturesIntegration,
    'HUOBI': HuobiFuturesIntegration,
    'HTX': HuobiFuturesIntegration,  # Alias for Huobi
    'KRAKEN': KrakenFuturesIntegration
}

# Supported exchanges list for validation
SUPPORTED_EXCHANGES = list(EXCHANGE_REGISTRY.keys())

def create_futures_exchange(
    exchange_name: str,
    api_key: str,
    api_secret: str,
    passphrase: str = "",
    testnet: bool = True
) -> BaseFuturesExchange:
    """
    Factory function to create futures exchange integration
    
    Args:
        exchange_name: Name of exchange (BINANCE, BYBIT, OKX, BITGET, HUOBI, KRAKEN)
        api_key: Exchange API key
        api_secret: Exchange API secret
        passphrase: API passphrase (required for OKX, Bitget)
        testnet: Use testnet/demo trading (default: True)
    
    Returns:
        BaseFuturesExchange: Exchange integration instance
    
    Raises:
        ValueError: If exchange is not supported
        
    Example:
        >>> exchange = create_futures_exchange(
        ...     exchange_name='BINANCE',
        ...     api_key='your_key',
        ...     api_secret='your_secret',
        ...     testnet=True
        ... )
    """
    exchange_name = exchange_name.upper().strip()
    
    if exchange_name not in EXCHANGE_REGISTRY:
        raise ValueError(
            f"Unsupported exchange: {exchange_name}. "
            f"Supported exchanges: {', '.join(SUPPORTED_EXCHANGES)}"
        )
    
    exchange_class = EXCHANGE_REGISTRY[exchange_name]
    
    # OKX and Bitget require passphrase
    if exchange_name in ['OKX', 'BITGET']:
        if not passphrase:
            logger.warning(f"{exchange_name} requires passphrase for API authentication")
        return exchange_class(api_key, api_secret, passphrase, testnet)
    else:
        return exchange_class(api_key, api_secret, testnet)

def get_supported_exchanges() -> list:
    """
    Get list of supported exchanges
    
    Returns:
        list: List of supported exchange names
    """
    return SUPPORTED_EXCHANGES.copy()

def validate_exchange_name(exchange_name: str) -> bool:
    """
    Validate if exchange name is supported
    
    Args:
        exchange_name: Exchange name to validate
    
    Returns:
        bool: True if supported, False otherwise
    """
    return exchange_name.upper().strip() in EXCHANGE_REGISTRY

def get_exchange_info(exchange_name: str) -> Optional[Dict[str, Any]]:
    """
    Get information about an exchange
    
    Args:
        exchange_name: Exchange name
    
    Returns:
        dict: Exchange information or None if not found
    """
    exchange_name = exchange_name.upper().strip()
    
    if exchange_name not in EXCHANGE_REGISTRY:
        return None
    
    exchange_class = EXCHANGE_REGISTRY[exchange_name]
    
    # Exchange metadata
    exchange_info = {
        'name': exchange_name,
        'class': exchange_class.__name__,
        'requires_passphrase': exchange_name in ['OKX', 'BITGET'],
        'supports_testnet': True,  # All exchanges support testnet/demo
        'features': {
            'market_orders': True,
            'stop_loss': True,
            'take_profit': True,
            'leverage': True,
            'multi_timeframe': True
        }
    }
    
    # Exchange-specific notes
    exchange_notes = {
        'BINANCE': 'Most popular, high liquidity, wide market coverage',
        'BYBIT': 'Popular for derivatives, good API documentation',
        'OKX': 'Requires API passphrase, unified trading account',
        'BITGET': 'Requires API passphrase, copy trading features',
        'HUOBI': 'Contract-based futures (integer quantities)',
        'HTX': 'Rebranded Huobi, contract-based futures',
        'KRAKEN': 'Fixed leverage per contract, regulated in US'
    }
    
    exchange_info['notes'] = exchange_notes.get(exchange_name, '')
    
    return exchange_info

def list_all_exchanges_info() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all supported exchanges
    
    Returns:
        dict: Dictionary mapping exchange names to their information
    """
    return {
        exchange_name: get_exchange_info(exchange_name)
        for exchange_name in SUPPORTED_EXCHANGES
    }


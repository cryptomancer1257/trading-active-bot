#!/usr/bin/env python3
"""
Currency conversion service for PayPal integration
Handles ICP/USD exchange rates with caching
"""

import requests
import redis
import logging
import os
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

class CurrencyService:
    """Service for handling currency conversions and exchange rates"""
    
    def __init__(self):
        # Redis connection for caching
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=redis_db,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis for currency caching")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using fallback without caching.")
            self.redis_client = None
        
        self.cache_ttl = 300  # 5 minutes cache
        self.fallback_rate = Decimal('10.0')  # Fallback ICP/USD rate
    
    def get_icp_usd_rate(self) -> Decimal:
        """
        Get current ICP/USD exchange rate with caching
        Returns rate as Decimal for precision
        """
        cache_key = 'icp_usd_rate'
        
        # Try cache first
        if self.redis_client:
            try:
                cached_rate = self.redis_client.get(cache_key)
                if cached_rate:
                    logger.debug(f"Using cached ICP/USD rate: {cached_rate}")
                    return Decimal(cached_rate)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")
        
        # Fetch from CoinGecko API
        try:
            logger.info("Fetching fresh ICP/USD rate from CoinGecko")
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={
                    'ids': 'internet-computer',
                    'vs_currencies': 'usd'
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            rate = Decimal(str(data['internet-computer']['usd']))
            
            logger.info(f"Retrieved ICP/USD rate: {rate}")
            
            # Cache the rate
            if self.redis_client:
                try:
                    self.redis_client.setex(cache_key, self.cache_ttl, str(rate))
                    logger.debug("Cached ICP/USD rate")
                except Exception as e:
                    logger.warning(f"Redis cache write failed: {e}")
            
            return rate
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch ICP rate from CoinGecko: {e}")
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse ICP rate response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching ICP rate: {e}")
        
        # Return fallback rate
        logger.warning(f"Using fallback ICP/USD rate: {self.fallback_rate}")
        return self.fallback_rate
    
    def icp_to_usd(self, icp_amount: Decimal) -> Decimal:
        """Convert ICP amount to USD"""
        rate = self.get_icp_usd_rate()
        usd_amount = icp_amount * rate
        return usd_amount.quantize(Decimal('0.01'))  # Round to cents
    
    def usd_to_icp(self, usd_amount: Decimal) -> Decimal:
        """Convert USD amount to ICP"""
        rate = self.get_icp_usd_rate()
        icp_amount = usd_amount / rate
        return icp_amount.quantize(Decimal('0.00000001'))  # 8 decimal places
    
    def get_cached_rate_info(self) -> dict:
        """Get information about cached rate"""
        if not self.redis_client:
            return {
                "cached": False,
                "message": "No cache available"
            }
        
        try:
            cache_key = 'icp_usd_rate'
            cached_rate = self.redis_client.get(cache_key)
            ttl = self.redis_client.ttl(cache_key)
            
            if cached_rate:
                return {
                    "cached": True,
                    "rate": Decimal(cached_rate),
                    "expires_in_seconds": ttl,
                    "last_updated": datetime.now() - timedelta(seconds=self.cache_ttl - ttl)
                }
            else:
                return {
                    "cached": False,
                    "message": "No cached rate available"
                }
        except Exception as e:
            return {
                "cached": False,
                "error": str(e)
            }
    
    def invalidate_cache(self):
        """Manually invalidate the currency cache"""
        if self.redis_client:
            try:
                self.redis_client.delete('icp_usd_rate')
                logger.info("Currency cache invalidated")
                return True
            except Exception as e:
                logger.error(f"Failed to invalidate cache: {e}")
                return False
        return False

# Global instance
currency_service = CurrencyService()

def get_currency_service() -> CurrencyService:
    """Get the global currency service instance"""
    return currency_service

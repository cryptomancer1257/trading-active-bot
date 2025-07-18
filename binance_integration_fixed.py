#!/usr/bin/env python3
"""
Fixed Binance integration - manual query string to avoid encoding issues
"""
import requests
import hmac
import hashlib
import time
import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OrderInfo:
    order_id: int
    client_order_id: str
    symbol: str
    side: str
    type: str
    quantity: str
    price: str
    status: str
    executed_qty: str
    executed_price: str = "0"

@dataclass
class BalanceInfo:
    asset: str
    free: str
    locked: str

class BinanceIntegrationFixed:
    """Fixed Binance API integration with manual query string formatting"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # API endpoints
        if testnet:
            self.base_url = "https://testnet.binance.vision"
        else:
            self.base_url = "https://api.binance.com"
        
        logger.info(f"Binance client initialized (testnet={testnet})")
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for query string"""
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"Query string: {query_string}")
        logger.debug(f"Signature: {signature}")
        
        return signature
    
    def _get_server_time(self) -> int:
        """Get Binance server time"""
        try:
            response = requests.get(f"{self.base_url}/api/v3/time", timeout=10)
            server_time = response.json()['serverTime']
            logger.debug(f"Server time: {server_time}")
            return server_time
        except Exception as e:
            logger.warning(f"Failed to get server time: {e}, using local time")
            return int(time.time() * 1000)
    
    def _make_signed_request(self, method: str, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make signed request with manual query string formatting"""
        
        # Add timestamp and recvWindow
        server_time = self._get_server_time()
        params['timestamp'] = server_time
        params['recvWindow'] = 60000
        
        # Create query string manually (exactly as Binance expects)
        sorted_params = sorted(params.items())
        query_string = '&'.join([f"{key}={value}" for key, value in sorted_params])
        
        # Generate signature
        signature = self._generate_signature(query_string)
        
        # Create final query string with signature
        final_query = f"{query_string}&signature={signature}"
        
        # Headers
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Making {method} request to {endpoint}")
            logger.debug(f"Query string: {query_string}")
            logger.debug(f"Signature: {signature[:20]}...")
            
            if method == "GET":
                response = requests.get(f"{url}?{final_query}", headers=headers, timeout=10)
            elif method == "POST":
                # Send as raw data to avoid any encoding
                response = requests.post(url, data=final_query, headers=headers, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, data=final_query, headers=headers, timeout=10)
            
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 400:
                error_data = response.json()
                logger.error(f"Binance API error: {error_data}")
                raise Exception(f"Binance API error: {error_data.get('msg', 'Unknown error')}")
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def test_connectivity(self) -> bool:
        """Test connection to Binance API"""
        try:
            response = requests.get(f"{self.base_url}/api/v3/ping", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return self._make_signed_request("GET", "/api/v3/account", {})
    
    def get_balance(self, asset: str) -> BalanceInfo:
        """Get balance for specific asset"""
        account_info = self.get_account_info()
        
        for balance in account_info.get('balances', []):
            if balance['asset'] == asset:
                return BalanceInfo(
                    asset=balance['asset'],
                    free=balance['free'],
                    locked=balance['locked']
                )
        
        # Return zero balance if asset not found
        return BalanceInfo(asset=asset, free="0.00000000", locked="0.00000000")
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        try:
            response = requests.get(f"{self.base_url}/api/v3/ticker/price", params={'symbol': symbol}, timeout=10)
            data = response.json()
            return float(data['price'])
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> OrderInfo:
        """Create market order with fixed signature"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': quantity
        }
        
        response = self._make_signed_request("POST", "/api/v3/order", params)
        
        return OrderInfo(
            order_id=response['orderId'],
            client_order_id=response['clientOrderId'],
            symbol=response['symbol'],
            side=response['side'],
            type=response['type'],
            quantity=response['origQty'],
            price=response.get('price', '0'),
            status=response['status'],
            executed_qty=response['executedQty']
        )

def test_fixed_implementation():
    """Test the fixed implementation"""
    import sys
    sys.path.append('.')
    
    from database import SessionLocal
    import models, crud
    
    db = SessionLocal()
    
    try:
        # Get credentials
        subscription = db.query(models.Subscription).filter(models.Subscription.id == 34).first()
        credentials = crud.get_user_exchange_credentials(db, subscription.user.id, 'BINANCE', True)
        cred = credentials[0]
        
        print("🔧 Testing Fixed Binance Implementation")
        print("=" * 40)
        
        # Create fixed client
        client = BinanceIntegrationFixed(cred.api_key, cred.api_secret, True)
        
        # Test connectivity
        print("1. Testing connectivity...")
        if client.test_connectivity():
            print("   ✅ Connectivity OK")
        else:
            print("   ❌ Connectivity failed")
            return
        
        # Test account info
        print("2. Testing account info...")
        try:
            account = client.get_account_info()
            print(f"   ✅ Account: {account.get('accountType')}")
            print(f"   ✅ Can Trade: {account.get('canTrade')}")
        except Exception as e:
            print(f"   ❌ Account info failed: {e}")
            return
        
        # Test balance
        print("3. Testing balance...")
        try:
            btc_balance = client.get_balance("BTC")
            usdt_balance = client.get_balance("USDT")
            print(f"   ✅ BTC: {btc_balance.free}")
            print(f"   ✅ USDT: {usdt_balance.free}")
        except Exception as e:
            print(f"   ❌ Balance failed: {e}")
            return
        
        # Test small order
        print("4. Testing small market order...")
        try:
            order = client.create_market_order("BTCUSDT", "SELL", "0.001")
            print(f"   ✅ Order successful!")
            print(f"   Order ID: {order.order_id}")
            print(f"   Status: {order.status}")
            print(f"   Executed: {order.executed_qty}")
        except Exception as e:
            error_msg = str(e)
            if "1022" in error_msg:
                print(f"   ❌ Still signature error: {e}")
            elif "2010" in error_msg:
                print("   ✅ Signature OK! Insufficient balance (expected)")
            elif "1013" in error_msg:
                print("   ✅ Signature OK! Quantity too small (expected)")
            else:
                print(f"   ❌ Other error: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_fixed_implementation() 
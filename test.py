import requests
import time
import hashlib
import hmac
import json
from decimal import Decimal, ROUND_DOWN

class BinanceTestnetClient:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://testnet.binance.vision"
        self.headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def _generate_signature(self, params):
        """Tạo chữ ký HMAC SHA256"""
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_server_time(self):
        """Lấy thời gian server Binance"""
        endpoint = "/api/v3/time"
        response = requests.get(f"{self.base_url}{endpoint}")
        
        if response.status_code == 200:
            return response.json()['serverTime']
        else:
            return int(time.time() * 1000)
    
    def get_account_info(self):
        """Lấy thông tin tài khoản"""
        endpoint = "/api/v3/account"
        timestamp = self.get_server_time()
        
        params = {
            'timestamp': timestamp,
            'recvWindow': 60000  # Tăng recv window lên 60 giây
        }
        
        params['signature'] = self._generate_signature(params)
        
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error getting account info: {response.text}")
    
    def get_symbol_info(self, symbol):
        """Lấy thông tin symbol"""
        endpoint = "/api/v3/exchangeInfo"
        response = requests.get(f"{self.base_url}{endpoint}")
        
        if response.status_code == 200:
            data = response.json()
            for s in data['symbols']:
                if s['symbol'] == symbol:
                    return s
        return None
    
    def get_current_price(self, symbol):
        """Lấy giá hiện tại"""
        endpoint = "/api/v3/ticker/price"
        params = {'symbol': symbol}
        
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        
        if response.status_code == 200:
            return float(response.json()['price'])
        else:
            raise Exception(f"Error getting price: {response.text}")
    
    def place_sell_order(self, symbol, quantity, order_type='MARKET'):
        """Đặt lệnh sell"""
        endpoint = "/api/v3/order"
        timestamp = self.get_server_time()
        
        params = {
            'symbol': symbol,
            'side': 'SELL',
            'type': order_type,
            'quantity': quantity,
            'timestamp': timestamp,
            'recvWindow': 60000
        }
        
        params['signature'] = self._generate_signature(params)
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            data=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error placing sell order: {response.text}")
    
    def calculate_sell_quantity(self, symbol, percentage=0.5):
        """Tính toán số lượng BTC cần sell (0.5% portfolio)"""
        # Lấy thông tin tài khoản
        account_info = self.get_account_info()
        
        # Tìm số dư BTC
        btc_balance = 0
        for balance in account_info['balances']:
            if balance['asset'] == 'BTC':
                btc_balance = float(balance['free'])
                break
        
        if btc_balance == 0:
            raise Exception("Không có BTC trong tài khoản")
        
        # Tính 0.5% của số dư BTC
        sell_quantity = btc_balance * (percentage / 100)
        
        # Lấy thông tin symbol để làm tròn theo quy định
        symbol_info = self.get_symbol_info(symbol)
        if symbol_info:
            # Tìm LOT_SIZE filter
            for filter_info in symbol_info['filters']:
                if filter_info['filterType'] == 'LOT_SIZE':
                    step_size = float(filter_info['stepSize'])
                    # Làm tròn xuống theo stepSize
                    decimal_places = len(str(step_size).split('.')[-1])
                    sell_quantity = float(Decimal(str(sell_quantity)).quantize(
                        Decimal(str(step_size)), rounding=ROUND_DOWN
                    ))
                    break
        
        return sell_quantity

def main():
    # Thay thế bằng API key và secret key thực tế của bạn
    API_KEY = "cNHNwLgLqjgQmPjhjNnXdyKxewfqmVJlUlbZDrIAWiO12mSbFz41G1gVqsAHMPgI"
    SECRET_KEY = "qiGvfQR12aIGgxgqZkgLn7vipbwWVPaBkQUlqzyxX4EPP52AuvBajUacGz4Osigb"
    
    # Khởi tạo client
    client = BinanceTestnetClient(API_KEY, SECRET_KEY)
    
    try:
        print("=== BINANCE TESTNET SELL ORDER ===")
        
        # Symbol trading pair
        symbol = "BTCUSDT"
        
        # Kiểm tra server time
        print("\n0. Kiểm tra đồng bộ thời gian...")
        server_time = client.get_server_time()
        local_time = int(time.time() * 1000)
        time_diff = abs(server_time - local_time)
        print(f"Server time: {server_time}")
        print(f"Local time: {local_time}")
        print(f"Time difference: {time_diff}ms")
        
        if time_diff > 30000:  # 30 giây
            print("⚠️  Cảnh báo: Thời gian hệ thống có thể không đồng bộ!")
        
        # Lấy thông tin tài khoản
        print("\n1. Lấy thông tin tài khoản...")
        account_info = client.get_account_info()
        print(f"Account Type: {account_info.get('accountType', 'N/A')}")
        
        # Hiển thị số dư BTC
        for balance in account_info['balances']:
            if balance['asset'] == 'BTC' and float(balance['free']) > 0:
                print(f"BTC Balance: {balance['free']}")
                break
        
        # Lấy giá hiện tại
        print(f"\n2. Lấy giá hiện tại {symbol}...")
        current_price = client.get_current_price(symbol)
        print(f"Current Price: ${current_price:,.2f}")
        
        # Tính toán số lượng cần sell (0.5% portfolio)
        print(f"\n3. Tính toán số lượng cần sell (0.5% portfolio)...")
        sell_quantity = client.calculate_sell_quantity(symbol, 0.5)
        print(f"Sell Quantity: {sell_quantity} BTC")
        print(f"Estimated Value: ${sell_quantity * current_price:,.2f}")
        
        # Xác nhận trước khi đặt lệnh
        confirm = input(f"\nBạn có chắc chắn muốn sell {sell_quantity} BTC? (y/n): ")
        
        if confirm.lower() == 'y':
            print(f"\n4. Đặt lệnh sell...")
            
            # Đặt lệnh sell market
            order_result = client.place_sell_order(symbol, sell_quantity, 'MARKET')
            
            print("✅ Lệnh sell đã được thực hiện thành công!")
            print(f"Order ID: {order_result.get('orderId')}")
            print(f"Symbol: {order_result.get('symbol')}")
            print(f"Side: {order_result.get('side')}")
            print(f"Type: {order_result.get('type')}")
            print(f"Quantity: {order_result.get('origQty')}")
            print(f"Status: {order_result.get('status')}")
            
            # Hiển thị fills nếu có
            if 'fills' in order_result and order_result['fills']:
                print("\nFill Details:")
                for fill in order_result['fills']:
                    print(f"  Price: ${float(fill['price']):,.2f}")
                    print(f"  Quantity: {fill['qty']}")
                    print(f"  Commission: {fill['commission']} {fill['commissionAsset']}")
        else:
            print("❌ Hủy lệnh sell")
            
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        
        # Gợi ý sửa lỗi
        if "Timestamp for this request is outside of the recvWindow" in str(e):
            print("\n🔧 Gợi ý sửa lỗi:")
            print("1. Đồng bộ thời gian hệ thống với internet")
            print("2. Kiểm tra timezone của máy tính")
            print("3. Thử khởi động lại script")
        elif "Invalid API-key" in str(e):
            print("\n🔧 Gợi ý sửa lỗi:")
            print("1. Kiểm tra API key và secret key")
            print("2. Đảm bảo sử dụng testnet keys")
            print("3. Kiểm tra quyền của API key")

if __name__ == "__main__":
    main()
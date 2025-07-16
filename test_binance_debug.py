#!/usr/bin/env python3
"""
Binance API Debug Tool
Giúp debug vấn đề kết nối Binance API
"""

import sys
import logging
from binance_integration import BinanceIntegration

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_binance_api(api_key: str, api_secret: str, testnet: bool = True):
    """Test Binance API với debugging chi tiết"""
    
    print(f"\n{'='*60}")
    print(f"🔍 BINANCE API DEBUG TOOL")
    print(f"{'='*60}")
    print(f"📍 Environment: {'TESTNET' if testnet else 'MAINNET'}")
    print(f"🔑 API Key Length: {len(api_key)} characters")
    print(f"🔐 API Secret Length: {len(api_secret)} characters")
    print(f"{'='*60}\n")
    
    try:
        # Tạo client
        client = BinanceIntegration(api_key, api_secret, testnet)
        print(f"✅ Created Binance client successfully")
        print(f"🌐 Base URL: {client.base_url}")
        
        # Test 1: Basic connectivity
        print(f"\n📡 STEP 1: Testing basic connectivity...")
        try:
            connectivity = client.test_connectivity()
            if connectivity:
                print(f"✅ Connectivity test: PASSED")
            else:
                print(f"❌ Connectivity test: FAILED")
                return False
        except Exception as e:
            print(f"❌ Connectivity test: ERROR - {e}")
            return False
        
        # Test 2: Server time
        print(f"\n⏰ STEP 2: Getting server time...")
        try:
            server_time = client._get_server_time()
            import time
            local_time = int(time.time() * 1000)
            time_diff = abs(server_time - local_time)
            
            print(f"✅ Server time: {server_time}")
            print(f"⏰ Local time: {local_time}")
            print(f"⏱️  Time difference: {time_diff}ms")
            
            if time_diff > 5000:  # 5 seconds
                print(f"⚠️  WARNING: Time difference > 5 seconds. This may cause API issues!")
        except Exception as e:
            print(f"❌ Server time test: ERROR - {e}")
        
        # Test 3: Account access
        print(f"\n👤 STEP 3: Testing account access...")
        try:
            account_info = client.get_account_info()
            print(f"✅ Account access: SUCCESSFUL")
            print(f"📊 Account Type: {account_info.get('accountType', 'UNKNOWN')}")
            print(f"💰 Can Trade: {account_info.get('canTrade', False)}")
            print(f"📤 Can Withdraw: {account_info.get('canWithdraw', False)}")
            print(f"📥 Can Deposit: {account_info.get('canDeposit', False)}")
            print(f"🔐 Permissions: {account_info.get('permissions', [])}")
            
            # Count non-zero balances
            balances = account_info.get('balances', [])
            non_zero_balances = [b for b in balances if float(b.get('free', 0)) > 0 or float(b.get('locked', 0)) > 0]
            print(f"💳 Total assets: {len(balances)}")
            print(f"💰 Non-zero balances: {len(non_zero_balances)}")
            
            # Show some balances
            if non_zero_balances:
                print(f"\n💰 Sample balances:")
                for balance in non_zero_balances[:5]:  # Show first 5
                    free = float(balance.get('free', 0))
                    locked = float(balance.get('locked', 0))
                    if free > 0 or locked > 0:
                        print(f"   {balance['asset']}: Free={free}, Locked={locked}")
            
            return True
            
        except Exception as e:
            print(f"❌ Account access: ERROR - {e}")
            print(f"🔍 Error details: {type(e).__name__}: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to create Binance client: {e}")
        return False

def main():
    print("🚀 Binance API Debug Tool")
    print("Nhập thông tin API key và secret để test:")
    
    # Lấy thông tin từ user
    api_key = input("\n🔑 API Key: ").strip()
    api_secret = input("🔐 API Secret: ").strip()
    
    testnet_choice = input("🌐 Use testnet? (y/n, default=y): ").strip().lower()
    testnet = testnet_choice != 'n'
    
    if not api_key or not api_secret:
        print("❌ API Key và Secret không được để trống!")
        return
    
    # Chạy test
    success = test_binance_api(api_key, api_secret, testnet)
    
    print(f"\n{'='*60}")
    if success:
        print(f"🎉 TỔNG KẾT: API credentials hợp lệ!")
    else:
        print(f"❌ TỔNG KẾT: API credentials có vấn đề!")
        print(f"\n💡 GỢI Ý KHẮC PHỤC:")
        print(f"1. Kiểm tra API Key và Secret có đúng không")
        print(f"2. Đảm bảo API Key có quyền 'Spot & Margin Trading'")
        print(f"3. Kiểm tra IP whitelist (nếu có)")
        print(f"4. Thử tạo API key mới trên Binance testnet")
        print(f"5. Kiểm tra thời gian hệ thống có chính xác không")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 
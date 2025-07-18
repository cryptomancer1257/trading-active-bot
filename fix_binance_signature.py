#!/usr/bin/env python3
"""
Quick fix script for Binance signature errors
"""
import os
import sys
import requests
import time
import hmac
import hashlib

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_binance_signature_issues():
    """Fix common Binance signature issues"""
    print("🔧 Binance Signature Quick Fix")
    print("=" * 40)
    
    from database import SessionLocal
    import models
    import crud
    import schemas
    
    db = SessionLocal()
    
    try:
        # Find subscriptions with recent signature errors
        print("🔍 Looking for failed subscriptions...")
        
        failed_actions = db.query(models.BotAction).filter(
            models.BotAction.action == "ERROR",
            models.BotAction.description.like("%Signature%")
        ).order_by(models.BotAction.created_at.desc()).limit(5).all()
        
        if not failed_actions:
            print("✅ No recent signature errors found")
            return
            
        print(f"Found {len(failed_actions)} recent signature errors")
        
        # Get unique subscription IDs
        subscription_ids = list(set([action.subscription_id for action in failed_actions]))
        
        for sub_id in subscription_ids:
            print(f"\n🔄 Processing subscription {sub_id}...")
            
            subscription = crud.get_subscription_by_id(db, sub_id)
            if not subscription:
                continue
                
            # Get exchange credentials
            use_testnet = getattr(subscription, 'is_testnet', True)
            exchange_type = subscription.exchange_type or schemas.ExchangeType.BINANCE
            
            credentials = crud.get_user_exchange_credentials(
                db, 
                user_id=subscription.user.id, 
                exchange=exchange_type.value,
                is_testnet=use_testnet
            )
            
            if not credentials:
                print(f"❌ No credentials found for subscription {sub_id}")
                continue
                
            cred = credentials[0]
            
            # Test current credentials
            print(f"🧪 Testing credentials for {subscription.user.email}...")
            
            try:
                # Simple test call
                base_url = "https://testnet.binance.vision" if use_testnet else "https://api.binance.com"
                
                # Get server time
                time_response = requests.get(f"{base_url}/api/v3/time", timeout=10)
                server_time = time_response.json()['serverTime']
                
                # Create signature for account info
                params = {'timestamp': server_time}
                query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
                
                signature = hmac.new(
                    cred.api_secret.encode('utf-8'),
                    query_string.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                params['signature'] = signature
                
                # Test account info call
                headers = {'X-MBX-APIKEY': cred.api_key}
                response = requests.get(
                    f"{base_url}/api/v3/account",
                    params=params,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    account_data = response.json()
                    print(f"✅ Credentials working! Account: {account_data.get('accountType', 'Unknown')}")
                    
                    # Update validation status
                    crud.update_credentials_validation(db, cred.id, True, "Fixed and validated")
                    
                    # Log successful fix
                    crud.log_bot_action(
                        db, sub_id, "INFO",
                        "🔧 Signature issue resolved - credentials validated successfully"
                    )
                    
                else:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                    error_msg = error_data.get('msg', 'Unknown error')
                    print(f"❌ Credentials failed: {error_msg}")
                    
                    # Update validation status
                    crud.update_credentials_validation(db, cred.id, False, f"Validation failed: {error_msg}")
                    
                    # Provide specific fix suggestions
                    if "1022" in str(response.status_code) or "signature" in error_msg.lower():
                        print("🔧 SIGNATURE ERROR - RECOMMENDED ACTIONS:")
                        print("   1. Recreate API keys in Binance")
                        print("   2. Check system time sync")
                        print("   3. Verify API key permissions")
                        print("   4. Remove IP restrictions")
                        
                        # Log suggested actions
                        crud.log_bot_action(
                            db, sub_id, "ERROR",
                            f"🚨 Signature validation failed. Suggestions: 1) Recreate API keys, 2) Sync time, 3) Check permissions. Error: {error_msg}"
                        )
                    
            except Exception as e:
                print(f"❌ Test failed: {e}")
                crud.log_bot_action(
                    db, sub_id, "ERROR",
                    f"🔧 Signature fix attempt failed: {str(e)}"
                )
        
        print("\n" + "=" * 40)
        print("🎯 SUMMARY:")
        print("If issues persist:")
        print("1. 🔄 Recreate API keys in Binance with trading permissions")
        print("2. ⏰ Sync system time: w32tm /resync (Windows) or ntpdate (Linux)")
        print("3. 🌐 Remove IP restrictions from API keys")  
        print("4. 🧪 Verify testnet vs live endpoint settings")
        print("5. 📧 Contact support if problems continue")
        
    except Exception as e:
        print(f"❌ Fix script error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    fix_binance_signature_issues() 
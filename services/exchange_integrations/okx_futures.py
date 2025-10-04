"""
OKX Futures Exchange Integration
"""

import hashlib
import hmac
import time
import base64
import requests
import pandas as pd
import logging
from typing import Dict, Any, List
from datetime import datetime

from .base_futures_exchange import BaseFuturesExchange, FuturesOrderInfo, FuturesPosition

logger = logging.getLogger(__name__)

class OKXFuturesIntegration(BaseFuturesExchange):
    """OKX Futures API Integration (V5 API)"""
    
    @property
    def exchange_name(self) -> str:
        return "OKX"
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str = "", testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        self.passphrase = passphrase  # OKX requires passphrase
        
        # OKX API endpoints (same for testnet and mainnet)
        self.base_url = "https://www.okx.com"
        
        # Logging
        mode = "🧪 DEMO TRADING" if testnet else "🔴 LIVE"
        logger.info(f"🔧 Initializing OKX Futures Integration - {mode}")
        logger.info(f"   API Key: {api_key[:8]}***")
        logger.info(f"   Passphrase: {'✅ Provided' if passphrase else '❌ MISSING'}")
        
        if not passphrase:
            logger.warning("⚠️ OKX REQUIRES PASSPHRASE! Authentication will fail without it.")
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Generate OKX signature"""
        message = timestamp + method + request_path + body
        mac = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(mac.digest()).decode()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False):
        """Make authenticated request to OKX API"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        
        # Check if this is a public endpoint (market data)
        is_public_endpoint = endpoint.startswith('/api/v5/market/') or endpoint.startswith('/api/v5/public/')
        
        # OKX requires ISO8601 timestamp in specific format
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Only add auth headers for authenticated endpoints
        if not is_public_endpoint:
            headers["OK-ACCESS-KEY"] = self.api_key
            headers["OK-ACCESS-TIMESTAMP"] = timestamp
            headers["OK-ACCESS-PASSPHRASE"] = self.passphrase
            
            # Demo trading flag for testnet (only for private endpoints)
            if self.testnet:
                headers["x-simulated-trading"] = "1"
        
        body = ""
        if signed:
            if method == "POST":
                import json
                body = json.dumps(params) if params else ""
            else:
                body = ""
            
            request_path = endpoint
            if method == "GET" and params:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                request_path = f"{endpoint}?{query_string}"
            
            signature = self._generate_signature(timestamp, method, request_path, body)
            headers["OK-ACCESS-SIGN"] = signature
        
        # Debug logging
        if is_public_endpoint:
            logger.info(f"🌐 OKX PUBLIC API Request: {method} {endpoint}")
        else:
            mode = "DEMO TRADING" if self.testnet else "LIVE"
            logger.info(f"🔑 OKX {mode} API Request: {method} {endpoint}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Log response for debugging
            logger.info(f"📥 OKX Response Status: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != '0':
                error_msg = data.get('msg', 'Unknown error')
                error_code = data.get('code')
                
                # OKX often returns detailed error in 'data' field
                detailed_errors = data.get('data', [])
                
                logger.error(f"❌ OKX API Error [{error_code}]: {error_msg}")
                
                # Log detailed error messages if available
                if detailed_errors and isinstance(detailed_errors, list) and len(detailed_errors) > 0:
                    for i, err_detail in enumerate(detailed_errors, 1):
                        if isinstance(err_detail, dict):
                            sub_code = err_detail.get('sCode', 'N/A')
                            sub_msg = err_detail.get('sMsg', 'N/A')
                            logger.error(f"   └─ Error #{i}: [{sub_code}] {sub_msg}")
                            # Build comprehensive error message
                            error_msg = f"{error_msg} | Detail: [{sub_code}] {sub_msg}"
                
                # Log full response for debugging
                logger.error(f"   Full response: {data}")
                
                raise Exception(f"OKX API error [{error_code}]: {error_msg}")
            
            logger.info(f"✅ OKX API Success: {method} {endpoint}")
            return data.get('data', [])
            
        except requests.exceptions.HTTPError as e:
            # Log response body for 401 errors
            try:
                error_body = e.response.json()
                logger.error(f"❌ OKX HTTP {e.response.status_code}: {error_body}")
            except:
                logger.error(f"❌ OKX HTTP {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ OKX API request failed: {e}")
            raise
    
    def test_connectivity(self) -> bool:
        """Test OKX API connectivity"""
        try:
            response = requests.get(f"{self.base_url}/api/v5/public/time", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OKX connectivity test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get OKX account information with detailed margin breakdown
        
        Returns:
            - totalWalletBalance: Total equity
            - availableBalance: Available for trading (CRITICAL!)
            - usedMargin: Margin locked in positions
            - unrealizedPnl: Unrealized profit/loss
        """
        try:
            result = self._make_request("GET", "/api/v5/account/balance", signed=True)
            
            if result and len(result) > 0:
                account = result[0]
                
                # OKX balance fields:
                total_equity = float(account.get('totalEq', 0))  # Total equity
                
                # Get USDT detail for available balance
                details = account.get('details', [])
                usdt_detail = next((d for d in details if d.get('ccy') == 'USDT'), {})
                
                available_balance = float(usdt_detail.get('availBal', 0))  # Available for trading!
                equity = float(usdt_detail.get('eq', 0))  # Equity in USDT
                frozen = float(usdt_detail.get('frozenBal', 0))  # Frozen balance
                
                # Calculate used margin
                used_margin = equity - available_balance
                
                logger.info(f"💰 OKX Account Breakdown:")
                logger.info(f"   Total Equity: ${total_equity:,.2f}")
                logger.info(f"   USDT Equity: ${equity:,.2f}")
                logger.info(f"   Available (for trading): ${available_balance:,.2f}")
                logger.info(f"   Used Margin: ${used_margin:,.2f}")
                logger.info(f"   Frozen: ${frozen:,.2f}")
                
                return {
                    'totalWalletBalance': total_equity,
                    'availableBalance': available_balance,  # CORRECT available balance!
                    'usedMargin': used_margin,
                    'frozen': frozen,
                    'raw_response': result
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get OKX account info: {e}")
            raise
    
    def get_position_info(self, symbol: str = None) -> List[FuturesPosition]:
        """
        Get OKX position information with detailed margin usage
        """
        try:
            params = {'instType': 'SWAP'}
            if symbol:
                params['instId'] = self._to_okx_symbol(symbol)
            
            result = self._make_request("GET", "/api/v5/account/positions", params, signed=True)
            
            positions = []
            logger.info(f"📊 OKX Positions ({len(result)} total):")
            
            for pos in result:
                size = float(pos.get('pos', 0))
                if size != 0:
                    symbol_clean = self._from_okx_symbol(pos['instId'])
                    pos_side = "LONG" if pos['posSide'] == 'long' else "SHORT"
                    entry_price = float(pos.get('avgPx', 0))
                    mark_price = float(pos.get('markPx', 0))
                    upl = float(pos.get('upl', 0))
                    upl_ratio = float(pos.get('uplRatio', 0)) * 100
                    margin = float(pos.get('margin', 0))  # Margin used by this position
                    leverage = float(pos.get('lever', 1))
                    
                    logger.info(f"   ├─ {symbol_clean} {pos_side}")
                    logger.info(f"   │  Size: {abs(size)} contracts")
                    logger.info(f"   │  Entry: ${entry_price:,.2f} | Mark: ${mark_price:,.2f}")
                    logger.info(f"   │  P&L: ${upl:,.2f} ({upl_ratio:+.2f}%)")
                    logger.info(f"   │  Margin Used: ${margin:,.2f} (Leverage: {leverage}x)")
                    
                    positions.append(FuturesPosition(
                        symbol=symbol_clean,
                        side=pos_side,
                        size=str(abs(size)),
                        entry_price=str(entry_price),
                        mark_price=str(mark_price),
                        pnl=str(upl),
                        percentage=str(upl_ratio)
                    ))
            
            if not positions:
                logger.info("   └─ No open positions")
            
            return positions
        except Exception as e:
            logger.error(f"Failed to get OKX position info: {e}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for symbol"""
        try:
            params = {'instId': self._to_okx_symbol(symbol)}
            result = self._make_request("GET", "/api/v5/market/ticker", params)
            
            if result and len(result) > 0:
                return {
                    'symbol': symbol,
                    'price': result[0]['last']
                }
            raise Exception(f"No ticker data for {symbol}")
        except Exception as e:
            logger.error(f"Failed to get ticker: {e}")
            raise
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for symbol
        
        Note: In long_short_mode, leverage must be set separately for long and short positions
        This method sets leverage for BOTH directions
        """
        try:
            okx_symbol = self._to_okx_symbol(symbol)
            
            # Set leverage for LONG positions
            params_long = {
                'instId': okx_symbol,
                'lever': str(leverage),
                'mgnMode': 'cross',
                'posSide': 'long'
            }
            
            # Set leverage for SHORT positions
            params_short = {
                'instId': okx_symbol,
                'lever': str(leverage),
                'mgnMode': 'cross',
                'posSide': 'short'
            }
            
            logger.info(f"🔧 Setting leverage {leverage}x for {symbol} (both long and short)")
            
            # Set for long
            try:
                self._make_request("POST", "/api/v5/account/set-leverage", params_long, signed=True)
                logger.info(f"✅ Leverage {leverage}x set for LONG positions")
            except Exception as e:
                if 'leverage not modified' not in str(e).lower():
                    logger.warning(f"⚠️ Failed to set leverage for LONG: {e}")
            
            # Set for short
            try:
                self._make_request("POST", "/api/v5/account/set-leverage", params_short, signed=True)
                logger.info(f"✅ Leverage {leverage}x set for SHORT positions")
            except Exception as e:
                if 'leverage not modified' not in str(e).lower():
                    logger.warning(f"⚠️ Failed to set leverage for SHORT: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            return False
    
    def set_position_mode(self, mode: str = 'net_mode') -> bool:
        """
        Set position mode for OKX account
        
        Args:
            mode: 'long_short_mode' or 'net_mode'
                - long_short_mode: Can hold both long and short positions separately
                - net_mode: Single position (default for most users)
        """
        try:
            params = {
                'posMode': mode
            }
            logger.info(f"🔧 Setting OKX position mode to: {mode}")
            self._make_request("POST", "/api/v5/account/set-position-mode", params, signed=True)
            logger.info(f"✅ Position mode set to {mode}")
            return True
        except Exception as e:
            error_msg = str(e)
            # If already in the correct mode, that's okay
            if 'Position mode is already set' in error_msg or '59000' in error_msg:
                logger.info(f"✅ Position mode already set to {mode}")
                return True
            logger.warning(f"⚠️ Failed to set position mode: {e}")
            return False
    
    def check_account_config(self) -> Dict[str, Any]:
        """
        Check OKX account configuration
        Returns position mode, account mode, and other settings
        """
        try:
            result = self._make_request("GET", "/api/v5/account/config", signed=True)
            
            if result and len(result) > 0:
                config = result[0]
                
                logger.info(f"📋 OKX Account Configuration:")
                logger.info(f"   Position Mode: {config.get('posMode', 'N/A')}")
                logger.info(f"   Account Level: {config.get('acctLv', 'N/A')}")
                logger.info(f"   Auto Loan: {config.get('autoLoan', 'N/A')}")
                
                return config
            
            return {}
        except Exception as e:
            logger.error(f"Failed to check account config: {e}")
            return {}
    
    def get_symbol_precision(self, symbol: str) -> dict:
        """
        Get symbol precision and contract info
        
        OKX Futures uses CONTRACT-based quantity:
        - ctVal: Contract value (how much crypto per contract)
        - lotSz: Minimum order size in contracts
        
        Example ETH-USDT-SWAP:
        - ctVal = 0.01 (1 contract = 0.01 ETH)
        - To trade 4.218 ETH → 4.218 / 0.01 = 421.8 → 422 contracts
        """
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        
        try:
            params = {'instType': 'SWAP', 'instId': self._to_okx_symbol(symbol)}
            result = self._make_request("GET", "/api/v5/public/instruments", params)
            
            if result and len(result) > 0:
                info = result[0]
                
                # OKX contract info
                ct_val = float(info.get('ctVal', '0.01'))  # Contract value (crypto per contract)
                lot_sz = float(info.get('lotSz', '1'))     # Minimum lot size
                tick_sz = float(info.get('tickSz', '0.01'))  # Price tick size
                
                precision_info = {
                    'quantityPrecision': 0,  # Contracts are integers
                    'pricePrecision': len(str(tick_sz).split('.')[-1]) if '.' in str(tick_sz) else 0,
                    'stepSize': str(lot_sz),
                    'tickSize': str(tick_sz),
                    'contractValue': ct_val,  # NEW: How much crypto per contract
                    'minSize': lot_sz  # Minimum order size in contracts
                }
                
                logger.info(f"📐 {symbol} precision info:")
                logger.info(f"   Contract Value: {ct_val} (crypto per contract)")
                logger.info(f"   Lot Size: {lot_sz} contracts")
                logger.info(f"   Tick Size: {tick_sz}")
                
                self._symbol_info_cache[symbol] = precision_info
                return precision_info
            
            # Default fallback
            return {
                'quantityPrecision': 0, 
                'pricePrecision': 2, 
                'stepSize': '1', 
                'tickSize': '0.01',
                'contractValue': 0.01,
                'minSize': 1
            }
        except Exception as e:
            logger.error(f"Failed to get symbol precision: {e}")
            return {
                'quantityPrecision': 0, 
                'pricePrecision': 2, 
                'stepSize': '1', 
                'tickSize': '0.01',
                'contractValue': 0.01,
                'minSize': 1
            }
    
    def quantity_to_contracts(self, quantity: float, symbol: str) -> float:
        """
        Convert crypto quantity to OKX contracts
        
        Example for ETH-USDT-SWAP:
        - quantity: 4.218 ETH
        - contractValue: 0.1 ETH per contract
        - Result: 4.218 / 0.1 = 42.18 contracts
        - Lot size: 0.01 → Rounded to 42.18 contracts ✅
        
        Note: OKX allows fractional contracts based on lot size!
        Uses Decimal to avoid floating point precision errors.
        """
        from decimal import Decimal, ROUND_DOWN
        
        precision_info = self.get_symbol_precision(symbol)
        contract_value = precision_info.get('contractValue', 0.01)
        lot_size = float(precision_info.get('stepSize', '1'))
        
        # Use Decimal for precise arithmetic (avoid floating point errors)
        qty_decimal = Decimal(str(quantity))
        ct_val_decimal = Decimal(str(contract_value))
        lot_size_decimal = Decimal(str(lot_size))
        
        # Convert crypto amount to contracts
        contracts_decimal = qty_decimal / ct_val_decimal
        
        # Round to nearest lot size using Decimal precision
        # E.g. lot_size=0.01 → Can trade 42.18, 42.19, 42.20 contracts
        contracts_decimal = (contracts_decimal / lot_size_decimal).quantize(Decimal('1'), rounding=ROUND_DOWN) * lot_size_decimal
        
        # Convert back to float for return
        contracts = float(contracts_decimal)
        
        logger.info(f"🔢 Quantity conversion: {quantity} crypto → {contracts} contracts (ctVal={contract_value}, lotSz={lot_size})")
        
        return contracts
    
    def round_quantity(self, quantity: float, symbol: str) -> str:
        """
        Round quantity to proper precision (converts to contracts for OKX)
        """
        contracts = self.quantity_to_contracts(quantity, symbol)
        return str(contracts)
    
    def create_market_order(self, symbol: str, side: str, quantity: str) -> FuturesOrderInfo:
        """
        Create OKX market order
        
        Note: OKX requires quantity in CONTRACTS (integers), not crypto amount!
        This method automatically converts crypto quantity to contracts.
        
        Position Side Logic:
        - BUY → posSide='long' (opening long position)
        - SELL → posSide='short' (opening short position)
        """
        try:
            okx_symbol = self._to_okx_symbol(symbol)
            okx_side = 'buy' if side == 'BUY' else 'sell'
            
            # Convert crypto quantity to contracts (OKX requirement)
            quantity_float = float(quantity)
            contracts = self.quantity_to_contracts(quantity_float, symbol)
            
            # Determine position side (long/short mode requirement)
            # When OPENING a position: BUY → long, SELL → short
            pos_side = 'long' if side == 'BUY' else 'short'
            
            # Format contracts string without floating point errors
            # Use Decimal to ensure clean output (e.g. '42.18' not '42.180000000000004')
            from decimal import Decimal
            contracts_str = str(Decimal(str(contracts)).normalize())
            
            params = {
                'instId': okx_symbol,
                'tdMode': 'cross',
                'side': okx_side,
                'posSide': pos_side,  # Required for long_short_mode accounts
                'ordType': 'market',
                'sz': contracts_str  # Clean string (no floating point errors)
            }
            
            logger.info(f"📤 Creating OKX market order:")
            logger.info(f"   Symbol: {symbol} → {okx_symbol}")
            logger.info(f"   Side: {side} → {okx_side}")
            logger.info(f"   Position Side: {pos_side}")
            logger.info(f"   Quantity: {quantity} crypto → {contracts} contracts")
            logger.info(f"   Trade Mode: cross")
            logger.info(f"   Full params: {params}")
            
            result = self._make_request("POST", "/api/v5/trade/order", params, signed=True)
            
            if result and len(result) > 0:
                order = result[0]
                
                # Log full order response for debugging
                logger.info(f"📦 OKX Order Response: {order}")
                
                order_id = order.get('ordId', '')
                s_code = order.get('sCode', '')
                s_msg = order.get('sMsg', '')
                
                # OKX sCode meanings:
                # '0' = Success
                # Other codes = Error
                if s_code == '0':
                    logger.info(f"✅ Order placed successfully! Order ID: {order_id}")
                    status = 'NEW'  # Order accepted
                else:
                    logger.error(f"❌ Order failed: [{s_code}] {s_msg}")
                    raise Exception(f"OKX order error [{s_code}]: {s_msg}")
                
                return FuturesOrderInfo(
                    order_id=order_id,
                    client_order_id=order.get('clOrdId', ''),
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=str(contracts),  # Use actual contracts
                    price='0',
                    status=status,
                    executed_qty='0'
                )
            raise Exception("Failed to create order - empty response")
        except Exception as e:
            logger.error(f"Failed to create market order: {e}")
            raise
    
    def create_stop_loss_order(self, symbol: str, side: str, quantity: str, 
                              stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
        """
        Create stop loss order (OKX requires contracts, not crypto amount)
        
        Note: 'side' is the CLOSING side
        - If side='SELL' → Closing a LONG position → posSide='long'
        - If side='BUY' → Closing a SHORT position → posSide='short'
        """
        try:
            # Convert crypto quantity to contracts
            quantity_float = float(quantity)
            contracts = self.quantity_to_contracts(quantity_float, symbol)
            
            okx_side = 'buy' if side == 'BUY' else 'sell'
            # Position side is OPPOSITE of closing side
            pos_side = 'short' if side == 'BUY' else 'long'
            
            # Format contracts string without floating point errors
            from decimal import Decimal
            contracts_str = str(Decimal(str(contracts)).normalize())
            
            params = {
                'instId': self._to_okx_symbol(symbol),
                'tdMode': 'cross',
                'side': okx_side,
                'posSide': pos_side,  # Required for long_short_mode
                'ordType': 'conditional',
                'sz': contracts_str,  # Clean string (no floating point errors)
                'slTriggerPx': stop_price,
                'slOrdPx': '-1',  # Market price
                'reduceOnly': reduce_only
            }
            
            logger.info(f"🛑 Creating SL order: {quantity} crypto → {contracts} contracts @ ${stop_price} (posSide={pos_side})")
            
            result = self._make_request("POST", "/api/v5/trade/order-algo", params, signed=True)
            
            if result and len(result) > 0:
                order = result[0]
                
                algo_id = order.get('algoId', '')
                s_code = order.get('sCode', '')
                s_msg = order.get('sMsg', '')
                
                if s_code == '0':
                    logger.info(f"✅ SL order placed! Algo ID: {algo_id}")
                    status = 'NEW'
                else:
                    logger.error(f"❌ SL order failed: [{s_code}] {s_msg}")
                    raise Exception(f"OKX SL order error [{s_code}]: {s_msg}")
                
                return FuturesOrderInfo(
                    order_id=algo_id,
                    client_order_id=order.get('clOrdId', ''),
                    symbol=symbol,
                    side=side,
                    type='STOP_MARKET',
                    quantity=str(contracts),
                    price=stop_price,
                    status=status,
                    executed_qty='0'
                )
            raise Exception("Failed to create stop loss order - empty response")
        except Exception as e:
            logger.error(f"Failed to create stop loss order: {e}")
            raise
    
    def create_take_profit_order(self, symbol: str, side: str, quantity: str, 
                                stop_price: str, reduce_only: bool = True) -> FuturesOrderInfo:
        """
        Create take profit order (OKX requires contracts, not crypto amount)
        
        Note: 'side' is the CLOSING side
        - If side='SELL' → Closing a LONG position → posSide='long'
        - If side='BUY' → Closing a SHORT position → posSide='short'
        """
        try:
            # Convert crypto quantity to contracts
            quantity_float = float(quantity)
            contracts = self.quantity_to_contracts(quantity_float, symbol)
            
            okx_side = 'buy' if side == 'BUY' else 'sell'
            # Position side is OPPOSITE of closing side
            pos_side = 'short' if side == 'BUY' else 'long'
            
            # Format contracts string without floating point errors
            from decimal import Decimal
            contracts_str = str(Decimal(str(contracts)).normalize())
            
            params = {
                'instId': self._to_okx_symbol(symbol),
                'tdMode': 'cross',
                'side': okx_side,
                'posSide': pos_side,  # Required for long_short_mode
                'ordType': 'conditional',
                'sz': contracts_str,  # Clean string (no floating point errors)
                'tpTriggerPx': stop_price,
                'tpOrdPx': '-1',  # Market price
                'reduceOnly': reduce_only
            }
            
            logger.info(f"🎯 Creating TP order: {quantity} crypto → {contracts} contracts @ ${stop_price} (posSide={pos_side})")
            
            result = self._make_request("POST", "/api/v5/trade/order-algo", params, signed=True)
            
            if result and len(result) > 0:
                order = result[0]
                
                algo_id = order.get('algoId', '')
                s_code = order.get('sCode', '')
                s_msg = order.get('sMsg', '')
                
                if s_code == '0':
                    logger.info(f"✅ TP order placed! Algo ID: {algo_id}")
                    status = 'NEW'
                else:
                    logger.error(f"❌ TP order failed: [{s_code}] {s_msg}")
                    raise Exception(f"OKX TP order error [{s_code}]: {s_msg}")
                
                return FuturesOrderInfo(
                    order_id=algo_id,
                    client_order_id=order.get('clOrdId', ''),
                    symbol=symbol,
                    side=side,
                    type='TAKE_PROFIT_MARKET',
                    quantity=str(contracts),
                    price=stop_price,
                    status=status,
                    executed_qty='0'
                )
            raise Exception("Failed to create take profit order - empty response")
        except Exception as e:
            logger.error(f"Failed to create take profit order: {e}")
            raise
    
    def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """Get all open orders for symbol"""
        try:
            params = {'instType': 'SWAP', 'instId': self._to_okx_symbol(symbol)}
            result = self._make_request("GET", "/api/v5/trade/orders-pending", params, signed=True)
            return result
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel a specific order"""
        try:
            params = {
                'instId': self._to_okx_symbol(symbol),
                'ordId': order_id
            }
            self._make_request("POST", "/api/v5/trade/cancel-order", params, signed=True)
            logger.info(f"❌ Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    def cancel_all_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol"""
        try:
            orders = self.get_open_orders(symbol)
            for order in orders:
                self.cancel_order(symbol, order.get('ordId', ''))
            return True
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                   start_time: int = None, end_time: int = None) -> pd.DataFrame:
        """
        Get OKX kline data
        
        OKX Pagination Logic (OPPOSITE of Binance!):
        - 'after': Get data OLDER than this timestamp (pagination backwards)
        - 'before': Get data NEWER than this timestamp (pagination forwards)
        - If neither specified: Returns LATEST candles (most recent data)
        
        For initial fetch, we DON'T use after/before, just get latest data!
        """
        try:
            # Convert interval format
            interval_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1H', '2h': '2H', '4h': '4H', '6h': '6H', '12h': '12H',
                '1d': '1D', '1w': '1W', '1M': '1M'
            }
            
            okx_interval = interval_map.get(interval, '1H')
            okx_symbol = self._to_okx_symbol(symbol)
            
            # OKX max limit is 300 for candles
            actual_limit = min(limit, 300)
            
            params = {
                'instId': okx_symbol,
                'bar': okx_interval,
                'limit': str(actual_limit)
            }
            
            # For standard bot usage, we want LATEST data
            # So we DON'T use after/before on first fetch
            # The bot will get the most recent candles by default
            logger.info(f"📊 Fetching OKX klines: {okx_symbol} {okx_interval} limit={actual_limit}")
            logger.info(f"   Mode: Latest candles (no time range specified)")
            
            result = self._make_request("GET", "/api/v5/market/candles", params)
            
            if not result or len(result) == 0:
                logger.error(f"❌ Empty result from OKX klines API for {okx_symbol} {okx_interval}")
                logger.error(f"   Symbol: {okx_symbol}")
                logger.error(f"   Interval: {okx_interval}")
                logger.error(f"   Limit: {actual_limit}")
                logger.error(f"   Possible causes:")
                logger.error(f"   1. Symbol not available on OKX (check if {okx_symbol} exists)")
                logger.error(f"   2. Wrong interval format")
                logger.error(f"   3. No trading data for this pair")
                raise Exception(f"No kline data returned for {okx_symbol}")
            
            logger.info(f"✅ Got {len(result)} candles from OKX")
            
            # OKX returns [timestamp, open, high, low, close, volume, volCcy, volCcyQuote, confirm]
            data = []
            for item in result:
                data.append({
                    'timestamp': int(item[0]),
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5])
                })
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp')
            
            logger.info(f"📈 Processed {len(df)} candles, date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to get klines: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _sync_server_time(self):
        """Sync with OKX server time"""
        try:
            response = requests.get(f"{self.base_url}/api/v5/public/time", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '0' and data.get('data'):
                    server_time = int(data['data'][0]['ts'])
                    local_time = int(time.time() * 1000)
                    self._time_offset = server_time - local_time
                    logger.info(f"⏱️ OKX server time synced, offset={self._time_offset} ms")
        except Exception as e:
            logger.warning(f"⚠️ Failed to sync OKX server time: {e}")
            self._time_offset = 0
    
    def _to_okx_symbol(self, symbol: str) -> str:
        """Convert symbol to OKX format (BTCUSDT -> BTC-USDT-SWAP)"""
        base_symbol = symbol.replace('/', '').replace('USDT', '-USDT')
        return f"{base_symbol}-SWAP"
    
    def _from_okx_symbol(self, okx_symbol: str) -> str:
        """Convert OKX symbol back to standard format"""
        return okx_symbol.replace('-SWAP', '').replace('-', '')
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for OKX"""
        return symbol.replace('/', '').upper()


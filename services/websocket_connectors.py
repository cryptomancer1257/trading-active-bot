"""
WebSocket Connectors for Exchanges

Handles WebSocket connections to Binance and Bybit Futures
Manages connection lifecycle, reconnection, and message parsing
"""

import asyncio
import json
import logging
import websockets
from typing import Callable, List
from datetime import datetime

logger = logging.getLogger(__name__)


class BinanceFuturesWebSocket:
    """
    Binance Futures WebSocket connector
    Subscribes to miniTicker streams for real-time price updates
    """
    
    def __init__(self):
        self.ws = None
        self.running = False
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60
        
    async def subscribe_ticker(self, symbols: List[str], callback: Callable):
        """
        Subscribe to price updates for multiple symbols
        
        Args:
            symbols: List of symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
            callback: Async function to call with (symbol, price, timestamp)
        """
        self.running = True
        
        # Build stream names
        streams = [f"{symbol.lower()}@miniTicker" for symbol in symbols]
        stream_string = "/".join(streams)
        
        ws_url = f"wss://fstream.binance.com/stream?streams={stream_string}"
        
        logger.info(f"🔌 Connecting to Binance Futures WebSocket...")
        logger.info(f"📊 Subscribing to {len(symbols)} symbols")
        
        while self.running:
            try:
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as websocket:
                    self.ws = websocket
                    logger.info(f"✅ Binance WebSocket connected")
                    
                    # Reset reconnect delay on successful connection
                    self.reconnect_delay = 5
                    
                    # Listen for messages
                    async for message in websocket:
                        if not self.running:
                            break
                        
                        await self._handle_message(message, callback)
                        
            except websockets.exceptions.ConnectionClosed:
                if self.running:
                    logger.warning(f"⚠️ Binance WebSocket disconnected, reconnecting in {self.reconnect_delay}s...")
                    await asyncio.sleep(self.reconnect_delay)
                    # Exponential backoff
                    self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                else:
                    break
                    
            except Exception as e:
                if self.running:
                    logger.error(f"❌ Binance WebSocket error: {e}")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    break
    
    async def _handle_message(self, message: str, callback: Callable):
        """Parse and handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Check if it's a miniTicker message
            if 'data' in data:
                ticker_data = data['data']
                
                if ticker_data.get('e') == '24hrMiniTicker':
                    symbol = ticker_data.get('s')  # Symbol (e.g., BTCUSDT)
                    price = float(ticker_data.get('c'))  # Close price
                    timestamp = ticker_data.get('E')  # Event time
                    
                    # Call callback with parsed data
                    await callback(symbol, price, timestamp)
                    
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Binance WebSocket message: {message}")
        except Exception as e:
            logger.error(f"Error handling Binance message: {e}")
    
    async def close(self):
        """Close WebSocket connection"""
        logger.info("🛑 Closing Binance WebSocket...")
        self.running = False
        
        if self.ws:
            try:
                await self.ws.close()
                logger.info("✅ Binance WebSocket closed")
            except Exception as e:
                logger.warning(f"⚠️  Error closing Binance WebSocket: {e}")


class BybitFuturesWebSocket:
    """
    Bybit Futures WebSocket connector
    Subscribes to ticker streams for real-time price updates
    """
    
    def __init__(self, testnet: bool = False):
        self.ws = None
        self.running = False
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60
        self.last_ping = None
        self.testnet = testnet
        self.subscribed_symbols = set()  # Track which symbols we subscribed to
        
    async def subscribe_ticker(self, symbols: List[str], callback: Callable):
        """
        Subscribe to price updates for multiple symbols
        
        Args:
            symbols: List of symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
            callback: Async function to call with (symbol, price, timestamp)
        """
        self.running = True
        
        # Use testnet or mainnet URL based on configuration
        ws_url = "wss://stream-testnet.bybit.com/v5/public/linear" if self.testnet else "wss://stream.bybit.com/v5/public/linear"
        
        logger.info(f"🔌 Connecting to Bybit Futures WebSocket ({'TESTNET' if self.testnet else 'MAINNET'})...")
        logger.info(f"📊 URL: {ws_url}")
        logger.info(f"📊 Subscribing to {len(symbols)} symbols")
        
        while self.running:
            try:
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as websocket:
                    self.ws = websocket
                    logger.info(f"✅ Bybit WebSocket connected")
                    
                    # Reset reconnect delay on successful connection
                    self.reconnect_delay = 5
                    
                    # Subscribe to tickers (remove "/" from symbols for Bybit)
                    formatted_symbols = [symbol.replace("/", "") for symbol in symbols]
                    self.subscribed_symbols = set(formatted_symbols)  # Store subscribed symbols
                    subscribe_message = {
                        "op": "subscribe",
                        "args": [f"tickers.{symbol}" for symbol in formatted_symbols]
                    }
                    
                    await websocket.send(json.dumps(subscribe_message))
                    logger.info(f"📡 Sent subscription request for {len(symbols)} symbols: {', '.join(formatted_symbols)}")
                    logger.info(f"📋 Subscribed symbols: {self.subscribed_symbols}")
                    
                    # Start heartbeat task
                    heartbeat_task = asyncio.create_task(self._send_heartbeat(websocket))
                    
                    try:
                        # Listen for messages
                        async for message in websocket:
                            if not self.running:
                                break
                            
                            await self._handle_message(message, callback)
                    finally:
                        heartbeat_task.cancel()
                        
            except websockets.exceptions.ConnectionClosed:
                if self.running:
                    logger.warning(f"⚠️ Bybit WebSocket disconnected, reconnecting in {self.reconnect_delay}s...")
                    await asyncio.sleep(self.reconnect_delay)
                    # Exponential backoff
                    self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                else:
                    break
                    
            except Exception as e:
                if self.running:
                    logger.error(f"❌ Bybit WebSocket error: {e}")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    break
    
    async def _send_heartbeat(self, websocket):
        """Send periodic ping to keep connection alive"""
        while self.running:
            try:
                await asyncio.sleep(20)
                if self.running:
                    ping_message = {"op": "ping"}
                    await websocket.send(json.dumps(ping_message))
                    self.last_ping = datetime.utcnow()
                    logger.debug("💓 Sent Bybit ping")
            except Exception as e:
                logger.error(f"Error sending Bybit heartbeat: {e}")
                break
    
    async def _handle_message(self, message: str, callback: Callable):
        """Parse and handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Log first message for debugging
            if not hasattr(self, '_first_msg_logged'):
                logger.info(f"📩 First Bybit message: {str(data)[:200]}")
                self._first_msg_logged = True
            
            # Handle subscription success
            if data.get('op') == 'subscribe' and data.get('success'):
                logger.info(f"✅ Bybit subscription successful")
                return
            
            # Handle pong
            if data.get('op') == 'pong':
                logger.debug("💓 Received Bybit pong")
                return
            
            # Handle ticker data
            if data.get('topic', '').startswith('tickers.'):
                ticker_data = data.get('data', {})
                
                symbol = ticker_data.get('symbol')  # Symbol (e.g., BTCUSDT)
                
                # Filter: Only process symbols we explicitly subscribed to
                if symbol not in self.subscribed_symbols:
                    logger.debug(f"⏭️  Skipping unsubscribed symbol: {symbol}")
                    return
                
                # ONLY use lastPrice (real trades), ignore markPrice/indexPrice
                # markPrice and indexPrice are derivatives and can differ significantly
                price_str = ticker_data.get('lastPrice')
                
                if not price_str or price_str == '0':
                    # Skip messages without lastPrice (use only real trades)
                    return
                    
                price = float(price_str)
                timestamp = ticker_data.get('timestamp')  # Timestamp in ms
                
                # Additional validation: skip if price is unrealistic (< $1k or > $10M for BTC)
                if symbol == 'BTCUSDT' and (price < 1000 or price > 10000000):
                    logger.warning(f"⚠️  Unusual price for {symbol}: ${price:,.2f} - skipping")
                    return
                
                if symbol and price > 0:
                    # Call callback with parsed data
                    logger.info(f"💹 Price update: {symbol} = ${price:,.2f}")
                    await callback(symbol, price, timestamp)
            else:
                # Log unhandled message types
                logger.debug(f"🔍 Unhandled message type: {data.get('op') or data.get('topic', 'unknown')}")
                    
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Bybit WebSocket message: {message}")
        except Exception as e:
            logger.error(f"Error handling Bybit message: {e}")
    
    async def close(self):
        """Close WebSocket connection"""
        logger.info("🛑 Closing Bybit WebSocket...")
        self.running = False
        
        if self.ws:
            try:
                await self.ws.close()
                logger.info("✅ Bybit WebSocket closed")
            except Exception as e:
                logger.warning(f"⚠️  Error closing Bybit WebSocket: {e}")


class WebSocketReconnectManager:
    """
    Manages reconnection logic with exponential backoff
    Can be used as a mixin or standalone helper
    """
    
    def __init__(self, initial_delay: float = 5.0, max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.current_delay = initial_delay
        self.reconnect_count = 0
    
    async def wait_before_reconnect(self):
        """Wait with exponential backoff before reconnecting"""
        logger.info(f"⏳ Waiting {self.current_delay}s before reconnect (attempt #{self.reconnect_count + 1})")
        await asyncio.sleep(self.current_delay)
        
        self.reconnect_count += 1
        self.current_delay = min(self.current_delay * self.backoff_factor, self.max_delay)
    
    def reset(self):
        """Reset reconnection state after successful connection"""
        self.current_delay = self.initial_delay
        self.reconnect_count = 0


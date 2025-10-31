"""
Binance Signals Bot with LLM Integration
Advanced signals bot with LLM AI analysis for intelligent market signals
Only sends trading signals to users - NO ACTUAL TRADING
Uses OpenAI/Claude/Gemini for market analysis and signal generation
NO USER API KEYS REQUIRED - Uses public Binance endpoints only
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging
import json
import time
import requests
import asyncio
import random
from datetime import datetime, timedelta
from dataclasses import dataclass

from bots.bot_sdk.CustomBot import CustomBot
from bots.bot_sdk.Action import Action
from services.llm_integration import create_llm_service
from services.transaction_service import TransactionService

logger = logging.getLogger(__name__)

@dataclass
class SignalInfo:
    """Trading signal information"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float  # 0.0 to 1.0
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reason: str
    analysis: str
    timestamp: datetime
    timeframes: List[str]
    indicators: Dict[str, Any]

class BinancePublicAPI:
    """Binance Public API - NO AUTHENTICATION REQUIRED"""
    
    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        
        # Use public endpoints only
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
        
        logger.info(f"🌐 Initialized Binance Public API {'TESTNET' if testnet else 'PRODUCTION'}")
        logger.info("✅ NO API KEYS REQUIRED - Using public endpoints only")
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> List[Dict]:
        """Get kline/candlestick data - PUBLIC ENDPOINT"""
        endpoint = "/fapi/v1/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Public API call - no authentication needed
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            klines = response.json()
            
            # Convert to standardized format
            formatted_data = []
            for kline in klines:
                formatted_data.append({
                    'timestamp': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': int(kline[6]),
                    'quote_volume': float(kline[7]),
                    'trades': int(kline[8])
                })
            
            logger.info(f"📊 Retrieved {len(formatted_data)} {interval} candles for {symbol}")
            return formatted_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching klines for {symbol} {interval}: {e}")
            return []
    
    def get_ticker_price(self, symbol: str) -> float:
        """Get current ticker price - PUBLIC ENDPOINT"""
        endpoint = "/fapi/v1/ticker/price"
        params = {'symbol': symbol}
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Public API call - no authentication needed
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            price = float(data['price'])
            logger.info(f"💰 Current price for {symbol}: ${price:,.2f}")
            return price
            
        except Exception as e:
            logger.error(f"❌ Error fetching price for {symbol}: {e}")
            return 0.0
    
    def get_24hr_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get 24hr ticker statistics - PUBLIC ENDPOINT"""
        endpoint = "/fapi/v1/ticker/24hr"
        params = {'symbol': symbol}
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'symbol': data['symbol'],
                'price_change': float(data['priceChange']),
                'price_change_percent': float(data['priceChangePercent']),
                'high_price': float(data['highPrice']),
                'low_price': float(data['lowPrice']),
                'volume': float(data['volume']),
                'count': int(data['count'])
            }
            
        except Exception as e:
            logger.error(f"❌ Error fetching 24hr ticker for {symbol}: {e}")
            return {}

class BinanceSignalsBot(CustomBot):
    """Advanced Binance Signals Bot - NO USER API KEYS REQUIRED"""
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str] = None, user_principal_id: str = None):
        """Initialize Signals Bot - No user API keys required"""
        super().__init__(config, api_keys)
        
        # Signals specific configuration
        self.trading_pair = config.get('trading_pair', 'BTCUSDT')
        self.testnet = config.get('testnet', True)
        
        # Multi-timeframe configuration - Optimized 3 timeframes
        self.timeframes = config.get('timeframes', ['30m', '1h', '4h'])
        self.primary_timeframe = config.get('primary_timeframe', self.timeframes[0])
        
        # Validate timeframes
        supported_timeframes = [
            '1m', '3m', '5m', '15m', '30m',  # Minutes
            '1h', '2h', '4h', '6h', '8h', '12h',  # Hours  
            '1d', '3d', '1w', '1M'  # Days, weeks, months
        ]
        
        # Filter valid timeframes
        valid_timeframes = [tf for tf in self.timeframes if tf in supported_timeframes]
        if len(valid_timeframes) != len(self.timeframes):
            invalid_tfs = [tf for tf in self.timeframes if tf not in supported_timeframes]
            logger.warning(f"❌ Unsupported timeframes removed: {invalid_tfs}")
            logger.info(f"✅ Supported timeframes: {supported_timeframes}")
        
        self.timeframes = valid_timeframes if valid_timeframes else ['1h']
        
        # Ensure primary timeframe is valid
        if self.primary_timeframe not in self.timeframes:
            self.primary_timeframe = self.timeframes[0]
            logger.warning(f"⚠️ Primary timeframe adjusted to: {self.primary_timeframe}")
        
        # LLM configuration
        self.llm_model = config.get('llm_model', 'openai')
        self.use_llm_analysis = config.get('use_llm_analysis', True)
        
        # Technical indicators config
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        
        # Signal thresholds
        self.min_confidence = config.get('min_confidence', 0.6)  # Minimum 60% confidence
        self.strong_signal_threshold = config.get('strong_signal_threshold', 0.8)  # 80% for strong signals
        
        # Store user principal for logging (optional)
        self.user_principal_id = user_principal_id or "anonymous"
        
        # Initialize Binance Public API - NO USER CREDENTIALS NEEDED
        self.binance_api = BinancePublicAPI(testnet=self.testnet)
        logger.info("🔓 Using Binance Public API - No user API keys required")
        
        # Initialize LLM service with provided API keys (environment/config)
        if self.use_llm_analysis and api_keys:
            try:
                # Create config dict for LLM service (correct signature)
                llm_config = {
                    'openai_api_key': api_keys.get('openai_api_key'),
                    'claude_api_key': api_keys.get('anthropic_api_key'),  # Note: anthropic_api_key maps to claude
                    'gemini_api_key': api_keys.get('google_api_key'),
                    'default_model': self.llm_model
                }
                
                self.llm_service = create_llm_service(llm_config)
                logger.info(f"✅ LLM service initialized: {self.llm_model}")
            except Exception as e:
                logger.warning(f"⚠️ LLM service initialization failed: {e}")
                self.llm_service = None
                self.use_llm_analysis = False
        else:
            self.llm_service = None
            self.use_llm_analysis = False
            logger.info("📊 Using technical analysis only (no LLM)")
        
        logger.info("=" * 60)
        logger.info(f"🔮 Binance Signals Bot initialized for {self.trading_pair}")
        logger.info(f"📊 Timeframes: {self.timeframes} (Primary: {self.primary_timeframe})")
        logger.info(f"🧪 Environment: {'TESTNET' if self.testnet else 'PRODUCTION'}")
        logger.info(f"🤖 LLM Analysis: {'ON' if self.use_llm_analysis else 'OFF'}")
        logger.info(f"🆔 User Principal: {self.user_principal_id}")
        logger.info("⚠️ SIGNALS ONLY - NO TRADING WILL BE PERFORMED")
        logger.info("🔓 NO USER API KEYS REQUIRED - PUBLIC DATA ONLY")
        logger.info("=" * 60)
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        prices_array = np.array(prices)
        deltas = np.diff(prices_array)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Calculate MACD indicator"""
        if len(prices) < slow:
            return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}
        
        prices_array = np.array(prices)
        
        # Calculate EMAs
        ema_fast = pd.Series(prices_array).ewm(span=fast).mean().iloc[-1]
        ema_slow = pd.Series(prices_array).ewm(span=slow).mean().iloc[-1]
        
        macd = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD)
        if len(prices) >= slow + signal:
            macd_series = pd.Series(prices_array).ewm(span=fast).mean() - pd.Series(prices_array).ewm(span=slow).mean()
            signal_line = macd_series.ewm(span=signal).mean().iloc[-1]
        else:
            signal_line = macd
        
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_sma(self, prices: List[float], period: int = 20) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        return np.mean(prices[-period:])
    
    def calculate_ema(self, prices: List[float], period: int = 20) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return self.calculate_sma(prices, len(prices))
        
        return pd.Series(prices).ewm(span=period).mean().iloc[-1]
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            current_price = prices[-1] if prices else 0.0
            return {
                'upper': current_price,
                'middle': current_price,
                'lower': current_price
            }
        
        sma = self.calculate_sma(prices, period)
        std = np.std(prices[-period:])
        
        return {
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }
    
    def calculate_volume_profile(self, data: List[Dict]) -> Dict[str, Any]:
        """Calculate basic volume analysis"""
        if not data or len(data) < 2:
            return {'avg_volume': 0, 'volume_trend': 'neutral'}
        
        volumes = [candle['volume'] for candle in data[-20:]]  # Last 20 periods
        avg_volume = np.mean(volumes)
        
        # Compare recent volume to average
        recent_volume = np.mean(volumes[-5:])  # Last 5 periods
        
        volume_trend = 'increasing' if recent_volume > avg_volume * 1.2 else 'decreasing' if recent_volume < avg_volume * 0.8 else 'neutral'
        
        return {
            'avg_volume': avg_volume,
            'recent_volume': recent_volume,
            'volume_trend': volume_trend,
            'volume_ratio': recent_volume / avg_volume if avg_volume > 0 else 1.0
        }
    
    def crawl_data(self) -> Dict[str, Any]:
        """Crawl historical data for multiple timeframes using public API"""
        try:
            logger.info(f"🕷️ Crawling public market data for {len(self.timeframes)} timeframes: {self.timeframes}")
            
            timeframes_data = {}
            
            for timeframe in self.timeframes:
                logger.info(f"📊 Fetching {timeframe} data for {self.trading_pair}")
                
                # Get kline data from public API
                klines = self.binance_api.get_klines(self.trading_pair, timeframe, limit=200)
                
                if not klines:
                    logger.warning(f"❌ No data for {timeframe}")
                    continue
                
                timeframes_data[timeframe] = klines
                logger.info(f"✅ {timeframe}: {len(klines)} candles")
            
            if not timeframes_data:
                raise Exception("No timeframe data retrieved")
            
            # Get current price and 24hr stats
            current_price = self.binance_api.get_ticker_price(self.trading_pair)
            ticker_24hr = self.binance_api.get_24hr_ticker(self.trading_pair)
            
            result = {
                'timeframes': timeframes_data,
                'current_price': current_price,
                'ticker_24hr': ticker_24hr,
                'timestamp': datetime.now().isoformat(),
                'symbol': self.trading_pair,
                'data_source': 'binance_public_api'
            }
            
            logger.info(f"✅ Data crawling completed for {len(timeframes_data)} timeframes")
            logger.info(f"💰 Current price: ${current_price:,.2f}")
            if ticker_24hr:
                logger.info(f"📈 24h change: {ticker_24hr.get('price_change_percent', 0):.2f}%")
            
            # Store the crawled data for LLM analysis
            self._last_crawled_data = timeframes_data
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error crawling data: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def analyze_data(self, multi_timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze multi-timeframe historical data and calculate indicators"""
        try:
            timeframes_data = multi_timeframe_data.get("timeframes", {})
            current_price = multi_timeframe_data.get("current_price", 0)
            ticker_24hr = multi_timeframe_data.get("ticker_24hr", {})
            
            if not timeframes_data:
                raise Exception("No timeframe data to analyze")
            
            logger.info(f"🔍 Analyzing {len(timeframes_data)} timeframes")
            
            analysis_result = {
                'symbol': self.trading_pair,
                'current_price': current_price,
                'ticker_24hr': ticker_24hr,
                'timestamp': datetime.now().isoformat(),
                'multi_timeframe': {},
                'primary_analysis': {},
                'market_overview': {},
                'data_source': 'public_api_analysis'
            }
            
            # Analyze each timeframe
            for timeframe, data in timeframes_data.items():
                if not data:
                    continue
                
                closes = [candle['close'] for candle in data]
                highs = [candle['high'] for candle in data]
                lows = [candle['low'] for candle in data]
                volumes = [candle['volume'] for candle in data]
                
                # Calculate technical indicators
                rsi = self.calculate_rsi(closes)
                macd = self.calculate_macd(closes)
                sma_20 = self.calculate_sma(closes, 20)
                sma_50 = self.calculate_sma(closes, 50)
                ema_12 = self.calculate_ema(closes, 12)
                ema_26 = self.calculate_ema(closes, 26)
                bb = self.calculate_bollinger_bands(closes)
                volume_analysis = self.calculate_volume_profile(data)
                
                # Trend analysis
                trend_bullish = closes[-1] > sma_20 and sma_20 > sma_50 and ema_12 > ema_26
                trend_bearish = closes[-1] < sma_20 and sma_20 < sma_50 and ema_12 < ema_26
                
                # Support/Resistance levels
                recent_highs = highs[-20:]
                recent_lows = lows[-20:]
                resistance = max(recent_highs) if recent_highs else closes[-1]
                support = min(recent_lows) if recent_lows else closes[-1]
                
                # Price momentum
                price_change_5 = ((closes[-1] - closes[-6]) / closes[-6] * 100) if len(closes) > 5 else 0
                price_change_10 = ((closes[-1] - closes[-11]) / closes[-11] * 100) if len(closes) > 10 else 0
                
                timeframe_analysis = {
                    'timeframe': timeframe,
                    'candles_count': len(data),
                    'price_info': {
                        'current': closes[-1],
                        'high_24h': max(highs[-24:]) if len(highs) >= 24 else max(highs),
                        'low_24h': min(lows[-24:]) if len(lows) >= 24 else min(lows),
                        'volume': volumes[-1] if volumes else 0,
                        'price_change_5p': price_change_5,
                        'price_change_10p': price_change_10
                    },
                    'indicators': {
                        'rsi': rsi,
                        'macd': macd,
                        'sma_20': sma_20,
                        'sma_50': sma_50,
                        'ema_12': ema_12,
                        'ema_26': ema_26,
                        'bollinger_bands': bb
                    },
                    'trend': {
                        'bullish': trend_bullish,
                        'bearish': trend_bearish,
                        'neutral': not trend_bullish and not trend_bearish
                    },
                    'support_resistance': {
                        'support': support,
                        'resistance': resistance,
                        'distance_to_support': ((closes[-1] - support) / support * 100) if support > 0 else 0,
                        'distance_to_resistance': ((resistance - closes[-1]) / closes[-1] * 100) if closes[-1] > 0 else 0
                    },
                    'volume_analysis': volume_analysis
                }
                
                analysis_result['multi_timeframe'][timeframe] = timeframe_analysis
                
                # Use primary timeframe for main analysis
                if timeframe == self.primary_timeframe:
                    analysis_result['primary_analysis'] = timeframe_analysis
            
            # Market overview and consensus
            bullish_timeframes = sum(1 for tf_analysis in analysis_result['multi_timeframe'].values() 
                                   if tf_analysis['trend']['bullish'])
            bearish_timeframes = sum(1 for tf_analysis in analysis_result['multi_timeframe'].values() 
                                   if tf_analysis['trend']['bearish'])
            total_timeframes = len(analysis_result['multi_timeframe'])
            
            # Calculate average RSI across timeframes
            rsi_values = [tf['indicators']['rsi'] for tf in analysis_result['multi_timeframe'].values()]
            avg_rsi = np.mean(rsi_values) if rsi_values else 50
            
            analysis_result['market_overview'] = {
                'total_timeframes': total_timeframes,
                'bullish_timeframes': bullish_timeframes,
                'bearish_timeframes': bearish_timeframes,
                'neutral_timeframes': total_timeframes - bullish_timeframes - bearish_timeframes,
                'overall_sentiment': 'bullish' if bullish_timeframes > bearish_timeframes else 'bearish' if bearish_timeframes > bullish_timeframes else 'neutral',
                'consensus_strength': max(bullish_timeframes, bearish_timeframes) / total_timeframes if total_timeframes > 0 else 0,
                'average_rsi': avg_rsi,
                'rsi_condition': 'overbought' if avg_rsi > 70 else 'oversold' if avg_rsi < 30 else 'neutral'
            }
            
            logger.info(f"✅ Analysis completed for {len(timeframes_data)} timeframes")
            logger.info(f"📊 Overall sentiment: {analysis_result['market_overview']['overall_sentiment'].upper()}")
            logger.info(f"📈 Consensus strength: {analysis_result['market_overview']['consensus_strength']:.1%}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing data: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_signal(self, analysis: Dict[str, Any]) -> Action:
        """Generate trading signal based on multi-timeframe analysis"""
        try:
            # Check for analysis errors
            if 'error' in analysis:
                return Action("HOLD", 0.0, f"Analysis error: {analysis['error']}")
            
            primary_analysis = analysis.get('primary_analysis', {})
            market_overview = analysis.get('market_overview', {})
            current_price = analysis.get('current_price', 0)
            ticker_24hr = analysis.get('ticker_24hr', {})
            
            if not primary_analysis:
                return Action("HOLD", 0.0, "No primary analysis available")
            
            # Extract indicators from primary timeframe
            indicators = primary_analysis.get('indicators', {})
            trend = primary_analysis.get('trend', {})
            support_resistance = primary_analysis.get('support_resistance', {})
            volume_analysis = primary_analysis.get('volume_analysis', {})
            
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', {})
            bb = indicators.get('bollinger_bands', {})
            
            # Initialize signal
            signal_action = "HOLD"
            confidence = 0.5
            signal_reasons = []
            
            # 1. RSI signals (weight: 0.2)
            if rsi < self.rsi_oversold:
                signal_action = "BUY"
                confidence += 0.2
                signal_reasons.append(f"RSI oversold at {rsi:.1f}")
            elif rsi > self.rsi_overbought:
                signal_action = "SELL"
                confidence += 0.2
                signal_reasons.append(f"RSI overbought at {rsi:.1f}")
            
            # 2. MACD signals (weight: 0.15)
            macd_histogram = macd.get('histogram', 0)
            macd_line = macd.get('macd', 0)
            macd_signal = macd.get('signal', 0)
            
            if macd_histogram > 0 and macd_line > macd_signal:
                if signal_action != "SELL":
                    signal_action = "BUY"
                    confidence += 0.15
                    signal_reasons.append("MACD bullish crossover")
            elif macd_histogram < 0 and macd_line < macd_signal:
                if signal_action != "BUY":
                    signal_action = "SELL"
                    confidence += 0.15
                    signal_reasons.append("MACD bearish crossover")
            
            # 3. Trend signals (weight: 0.1)
            if trend.get('bullish'):
                if signal_action != "SELL":
                    signal_action = "BUY"
                    confidence += 0.1
                    signal_reasons.append("Strong bullish trend")
            elif trend.get('bearish'):
                if signal_action != "BUY":
                    signal_action = "SELL"
                    confidence += 0.1
                    signal_reasons.append("Strong bearish trend")
            
            # 4. Multi-timeframe consensus (weight: 0.15)
            consensus_strength = market_overview.get('consensus_strength', 0)
            overall_sentiment = market_overview.get('overall_sentiment', 'neutral')
            
            if overall_sentiment == 'bullish' and consensus_strength > 0.6:
                if signal_action != "SELL":
                    signal_action = "BUY"
                    confidence += 0.15
                    signal_reasons.append(f"Strong bullish consensus ({consensus_strength:.1%})")
            elif overall_sentiment == 'bearish' and consensus_strength > 0.6:
                if signal_action != "BUY":
                    signal_action = "SELL"
                    confidence += 0.15
                    signal_reasons.append(f"Strong bearish consensus ({consensus_strength:.1%})")
            
            # 5. Bollinger Bands signals (weight: 0.1)
            if bb and current_price:
                bb_upper = bb.get('upper', 0)
                bb_lower = bb.get('lower', 0)
                bb_middle = bb.get('middle', 0)
                
                if current_price < bb_lower:
                    if signal_action != "SELL":
                        signal_action = "BUY"
                        confidence += 0.1
                        signal_reasons.append("Price below Bollinger lower band (oversold)")
                elif current_price > bb_upper:
                    if signal_action != "BUY":
                        signal_action = "SELL"
                        confidence += 0.1
                        signal_reasons.append("Price above Bollinger upper band (overbought)")
            
            # 6. Volume confirmation (weight: 0.05)
            volume_trend = volume_analysis.get('volume_trend', 'neutral')
            if volume_trend == 'increasing':
                confidence += 0.05
                signal_reasons.append("Volume increasing (confirmation)")
            
            # 7. 24hr momentum (weight: 0.05)
            if ticker_24hr:
                price_change_24h = ticker_24hr.get('price_change_percent', 0)
                if abs(price_change_24h) > 3:  # Significant 24h movement
                    if price_change_24h > 3 and signal_action == "BUY":
                        confidence += 0.05
                        signal_reasons.append(f"Strong 24h momentum (+{price_change_24h:.1f}%)")
                    elif price_change_24h < -3 and signal_action == "SELL":
                        confidence += 0.05
                        signal_reasons.append(f"Strong 24h momentum ({price_change_24h:.1f}%)")
            
            # Limit confidence to 1.0
            confidence = min(confidence, 1.0)
            
            # Check minimum confidence threshold
            if confidence < self.min_confidence:
                signal_action = "HOLD"
                signal_reasons.append(f"Confidence below threshold ({confidence:.1%} < {self.min_confidence:.1%})")
            
            # Generate comprehensive signal reason
            reason_text = "; ".join(signal_reasons) if signal_reasons else "No clear signals detected"
            
            # Create action
            action = Action(signal_action, confidence, reason_text)
            
            # Add comprehensive LLM analysis if enabled (note: this will be called from async context)
            action.recommendation = f"Technical analysis: {reason_text}"
            
            logger.info(f"🔮 Signal generated: {signal_action} ({confidence:.1%})")
            logger.info(f"📝 Primary reasons: {reason_text}")
            
            return action
            
        except Exception as e:
            logger.error(f"❌ Error generating signal: {e}")
            return Action("HOLD", 0.0, f"Signal generation error: {str(e)}")
    
    def create_technical_summary(self, analysis: Dict[str, Any], signal_action: str, confidence: float) -> str:
        """Create detailed technical analysis summary when LLM is not available"""
        try:
            current_price = analysis.get('current_price', 0)
            ticker_24hr = analysis.get('ticker_24hr', {})
            primary_analysis = analysis.get('primary_analysis', {})
            market_overview = analysis.get('market_overview', {})
            
            indicators = primary_analysis.get('indicators', {})
            support_resistance = primary_analysis.get('support_resistance', {})
            
            summary = f"""
TECHNICAL ANALYSIS REPORT - {analysis.get('symbol', self.trading_pair)}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

CURRENT MARKET SNAPSHOT:
• Price: ${current_price:,.2f}
• 24h Change: {ticker_24hr.get('price_change_percent', 0):+.2f}%
• 24h High: ${ticker_24hr.get('high_price', 0):,.2f}
• 24h Low: ${ticker_24hr.get('low_price', 0):,.2f}
• 24h Volume: {ticker_24hr.get('volume', 0):,.0f}

SIGNAL RECOMMENDATION: {signal_action}
Confidence Level: {confidence:.1%} ({'Strong' if confidence >= 0.8 else 'Moderate' if confidence >= 0.6 else 'Weak'})

TECHNICAL INDICATORS ANALYSIS:
• RSI ({self.rsi_period}): {indicators.get('rsi', 0):.1f} - {'Overbought' if indicators.get('rsi', 50) > 70 else 'Oversold' if indicators.get('rsi', 50) < 30 else 'Neutral'}
• MACD: {indicators.get('macd', {}).get('macd', 0):.4f}
• MACD Signal: {indicators.get('macd', {}).get('signal', 0):.4f}
• MACD Histogram: {indicators.get('macd', {}).get('histogram', 0):.4f}
• SMA 20: ${indicators.get('sma_20', 0):,.2f}
• SMA 50: ${indicators.get('sma_50', 0):,.2f}
• EMA 12: ${indicators.get('ema_12', 0):,.2f}
• EMA 26: ${indicators.get('ema_26', 0):,.2f}

SUPPORT & RESISTANCE:
• Support Level: ${support_resistance.get('support', 0):,.2f} ({support_resistance.get('distance_to_support', 0):+.2f}%)
• Resistance Level: ${support_resistance.get('resistance', 0):,.2f} ({support_resistance.get('distance_to_resistance', 0):+.2f}%)

MULTI-TIMEFRAME CONSENSUS:
• Timeframes Analyzed: {market_overview.get('total_timeframes', 0)}
• Bullish Timeframes: {market_overview.get('bullish_timeframes', 0)}
• Bearish Timeframes: {market_overview.get('bearish_timeframes', 0)}
• Overall Sentiment: {market_overview.get('overall_sentiment', 'neutral').upper()}
• Consensus Strength: {market_overview.get('consensus_strength', 0):.1%}
• Average RSI: {market_overview.get('average_rsi', 50):.1f}

BOLLINGER BANDS:
• Upper Band: ${indicators.get('bollinger_bands', {}).get('upper', 0):,.2f}
• Middle Band: ${indicators.get('bollinger_bands', {}).get('middle', 0):,.2f}
• Lower Band: ${indicators.get('bollinger_bands', {}).get('lower', 0):,.2f}

VOLUME ANALYSIS:
• Volume Trend: {primary_analysis.get('volume_analysis', {}).get('volume_trend', 'neutral').upper()}
• Volume Ratio: {primary_analysis.get('volume_analysis', {}).get('volume_ratio', 1.0):.2f}x

TRADING SUGGESTIONS:
"""
            
            if signal_action == "BUY":
                entry_price = current_price
                stop_loss = support_resistance.get('support', current_price * 0.98)
                take_profit = current_price * 1.04
                
                summary += f"""
Entry Strategy: Consider buying on dips near ${entry_price:,.2f}
Stop Loss: ${stop_loss:,.2f} ({((stop_loss - entry_price) / entry_price * 100):+.2f}%)
Take Profit: ${take_profit:,.2f} ({((take_profit - entry_price) / entry_price * 100):+.2f}%)
Risk/Reward Ratio: {abs((take_profit - entry_price) / (entry_price - stop_loss)):.2f}:1
"""
            elif signal_action == "SELL":
                entry_price = current_price
                stop_loss = support_resistance.get('resistance', current_price * 1.02)
                take_profit = current_price * 0.96
                
                summary += f"""
Entry Strategy: Consider selling rallies near ${entry_price:,.2f}
Stop Loss: ${stop_loss:,.2f} ({((stop_loss - entry_price) / entry_price * 100):+.2f}%)
Take Profit: ${take_profit:,.2f} ({((take_profit - entry_price) / entry_price * 100):+.2f}%)
Risk/Reward Ratio: {abs((take_profit - entry_price) / (stop_loss - entry_price)):.2f}:1
"""
            else:
                summary += """
Entry Strategy: Wait for clearer signals
Current market conditions suggest holding position
Monitor key support/resistance levels for breakout opportunities
"""
            
            summary += f"""
RISK DISCLAIMER:
This is a technical analysis for educational purposes only.
Always conduct your own research and risk management.
Past performance does not guarantee future results.
Use proper position sizing and stop losses.

Data Source: Binance Public API (No user credentials required)
Analysis Framework: Multi-timeframe technical analysis
"""
            
            return summary.strip()
            
        except Exception as e:
            return f"Technical analysis summary error: {e}"
    
    def _create_synthetic_ohlcv(self, current_price: float, periods: int = 50) -> List[Dict]:
        """Create synthetic OHLCV data for LLM analysis when historical data is not available"""
        ohlcv_data = []
        base_time = datetime.now()
        
        for i in range(periods):
            # Create realistic price variations (±2% random walk)
            variation = 1 + (random.random() - 0.5) * 0.04  # ±2%
            price = current_price * variation
            
            # Create OHLC with small intraday variations
            high = price * (1 + random.random() * 0.01)  # up to 1% higher
            low = price * (1 - random.random() * 0.01)   # up to 1% lower
            open_price = low + (high - low) * random.random()
            close_price = low + (high - low) * random.random()
            
            volume = 1000 + random.random() * 5000  # Random volume
            
            ohlcv_data.append({
                'timestamp': int((base_time - timedelta(hours=periods-i)).timestamp() * 1000),
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        return ohlcv_data

    async def get_llm_analysis(self, analysis: Dict[str, Any]) -> str:
        """Get comprehensive market analysis from LLM - FULL TEXT RESPONSE"""
        try:
            if not self.llm_service:
                return "LLM service not available"
            
            # Create comprehensive prompt for signals analysis
            current_price = analysis.get('current_price', 0)
            ticker_24hr = analysis.get('ticker_24hr', {})
            market_overview = analysis.get('market_overview', {})
            
            prompt = f"""
You are a professional cryptocurrency trading analyst providing comprehensive market signals and analysis.

Analyze the following market data for {analysis.get('symbol', self.trading_pair)} and provide a detailed trading signal analysis:

CURRENT MARKET CONDITIONS:
• Current Price: ${current_price:,.2f}
• 24h Change: {ticker_24hr.get('price_change_percent', 0):+.2f}%
• 24h High: ${ticker_24hr.get('high_price', 0):,.2f}
• 24h Low: ${ticker_24hr.get('low_price', 0):,.2f}
• 24h Volume: {ticker_24hr.get('volume', 0):,.0f}

MULTI-TIMEFRAME TECHNICAL ANALYSIS:
"""
            
            # Add detailed timeframe data
            multi_tf = analysis.get('multi_timeframe', {})
            for timeframe, tf_data in multi_tf.items():
                indicators = tf_data.get('indicators', {})
                trend = tf_data.get('trend', {})
                sr = tf_data.get('support_resistance', {})
                volume = tf_data.get('volume_analysis', {})
                
                prompt += f"""
{timeframe.upper()} TIMEFRAME:
• RSI: {indicators.get('rsi', 0):.1f}
• MACD Line: {indicators.get('macd', {}).get('macd', 0):.4f}
• MACD Signal: {indicators.get('macd', {}).get('signal', 0):.4f}
• MACD Histogram: {indicators.get('macd', {}).get('histogram', 0):.4f}
• SMA 20: ${indicators.get('sma_20', 0):,.2f}
• SMA 50: ${indicators.get('sma_50', 0):,.2f}
• EMA 12: ${indicators.get('ema_12', 0):,.2f}
• EMA 26: ${indicators.get('ema_26', 0):,.2f}
• Trend: {'Bullish' if trend.get('bullish') else 'Bearish' if trend.get('bearish') else 'Neutral'}
• Support: ${sr.get('support', 0):,.2f} ({sr.get('distance_to_support', 0):+.2f}%)
• Resistance: ${sr.get('resistance', 0):,.2f} ({sr.get('distance_to_resistance', 0):+.2f}%)
• Volume Trend: {volume.get('volume_trend', 'neutral').title()}
• Bollinger Upper: ${indicators.get('bollinger_bands', {}).get('upper', 0):,.2f}
• Bollinger Lower: ${indicators.get('bollinger_bands', {}).get('lower', 0):,.2f}
"""
            
            # Add market overview
            prompt += f"""
MARKET CONSENSUS:
• Total Timeframes: {market_overview.get('total_timeframes', 0)}
• Bullish Timeframes: {market_overview.get('bullish_timeframes', 0)}
• Bearish Timeframes: {market_overview.get('bearish_timeframes', 0)}
• Overall Sentiment: {market_overview.get('overall_sentiment', 'neutral').title()}
• Consensus Strength: {market_overview.get('consensus_strength', 0):.1%}
• Average RSI: {market_overview.get('average_rsi', 50):.1f}
• RSI Condition: {market_overview.get('rsi_condition', 'neutral').title()}

Please provide a comprehensive analysis covering:

1. **EXECUTIVE SUMMARY**: Brief overview of current market condition and main signal

2. **TECHNICAL ANALYSIS DEEP DIVE**:
   - Key technical indicators interpretation
   - Multi-timeframe alignment analysis
   - Support and resistance level significance
   - Volume analysis and confirmation signals

3. **MARKET SENTIMENT & MOMENTUM**:
   - Overall market sentiment assessment
   - Momentum indicators analysis
   - Timeframe consensus interpretation

4. **TRADING SIGNAL RECOMMENDATION**:
   - Clear BUY/SELL/HOLD recommendation with confidence level
   - Detailed reasoning for the signal
   - Key factors supporting the decision

5. **ENTRY & EXIT STRATEGY**:
   - Optimal entry price levels and timing
   - Stop loss placement with risk management
   - Take profit targets with profit potential
   - Risk/reward ratio analysis

6. **RISK ASSESSMENT**:
   - Current market risks and uncertainties
   - Volatility considerations
   - Potential market scenarios (bull/bear cases)

7. **TIME HORIZON OUTLOOK**:
   - Short-term outlook (1-7 days)
   - Medium-term outlook (1-4 weeks)
   - Key levels to watch

8. **MARKET CONTEXT**:
   - Broader market conditions impact
   - Any notable market events or catalysts
   - Correlation with major assets

Please provide a comprehensive, professional analysis in clear, structured format. Be specific with price levels, percentages, and timeframes. This analysis is for educational and informational purposes only.

DATA SOURCE: Binance Public API (Real-time market data, no user credentials required)
"""
            
            # Convert our analysis to timeframes data format expected by LLM service
            # We need to provide actual historical OHLCV data, not just single price points
            timeframes_data = {}
            
            # Get the raw data we crawled earlier which contains proper OHLCV arrays
            raw_data = getattr(self, '_last_crawled_data', {})
            
            if raw_data:
                # Use the actual OHLCV data we crawled
                for timeframe in self.timeframes:
                    if timeframe in raw_data:
                        data = raw_data[timeframe]
                        
                        # Handle DataFrame or list data
                        if isinstance(data, pd.DataFrame) and not data.empty and len(data) > 0:
                            # Convert DataFrame to list of OHLCV dicts
                            ohlcv_data = []
                            for idx, row in data.iterrows():
                                ohlcv_data.append({
                                    'timestamp': int(row.name.timestamp() * 1000) if hasattr(row.name, 'timestamp') else int(datetime.now().timestamp() * 1000),
                                    'open': float(row.get('open', current_price)),
                                    'high': float(row.get('high', current_price)),
                                    'low': float(row.get('low', current_price)),
                                    'close': float(row.get('close', current_price)),
                                    'volume': float(row.get('volume', 0))
                                })
                            timeframes_data[timeframe] = ohlcv_data
                        elif isinstance(data, list) and len(data) > 0:
                            # Data is already in list format (from Binance API)
                            ohlcv_data = []
                            for candle in data:
                                if isinstance(candle, list) and len(candle) >= 6:
                                    # Binance format: [timestamp, open, high, low, close, volume, ...]
                                    ohlcv_data.append({
                                        'timestamp': int(candle[0]),
                                        'open': float(candle[1]),
                                        'high': float(candle[2]),
                                        'low': float(candle[3]),
                                        'close': float(candle[4]),
                                        'volume': float(candle[5])
                                    })
                                elif isinstance(candle, dict):
                                    # Already in dict format
                                    ohlcv_data.append({
                                        'timestamp': int(candle.get('timestamp', datetime.now().timestamp() * 1000)),
                                        'open': float(candle.get('open', current_price)),
                                        'high': float(candle.get('high', current_price)),
                                        'low': float(candle.get('low', current_price)),
                                        'close': float(candle.get('close', current_price)),
                                        'volume': float(candle.get('volume', 0))
                                    })
                            timeframes_data[timeframe] = ohlcv_data
                        else:
                            # Fallback: create synthetic data with current price
                            timeframes_data[timeframe] = self._create_synthetic_ohlcv(current_price, 50)
                    else:
                        # Fallback: create synthetic data
                        timeframes_data[timeframe] = self._create_synthetic_ohlcv(current_price, 50)
            else:
                # Fallback: create synthetic data for all timeframes
                for timeframe in self.timeframes:
                    timeframes_data[timeframe] = self._create_synthetic_ohlcv(current_price, 50)
            
            # Get LLM response using correct method
            # Extract indicators analysis from multi_timeframe data
            indicators_analysis = analysis.get('multi_timeframe', {})
            
            # Fetch historical transactions for learning (if enabled)
            historical_transactions = None
            if hasattr(self, 'historical_learning_enabled') and self.historical_learning_enabled:
                try:
                    transaction_service = TransactionService()
                    historical_transactions = transaction_service.get_recent_transactions_for_learning(
                        bot_id=self.bot_id if hasattr(self, 'bot_id') else None,
                        limit=getattr(self, 'historical_transaction_limit', 25),
                        include_failed=getattr(self, 'include_failed_trades', True),
                        mode=getattr(self, 'learning_mode', 'recent')
                    )
                    
                    if historical_transactions:
                        logger.info(f"📚 Loaded {len(historical_transactions)} historical transactions for learning")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to fetch historical transactions: {e}")
                    historical_transactions = None
            
            llm_response = await self.llm_service.analyze_market(
                symbol=analysis.get('symbol', self.trading_pair),
                timeframes_data=timeframes_data,
                indicators_analysis=indicators_analysis,  # ✅ Pass indicators to LLM
                model=self.llm_model,
                bot_id=self.bot_id if hasattr(self, 'bot_id') else None,
                historical_transactions=historical_transactions  # ✅ Pass historical learning data
            )
            
            # Extract ONLY recommendation from LLM response
            if isinstance(llm_response, dict):
                if 'error' in llm_response:
                    return f"LLM analysis error: {llm_response['error']}"
                elif 'recommendation' in llm_response:
                    # Return only the recommendation part, formatted concisely
                    rec = llm_response['recommendation']
                    return f"Action: {rec.get('action', 'HOLD')} | Confidence: {rec.get('confidence', 'N/A')}% | Reasoning: {rec.get('reasoning', 'N/A')[:100]}..."
                else:
                    return "LLM recommendation not found in response"
            elif isinstance(llm_response, str):
                return llm_response[:200] + "..." if len(llm_response) > 200 else llm_response
            else:
                return "LLM Analysis completed"
                
        except Exception as e:
            logger.error(f"❌ LLM analysis error: {e}")
            return f"LLM analysis error: {str(e)}"
    
    async def setup_position(self, signal: Action, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Process signal for signals bot - NO ACTUAL TRADING"""
        try:
            current_price = analysis.get('current_price', 0)
            primary_analysis = analysis.get('primary_analysis', {})
            indicators = primary_analysis.get('indicators', {})
            support_resistance = primary_analysis.get('support_resistance', {})
            ticker_24hr = analysis.get('ticker_24hr', {})
            
            # Calculate suggested levels
            entry_price = current_price
            stop_loss = None
            take_profit = None
            risk_reward_ratio = None
            
            if signal.action == "BUY":
                # For buy signals, place stop loss below support
                stop_loss = support_resistance.get('support', current_price * 0.98)
                take_profit = current_price * 1.04  # 4% profit target
                
                if stop_loss and stop_loss < current_price:
                    risk_reward_ratio = abs((take_profit - entry_price) / (entry_price - stop_loss))
                
            elif signal.action == "SELL":
                # For sell signals, place stop loss above resistance
                stop_loss = support_resistance.get('resistance', current_price * 1.02)
                take_profit = current_price * 0.96  # 4% profit target
                
                if stop_loss and stop_loss > current_price:
                    risk_reward_ratio = abs((take_profit - entry_price) / (stop_loss - entry_price))
            
            # Get LLM analysis if enabled
            full_analysis = signal.recommendation
            if self.use_llm_analysis and self.llm_service:
                try:
                    logger.info("🤖 Getting LLM analysis...")
                    llm_analysis = await self.get_llm_analysis(analysis)
                    full_analysis = llm_analysis
                    logger.info("✅ LLM analysis completed")
                except Exception as e:
                    logger.warning(f"⚠️ LLM analysis failed: {e}")
                    full_analysis = f"{signal.recommendation}. LLM analysis unavailable: {e}"
            else:
                # Create detailed technical analysis when LLM not available
                full_analysis = self.create_technical_summary(analysis, signal.action, signal.value)
            
            # Create comprehensive signal result
            result = {
                'status': 'signal_generated',
                'signal_type': 'trading_signal',
                'data_source': 'binance_public_api',
                'authentication_required': False,
                
                # Basic signal info
                'symbol': self.trading_pair,
                'action': signal.action,
                'confidence': f"{signal.value * 100:.1f}%",
                'confidence_raw': signal.value,
                'signal_strength': 'Strong' if signal.value >= self.strong_signal_threshold else 'Moderate' if signal.value >= self.min_confidence else 'Weak',
                
                # Price and levels
                'current_price': current_price,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward_ratio': risk_reward_ratio,
                
                # Analysis
                'reason': signal.reason,
                'full_analysis': full_analysis,
                
                # Market data
                'market_data': {
                    'price_24h_change': ticker_24hr.get('price_change_percent', 0),
                    'volume_24h': ticker_24hr.get('volume', 0),
                    'high_24h': ticker_24hr.get('high_price', 0),
                    'low_24h': ticker_24hr.get('low_price', 0)
                },
                
                # Technical indicators
                'indicators': {
                    'rsi': indicators.get('rsi'),
                    'macd': indicators.get('macd'),
                    'sma_20': indicators.get('sma_20'),
                    'sma_50': indicators.get('sma_50'),
                    'ema_12': indicators.get('ema_12'),
                    'ema_26': indicators.get('ema_26'),
                    'bollinger_bands': indicators.get('bollinger_bands')
                },
                
                # Support/Resistance
                'support_resistance': support_resistance,
                
                # Market overview
                'market_overview': analysis.get('market_overview', {}),
                
                # Metadata
                'timeframes_analyzed': self.timeframes,
                'primary_timeframe': self.primary_timeframe,
                'timestamp': datetime.now().isoformat(),
                'user_principal_id': self.user_principal_id,
                'bot_type': 'signals_bot',
                
                # Disclaimers
                'warnings': [
                    '⚠️ THIS IS A SIGNAL ONLY - NO ACTUAL TRADING PERFORMED',
                    '📚 For educational and informational purposes only',
                    '⚖️ Always conduct your own research and risk management',
                    '🔍 Past performance does not guarantee future results'
                ],
                
                'note': 'This analysis uses public market data and does not require user API keys'
            }
            
            logger.info(f"🔮 Signal processed successfully: {signal.action} with {signal.value:.1%} confidence")
            if stop_loss and take_profit:
                logger.info(f"📊 Levels - Entry: ${entry_price:.2f}, SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}")
                if risk_reward_ratio:
                    logger.info(f"⚖️ Risk/Reward Ratio: {risk_reward_ratio:.2f}:1")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing signal: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def save_transaction_to_db(self, result: Dict[str, Any]) -> None:
        """Save signal to log for tracking - NO DATABASE REQUIRED"""
        try:
            # For signals bot, just log the signal
            signal_log = {
                'timestamp': result.get('timestamp'),
                'symbol': result.get('symbol'),
                'action': result.get('action'),
                'confidence': result.get('confidence_raw'),
                'entry_price': result.get('entry_price'),
                'reason': result.get('reason'),
                'user_principal_id': self.user_principal_id,
                'bot_type': 'signals_bot',
                'data_source': 'public_api'
            }
            
            logger.info(f"📝 Signal logged: {json.dumps(signal_log, indent=2)}")
            
            # TODO: Could implement file-based logging or database saving if needed
            # For now, just console logging is sufficient
            
        except Exception as e:
            logger.error(f"❌ Error saving signal log: {e}")
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Execute algorithm - Required by CustomBot abstract class
        This method integrates with the bot SDK framework
        """
        try:
            logger.info(f"🤖 Executing signals algorithm for {timeframe}")
            
            # Convert DataFrame to our format if needed
            if data is None or data.empty:
                return Action("HOLD", 0.0, "No data provided")
            
            # For signals bot, we'll use our existing analysis pipeline
            # Convert DataFrame to our expected format
            timeframe_data = {}
            
            # Check if data has the expected columns
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in data.columns for col in required_columns):
                logger.warning("⚠️ Data missing required columns, using crawl_data() instead")
                # Fall back to our public API crawling
                multi_timeframe_data = self.crawl_data()
                analysis = self.analyze_data(multi_timeframe_data)
                return self.generate_signal(analysis)
            
            # Convert DataFrame to our format
            candles = []
            for _, row in data.iterrows():
                candles.append({
                    'timestamp': int(row['timestamp']) if 'timestamp' in row else int(datetime.now().timestamp() * 1000),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']) if 'volume' in row else 0.0
                })
            
            timeframe_data[timeframe] = candles
            
            # Get current price (last close price)
            current_price = float(data['close'].iloc[-1]) if len(data) > 0 else 0.0
            
            # Create analysis data structure
            multi_timeframe_data = {
                'timeframes': timeframe_data,
                'current_price': current_price,
                'timestamp': datetime.now().isoformat(),
                'symbol': self.trading_pair,
                'data_source': 'sdk_integration'
            }
            
            # Run our analysis pipeline
            analysis = self.analyze_data(multi_timeframe_data)
            signal = self.generate_signal(analysis)
            
            logger.info(f"✅ Algorithm executed: {signal.action} ({signal.value:.1%})")
            return signal
            
        except Exception as e:
            logger.error(f"❌ Error in execute_algorithm: {e}")
            return Action("HOLD", 0.0, f"Algorithm execution error: {str(e)}")

# Test execution
async def main_execution():
    """Test the Binance Signals Bot - NO USER API KEYS REQUIRED"""
    
    # Test configuration - NO USER PRINCIPAL REQUIRED
    test_config = {
        'trading_pair': 'BTCUSDT',
        'testnet': True,
        'timeframes': ['1h', '4h', '1d'],
        'primary_timeframe': '1h',
        'use_llm_analysis': True,  # Set to False if no LLM API keys
        'llm_model': 'openai',
        'min_confidence': 0.6,
        'strong_signal_threshold': 0.8,
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70
    }
    
    # LLM API keys from environment (optional)
    llm_api_keys = {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'google_api_key': os.getenv('GOOGLE_API_KEY')
    }
    
    print("🔮 BINANCE SIGNALS BOT - PUBLIC API VERSION")
    print("=" * 60)
    print(f"🤖 LLM Model: {test_config['llm_model']}")
    print(f"💱 Trading Pair: {test_config['trading_pair']}")
    print(f"📊 Timeframes: {test_config['timeframes']}")
    print(f"🎯 Primary Timeframe: {test_config['primary_timeframe']}")
    print(f"🧪 Environment: {'TESTNET' if test_config['testnet'] else 'PRODUCTION'}")
    print("🔓 NO USER API KEYS REQUIRED")
    print("📡 USING BINANCE PUBLIC ENDPOINTS ONLY")
    print("⚠️ SIGNALS ONLY - NO TRADING PERFORMED")
    print("=" * 60)
    
    # Initialize signals bot
    print("\n🔮 Initializing Signals Bot...")
    
    try:
        # No user_principal_id required!
        bot = BinanceSignalsBot(test_config, api_keys=llm_api_keys, user_principal_id="test_user")
        print("✅ Signals Bot initialized successfully!")
        print("🔓 No user credentials required - using public market data only")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print("\n📝 Common issues:")
        print("   1. Check internet connection")
        print("   2. Verify Binance API endpoints are accessible")
        print("   3. For LLM analysis, set environment variables (optional):")
        print("      - OPENAI_API_KEY for OpenAI GPT")
        print("      - ANTHROPIC_API_KEY for Claude")
        print("      - GOOGLE_API_KEY for Gemini")
        return
    
    # Test the complete signals generation cycle
    try:
        print("\n🔄 Running complete signals generation cycle...")
        
        # 1. Crawl multi-timeframe data from public API
        print("\n" + "=" * 60)
        print("📊 Step 1: Crawling public market data...")
        multi_timeframe_data = bot.crawl_data()
        
        if 'error' in multi_timeframe_data:
            print(f"❌ Failed to crawl data: {multi_timeframe_data['error']}")
            return
        
        timeframes_crawled = list(multi_timeframe_data.get('timeframes', {}).keys())
        print(f"✅ Successfully crawled {len(timeframes_crawled)} timeframes: {timeframes_crawled}")
        print(f"💰 Current price: ${multi_timeframe_data.get('current_price', 0):,.2f}")
        
        if multi_timeframe_data.get('ticker_24hr'):
            ticker = multi_timeframe_data['ticker_24hr']
            print(f"📈 24h change: {ticker.get('price_change_percent', 0):+.2f}%")
            print(f"📊 24h volume: {ticker.get('volume', 0):,.0f}")
        
        # 2. Analyze multi-timeframe data
        print("\n🔍 Step 2: Analyzing market data with technical indicators...")
        analysis = bot.analyze_data(multi_timeframe_data)
        
        if 'error' in analysis:
            print(f"❌ Analysis error: {analysis['error']}")
            return
        
        print(f"✅ Technical analysis completed for {len(analysis.get('multi_timeframe', {}))} timeframes")
        market_overview = analysis.get('market_overview', {})
        print(f"📊 Market sentiment: {market_overview.get('overall_sentiment', 'neutral').upper()}")
        print(f"🎯 Consensus strength: {market_overview.get('consensus_strength', 0):.1%}")
        
        # 3. Generate trading signal
        print("\n🔮 Step 3: Generating trading signal...")
        signal = bot.generate_signal(analysis)
        
        print(f"✅ Signal generated: {signal.action} with {signal.value:.1%} confidence")
        print(f"📝 Primary reasons: {signal.reason}")
        
        # 4. Process signal information
        print("\n📋 Step 4: Processing signal information...")
        signal_result = await bot.setup_position(signal, analysis)
        
        # 5. Log signal
        if signal_result.get('status') == 'signal_generated':
            bot.save_transaction_to_db(signal_result)
        
        # Create final result summary
        final_result = {
            'bot_info': {
                'name': 'BinanceSignalsBot',
                'version': 'public_api_v1.0',
                'data_source': 'binance_public_endpoints',
                'authentication_required': False
            },
            'market_summary': {
                'symbol': bot.trading_pair,
                'current_price': analysis.get('current_price'),
                'timeframes_analyzed': len(timeframes_crawled),
                'timeframes': timeframes_crawled,
                'primary_timeframe': bot.primary_timeframe,
                'market_sentiment': market_overview.get('overall_sentiment', 'neutral'),
                'consensus_strength': f"{market_overview.get('consensus_strength', 0):.1%}"
            },
            'signal_summary': {
                'action': signal.action,
                'confidence': f"{signal.value:.1%}",
                'strength': signal_result.get('signal_strength', 'Unknown'),
                'entry_price': signal_result.get('entry_price'),
                'stop_loss': signal_result.get('stop_loss'),
                'take_profit': signal_result.get('take_profit'),
                'risk_reward': signal_result.get('risk_reward_ratio')
            },
            'full_signal_data': signal_result,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n🔮 SIGNALS BOT EXECUTION COMPLETED")
        print("=" * 60)
        print("📋 SUMMARY:")
        print(f"   Symbol: {final_result['market_summary']['symbol']}")
        print(f"   Signal: {final_result['signal_summary']['action']} ({final_result['signal_summary']['confidence']})")
        print(f"   Strength: {final_result['signal_summary']['strength']}")
        print(f"   Entry: ${final_result['signal_summary']['entry_price']:,.2f}")
        print(f"   Stop Loss: ${final_result['signal_summary']['stop_loss']:,.2f}")
        print(f"   Take Profit: ${final_result['signal_summary']['take_profit']:,.2f}")
        if final_result['signal_summary']['risk_reward']:
            print(f"   Risk/Reward: {final_result['signal_summary']['risk_reward']:.2f}:1")
        print(f"   Market Sentiment: {final_result['market_summary']['market_sentiment'].upper()}")
        print("=" * 60)
        
        # Print detailed analysis if available
        if signal_result.get('full_analysis'):
            print(f"\n📖 DETAILED ANALYSIS:")
            print("=" * 60)
            print(signal_result['full_analysis'])
            print("=" * 60)
        
        # Final JSON output for integration
        print(f"\n📄 FULL RESULT (JSON):")
        print(json.dumps(final_result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Error during signals generation: {e}")
        import traceback
        traceback.print_exc()

# Factory function for production use
def create_signals_bot_for_user(config: Dict[str, Any] = None, llm_api_keys: Dict[str, str] = None) -> 'BinanceSignalsBot':
    """
    Factory function to create BinanceSignalsBot - NO USER CREDENTIALS REQUIRED
    
    Args:
        config: Bot configuration (optional)
        llm_api_keys: LLM API keys for enhanced analysis (optional)
        
    Returns:
        Configured BinanceSignalsBot instance
    """
    default_config = {
        'trading_pair': 'BTCUSDT',
        'testnet': True,  # Default to testnet for safety
        'timeframes': ['1h', '4h', '1d'],
        'primary_timeframe': '1h',
        'use_llm_analysis': bool(llm_api_keys),  # Enable LLM if keys provided
        'llm_model': 'openai',
        'min_confidence': 0.6,
        'strong_signal_threshold': 0.8,
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70
    }
    
    # Merge with provided config
    if config:
        default_config.update(config)
    
    # Create signals bot without user principal requirement
    return BinanceSignalsBot(default_config, api_keys=llm_api_keys)

if __name__ == "__main__":
    asyncio.run(main_execution())

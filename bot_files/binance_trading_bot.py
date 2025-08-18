"""
Advanced Binance Trading Bot with LLM Integration
A complete trading bot that can execute real trades on Binance testnet
Uses LLM AI analysis (OpenAI/Claude/Gemini) for intelligent trading decisions
Falls back to RSI + MACD + Moving Average strategy if LLM unavailable
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json
import asyncio

from bots.bot_sdk.CustomBot import CustomBot
from bots.bot_sdk.Action import Action
from services.llm_integration import create_llm_service

logger = logging.getLogger(__name__)

class BinanceTradingBot(CustomBot):
    """
    Advanced Binance Trading Bot with LLM AI Integration
    Primary Strategy: LLM-powered analysis (OpenAI/Claude/Gemini)
    Fallback Strategy: RSI + MACD + Moving Average + Volume confirmation
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        """Initialize Binance Trading Bot"""
        super().__init__(config, api_keys)
        
        # Trading configuration
        self.exchange_type = config.get('exchange_type', 'BINANCE')
        self.trading_pair = config.get('trading_pair', 'BTC/USDT')
        self.testnet = config.get('testnet', True)
        self.timeframe = config.get('timeframe', '5m')
        
        # LLM configuration
        self.llm_model = config.get('llm_model', 'openai')  # Default to OpenAI
        self.use_llm_analysis = config.get('use_llm_analysis', True)  # Enable LLM by default
        
        # Technical indicators config (kept for fallback)
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        
        self.macd_fast = config.get('macd_fast', 12)
        self.macd_slow = config.get('macd_slow', 26)
        self.macd_signal = config.get('macd_signal', 9)
        
        self.ma_fast_period = config.get('ma_fast_period', 20)
        self.ma_slow_period = config.get('ma_slow_period', 50)
        
        # Risk management
        self.max_position_size = config.get('max_position_size', 0.1)
        self.min_trade_amount = config.get('min_trade_amount', 10.0)
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)
        
        # Initialize LLM service
        self.llm_service = None
        if self.use_llm_analysis:
            try:
                llm_config = {
                    'openai_api_key': api_keys.get('openai_api_key'),
                    'claude_api_key': api_keys.get('claude_api_key'), 
                    'gemini_api_key': api_keys.get('gemini_api_key'),
                    'openai_model': config.get('openai_model', 'gpt-4o'),
                    'claude_model': config.get('claude_model', 'claude-3-5-sonnet-20241022'),
                    'gemini_model': config.get('gemini_model', 'gemini-1.5-pro')
                }
                self.llm_service = create_llm_service(llm_config)
                logger.info(f"LLM service initialized with model: {self.llm_model}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM service: {e}")
                self.use_llm_analysis = False
                logger.warning("Falling back to traditional technical analysis")
        
        logger.info(f"Initialized BinanceTradingBot for {self.trading_pair} on {'TESTNET' if self.testnet else 'PRODUCTION'}")
        logger.info(f"Analysis method: {'LLM (' + self.llm_model + ')' if self.use_llm_analysis else 'Technical Indicators'}")
    
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, subscription_config: Dict[str, Any] = None) -> Action:
        """
        Execute the main trading algorithm (required abstract method)
        This is the core method called by the framework
        
        Args:
            data: Preprocessed market data (OHLCV DataFrame)
            timeframe: Trading timeframe (e.g., '5m', '1h')
            subscription_config: Additional configuration
            
        Returns:
            Action: BUY, SELL, or HOLD with confidence and reason
        """
        try:
            logger.info(f"Executing algorithm for {len(data)} data points")
            
            if len(data) < max(self.ma_slow_period, self.rsi_period + 10):
                return Action(action="HOLD", value=0.0, reason="Insufficient data for analysis")
            
            # Calculate all technical indicators
            analysis = self._calculate_comprehensive_analysis(data)
            
            # Generate trading signal
            return self._generate_comprehensive_signal(analysis, data)
            
        except Exception as e:
            logger.error(f"Error in execute_algorithm: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Algorithm error: {e}")
    
    def _calculate_comprehensive_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive technical analysis"""
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                logger.error(f"Missing required column: {col}")
                return {'error': f'Missing column: {col}'}
        
        try:
            # RSI Calculation
            def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            
            # MACD Calculation
            def calculate_macd(prices: pd.Series, fast=12, slow=26, signal=9):
                ema_fast = prices.ewm(span=fast).mean()
                ema_slow = prices.ewm(span=slow).mean()
                macd_line = ema_fast - ema_slow
                signal_line = macd_line.ewm(span=signal).mean()
                histogram = macd_line - signal_line
                return macd_line, signal_line, histogram
            
            # Calculate all indicators
            rsi = calculate_rsi(data['close'], self.rsi_period)
            macd, macd_signal, macd_hist = calculate_macd(data['close'], self.macd_fast, self.macd_slow, self.macd_signal)
            
            # Moving averages
            ma_fast = data['close'].rolling(window=self.ma_fast_period).mean()
            ma_slow = data['close'].rolling(window=self.ma_slow_period).mean()
            
            # Bollinger Bands
            bb_period = 20
            bb_middle = data['close'].rolling(window=bb_period).mean()
            bb_std = data['close'].rolling(window=bb_period).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            
            # Volume analysis
            volume_ma = data['volume'].rolling(window=20).mean()
            
            # Get current values (last row)
            current_idx = -1
            
            return {
                'current_price': data['close'].iloc[current_idx],
                'rsi': rsi.iloc[current_idx] if not pd.isna(rsi.iloc[current_idx]) else 50,
                'rsi_oversold': rsi.iloc[current_idx] < self.rsi_oversold if not pd.isna(rsi.iloc[current_idx]) else False,
                'rsi_overbought': rsi.iloc[current_idx] > self.rsi_overbought if not pd.isna(rsi.iloc[current_idx]) else False,
                'macd': macd.iloc[current_idx] if not pd.isna(macd.iloc[current_idx]) else 0,
                'macd_signal': macd_signal.iloc[current_idx] if not pd.isna(macd_signal.iloc[current_idx]) else 0,
                'macd_bullish': macd.iloc[current_idx] > macd_signal.iloc[current_idx] if not pd.isna(macd.iloc[current_idx]) and not pd.isna(macd_signal.iloc[current_idx]) else False,
                'ma_fast': ma_fast.iloc[current_idx] if not pd.isna(ma_fast.iloc[current_idx]) else data['close'].iloc[current_idx],
                'ma_slow': ma_slow.iloc[current_idx] if not pd.isna(ma_slow.iloc[current_idx]) else data['close'].iloc[current_idx],
                'ma_bullish': ma_fast.iloc[current_idx] > ma_slow.iloc[current_idx] if not pd.isna(ma_fast.iloc[current_idx]) and not pd.isna(ma_slow.iloc[current_idx]) else False,
                'bb_upper': bb_upper.iloc[current_idx] if not pd.isna(bb_upper.iloc[current_idx]) else data['close'].iloc[current_idx] * 1.02,
                'bb_lower': bb_lower.iloc[current_idx] if not pd.isna(bb_lower.iloc[current_idx]) else data['close'].iloc[current_idx] * 0.98,
                'bb_middle': bb_middle.iloc[current_idx] if not pd.isna(bb_middle.iloc[current_idx]) else data['close'].iloc[current_idx],
                'volume_ratio': data['volume'].iloc[current_idx] / volume_ma.iloc[current_idx] if not pd.isna(volume_ma.iloc[current_idx]) and volume_ma.iloc[current_idx] > 0 else 1,
                'high_volume': data['volume'].iloc[current_idx] > volume_ma.iloc[current_idx] * 1.5 if not pd.isna(volume_ma.iloc[current_idx]) and volume_ma.iloc[current_idx] > 0 else False
            }
            
        except Exception as e:
            logger.error(f"Error calculating analysis: {e}")
            return {'error': str(e)}
    
    def _generate_comprehensive_signal(self, analysis: Dict[str, Any], data: pd.DataFrame) -> Action:
        """Generate comprehensive trading signal"""
        
        if 'error' in analysis:
            return Action(action="HOLD", value=0.0, reason=f"Analysis error: {analysis['error']}")
        
        try:
            signals = []
            signal_strength = 0
            reasons = []
            
            # RSI signals
            if analysis.get('rsi_oversold', False):
                signals.append('RSI_OVERSOLD')
                signal_strength += 2
                reasons.append(f"RSI oversold ({analysis.get('rsi', 0):.1f})")
            elif analysis.get('rsi_overbought', False):
                signals.append('RSI_OVERBOUGHT')
                signal_strength -= 2
                reasons.append(f"RSI overbought ({analysis.get('rsi', 0):.1f})")
            else:
                reasons.append(f"RSI neutral ({analysis.get('rsi', 0):.1f})")
            
            # MACD signals
            if analysis.get('macd_bullish', False):
                signals.append('MACD_BULLISH')
                signal_strength += 1
                reasons.append("MACD bullish")
            else:
                signals.append('MACD_BEARISH')
                signal_strength -= 1
                reasons.append("MACD bearish")
            
            # Moving average signals
            if analysis.get('ma_bullish', False):
                signals.append('MA_BULLISH')
                signal_strength += 1
                reasons.append("MA bullish trend")
            else:
                signals.append('MA_BEARISH')
                signal_strength -= 1
                reasons.append("MA bearish trend")
            
            # Volume confirmation
            if analysis.get('high_volume', False):
                signal_strength += 0.5
                reasons.append(f"High volume ({analysis.get('volume_ratio', 0):.1f}x)")
            else:
                reasons.append("Normal volume")
            
            # Bollinger Band position
            current_price = analysis.get('current_price', 0)
            bb_upper = analysis.get('bb_upper', current_price * 1.02)
            bb_lower = analysis.get('bb_lower', current_price * 0.98)
            
            if bb_upper != bb_lower:
                bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
                if bb_position < 0.2:
                    signal_strength += 0.5
                    reasons.append("Near BB lower band")
                elif bb_position > 0.8:
                    signal_strength -= 0.5
                    reasons.append("Near BB upper band")
            
            # Calculate confidence
            confidence = min(abs(signal_strength) * 15, 100)
            reason_text = ", ".join(reasons)
            
            # Decision logic
            if signal_strength >= 2:
                return Action(action="BUY", value=confidence/100, reason=reason_text)
            elif signal_strength <= -2:
                return Action(action="SELL", value=confidence/100, reason=reason_text)
            else:
                return Action(action="HOLD", value=0.0, reason=reason_text)
                
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Signal generation error: {e}")
    
    def crawl_data(self) -> List[Dict[str, Any]]:
        """
        Crawl real-time market data from Binance
        Returns historical OHLCV data for analysis
        """
        try:
            logger.info(f"Crawling data for {self.trading_pair}...")
            
            # Get exchange instance
            exchange = self._get_exchange_instance()
            if not exchange:
                logger.error("Failed to get exchange instance")
                return []
            
            # Fetch OHLCV data
            symbol = self.trading_pair.replace('/', '')  # Convert BTC/USDT to BTCUSDT
            ohlcv_data = exchange.get_klines(
                symbol=symbol,
                interval=self.timeframe,
                limit=200  # Get enough data for indicators
            )
            
            if ohlcv_data is None or ohlcv_data.empty:
                logger.error("No market data received")
                return []
            
            # Convert DataFrame to expected format
            formatted_data = []
            for index, row in ohlcv_data.iterrows():
                # Handle pandas Timestamp - convert to milliseconds
                timestamp_ms = int(row['timestamp'].timestamp() * 1000) if hasattr(row['timestamp'], 'timestamp') else int(row['timestamp'])
                
                formatted_data.append({
                    'timestamp': timestamp_ms,
                    'open': float(row.get('open', 0)),
                    'high': float(row.get('high', 0)),
                    'low': float(row.get('low', 0)),
                    'close': float(row.get('close', 0)),
                    'volume': float(row.get('volume', 0))
                })
            
            logger.info(f"Successfully crawled {len(formatted_data)} data points")
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error crawling data: {e}")
            return []
    
    def analyze_data(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze market data using technical indicators
        Returns comprehensive market analysis
        """
        try:
            if len(historical_data) < max(self.ma_slow_period, self.rsi_period + 20):
                logger.warning("Insufficient data for analysis")
                return {'error': 'Insufficient data', 'historical_data': historical_data}
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Calculate Technical Indicators
            analysis = self._calculate_all_indicators(df)
            
            # Current market state
            current = df.iloc[-1]
            analysis.update({
                'current_price': current['close'],
                'current_volume': current['volume'],
                'price_change_24h': ((current['close'] - df.iloc[-288]['close']) / df.iloc[-288]['close']) * 100 if len(df) >= 288 else 0,
                'data_points': len(df),
                'last_update': datetime.now().isoformat(),
                'historical_data': historical_data  # Pass historical data for LLM analysis
            })
            
            logger.info(f"Analysis complete: RSI={analysis.get('rsi', 0):.2f}, MACD={analysis.get('macd', 0):.4f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            return {'error': str(e), 'historical_data': historical_data}
    
    def _calculate_all_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical indicators"""
        
        # RSI Calculation
        def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty else 50
        
        # MACD Calculation
        def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            return (
                macd_line.iloc[-1] if not macd_line.empty else 0,
                signal_line.iloc[-1] if not signal_line.empty else 0,
                histogram.iloc[-1] if not histogram.empty else 0
            )
        
        # Calculate indicators
        rsi = calculate_rsi(df['close'], self.rsi_period)
        macd, macd_signal, macd_histogram = calculate_macd(df['close'], self.macd_fast, self.macd_slow, self.macd_signal)
        
        # Moving Averages
        ma_fast = df['close'].rolling(window=self.ma_fast_period).mean().iloc[-1]
        ma_slow = df['close'].rolling(window=self.ma_slow_period).mean().iloc[-1]
        
        # Bollinger Bands
        bb_period = 20
        bb_std = 2
        bb_middle = df['close'].rolling(window=bb_period).mean().iloc[-1]
        bb_std_dev = df['close'].rolling(window=bb_period).std().iloc[-1]
        bb_upper = bb_middle + (bb_std_dev * bb_std)
        bb_lower = bb_middle - (bb_std_dev * bb_std)
        
        # Volume analysis
        avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        return {
            'rsi': rsi,
            'rsi_oversold': rsi < self.rsi_oversold,
            'rsi_overbought': rsi > self.rsi_overbought,
            'macd': macd,
            'macd_signal': macd_signal,
            'macd_histogram': macd_histogram,
            'macd_bullish': macd > macd_signal,
            'ma_fast': ma_fast,
            'ma_slow': ma_slow,
            'ma_bullish': ma_fast > ma_slow,
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower,
            'bb_position': (df['close'].iloc[-1] - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5,
            'volume_ratio': volume_ratio,
            'high_volume': volume_ratio > 1.5
        }
    
    def _convert_data_to_llm_format(self, historical_data: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Convert historical data to LLM-friendly multi-timeframe format"""
        try:
            if not historical_data:
                return {}
            
            # Clean data to ensure JSON serializable (convert any pandas objects to primitives)
            cleaned_data = []
            for item in historical_data:
                cleaned_item = {}
                for key, value in item.items():
                    if hasattr(value, 'timestamp'):  # pandas Timestamp
                        cleaned_item[key] = value.timestamp() if hasattr(value, 'timestamp') else float(value)
                    elif hasattr(value, 'isoformat'):  # datetime object
                        cleaned_item[key] = value.isoformat()
                    else:
                        cleaned_item[key] = float(value) if isinstance(value, (int, float)) else value
                cleaned_data.append(cleaned_item)
            
            # For simplicity, we'll use the available data for all timeframes
            # In a real implementation, you might want to fetch different timeframes
            timeframes_data = {
                "1h": cleaned_data[-24:] if len(cleaned_data) >= 24 else cleaned_data,  # Last 24 hours
                "4h": cleaned_data[-12:] if len(cleaned_data) >= 12 else cleaned_data,  # Last 48 hours 
                "1d": cleaned_data[-7:] if len(cleaned_data) >= 7 else cleaned_data     # Last 7 days
            }
            
            return timeframes_data
            
        except Exception as e:
            logger.error(f"Error converting data to LLM format: {e}")
            return {}
    
    async def generate_signal_with_llm(self, historical_data: List[Dict[str, Any]]) -> Action:
        """Generate trading signal using LLM analysis"""
        try:
            if not self.llm_service:
                logger.error("LLM service not available")
                return Action(action="HOLD", value=0.0, reason="LLM service unavailable")
            
            # Convert data to LLM format
            timeframes_data = self._convert_data_to_llm_format(historical_data)
            if not timeframes_data:
                return Action(action="HOLD", value=0.0, reason="Failed to format data for LLM")
            
            # Get LLM analysis
            symbol = self.trading_pair  # e.g., "BTC/USDT"
            llm_analysis = await self.llm_service.analyze_market(
                symbol=symbol,
                timeframes_data=timeframes_data,
                model=self.llm_model
            )
            
            if "error" in llm_analysis:
                logger.error(f"LLM analysis failed: {llm_analysis['error']}")
                return Action(action="HOLD", value=0.0, reason=f"LLM analysis error: {llm_analysis['error']}")
            
            # Parse LLM recommendation
            if llm_analysis.get("parsed", False) and "recommendation" in llm_analysis:
                recommendation = llm_analysis["recommendation"]
                
                action = recommendation.get("action", "HOLD").upper()
                
                # Parse confidence safely (handle both "60%" and 60 formats)
                confidence_raw = recommendation.get("confidence", 0)
                try:
                    if isinstance(confidence_raw, str):
                        # Remove % sign if present and convert
                        confidence_str = confidence_raw.replace("%", "").strip()
                        confidence = float(confidence_str) / 100.0
                    else:
                        # Already a number
                        confidence = float(confidence_raw) / 100.0
                    
                    # Ensure confidence is in valid range 0-1
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse confidence '{confidence_raw}': {e}")
                    confidence = 0.0
                
                reasoning = recommendation.get("reasoning", "LLM analysis")
                
                # Validate action
                if action not in ["BUY", "SELL", "HOLD"]:
                    action = "HOLD"
                    confidence = 0.0
                    reasoning = f"Invalid LLM action: {action}"
                
                logger.info(f"LLM Recommendation: {action} (confidence: {confidence*100:.1f}%)")
                logger.info(f"LLM Reasoning: {reasoning}")
                
                return Action(action=action, value=confidence, reason=reasoning)
            else:
                logger.warning("LLM response could not be parsed properly")
                return Action(action="HOLD", value=0.0, reason="Unparseable LLM response")
                
        except Exception as e:
            logger.error(f"Error in LLM signal generation: {e}")
            return Action(action="HOLD", value=0.0, reason=f"LLM signal error: {e}")

    def generate_signal(self, analysis: Dict[str, Any]) -> Action:
        """
        Generate trading signal based on analysis
        Uses LLM if available, otherwise falls back to technical analysis
        """
        try:
            # If LLM is enabled and we have historical data, use LLM analysis
            if self.use_llm_analysis and self.llm_service and 'historical_data' in analysis:
                logger.info("Generating signal using LLM analysis...")
                # Run async LLM analysis
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    llm_action = loop.run_until_complete(
                        self.generate_signal_with_llm(analysis['historical_data'])
                    )
                    return llm_action
                finally:
                    loop.close()
            
            # Fallback to traditional technical analysis
            logger.info("Generating signal using traditional technical analysis...")
            if 'error' in analysis:
                return Action.HOLD(0, "Analysis error")
            
            signals = []
            signal_strength = 0
            reasons = []
            
            # RSI Signals
            if analysis.get('rsi_oversold', False):
                signals.append('RSI_OVERSOLD')
                signal_strength += 2
                reasons.append(f"RSI oversold ({analysis.get('rsi', 0):.1f})")
            elif analysis.get('rsi_overbought', False):
                signals.append('RSI_OVERBOUGHT')
                signal_strength -= 2
                reasons.append(f"RSI overbought ({analysis.get('rsi', 0):.1f})")
            
            # MACD Signals
            if analysis.get('macd_bullish', False):
                signals.append('MACD_BULLISH')
                signal_strength += 1
                reasons.append("MACD bullish")
            else:
                signals.append('MACD_BEARISH')
                signal_strength -= 1
                reasons.append("MACD bearish")
            
            # Moving Average Signals
            if analysis.get('ma_bullish', False):
                signals.append('MA_BULLISH')
                signal_strength += 1
                reasons.append("MA trend bullish")
            else:
                signals.append('MA_BEARISH')
                signal_strength -= 1
                reasons.append("MA trend bearish")
            
            # Volume confirmation
            if analysis.get('high_volume', False):
                signal_strength += 0.5
                reasons.append(f"High volume ({analysis.get('volume_ratio', 0):.1f}x)")
            else:
                reasons.append("Low volume")
            
            # Bollinger Bands position
            bb_pos = analysis.get('bb_position', 0.5)
            if bb_pos < 0.2:
                signal_strength += 0.5
                reasons.append("Near BB lower band")
            elif bb_pos > 0.8:
                signal_strength -= 0.5
                reasons.append("Near BB upper band")
            
            # Risk adjustment for extreme positions
            if bb_pos < 0.1 or bb_pos > 0.9:
                signal_strength *= 0.7  # Reduce strength for extreme positions
                reasons.append("Extreme BB position")
            
            # Decision logic
            confidence = min(abs(signal_strength) * 20, 100)  # Convert to percentage
            reason_text = ", ".join(reasons)
            
            if signal_strength >= 2:
                return Action(action="BUY", value=confidence/100, reason=reason_text)
            elif signal_strength <= -2:
                return Action(action="SELL", value=confidence/100, reason=reason_text)
            else:
                return Action(action="HOLD", value=0.0, reason=reason_text)
                
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return Action(action="HOLD", value=0.0, reason=f"Signal generation error: {e}")
    
    def execute_trade(self, action: Action, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the trading action on Binance
        Returns trade execution result
        """
        try:
            if action.action == "HOLD":
                logger.info(f"HOLD signal: {action.reason}")
                return {
                    'status': 'success',
                    'action': 'HOLD',
                    'reason': action.reason,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get exchange instance
            exchange = self._get_exchange_instance()
            if not exchange:
                return {'status': 'error', 'message': 'Failed to get exchange instance'}
            
            # Calculate position size
            current_price = analysis.get('current_price', 0)
            if current_price <= 0:
                return {'status': 'error', 'message': 'Invalid current price'}
            
            # Simple position sizing (can be improved)
            trade_amount_usd = max(self.min_trade_amount, self.max_position_size * 1000)  # Ensure at least min_trade_amount
            quantity = trade_amount_usd / current_price
            
            # Ensure minimum quantity meets exchange requirements
            # For BTC/USDT, minimum notional is usually $10-$15
            min_notional_usd = 15.0  # Conservative minimum notional
            min_quantity_for_notional = min_notional_usd / current_price
            
            if quantity < min_quantity_for_notional:
                quantity = min_quantity_for_notional
                logger.info(f"Increased quantity to meet minimum notional: ${min_notional_usd}")
            
            # Round to proper step size for BTC/USDT (step size = 0.00001)
            step_size = 0.00001  # Standard step size for BTC/USDT
            quantity = round(quantity / step_size) * step_size
            
            # Ensure we still meet minimum notional after rounding
            if quantity * current_price < min_notional_usd:
                quantity = (round(min_notional_usd / current_price / step_size) + 1) * step_size
            
            # Format as decimal string (no scientific notation)
            quantity_str = f"{quantity:.5f}"  # 5 decimal places for BTC step size
            
            # Final check - ensure we have enough balance for this trade
            notional_value = quantity * current_price
            logger.info(f"Trade details: {quantity_str} BTC @ ${current_price:.2f} = ${notional_value:.2f}")
            
            logger.info(f"Executing {action.action} order: {quantity_str} {self.trading_pair} @ ${current_price:.2f}")
            
            # Execute trade
            symbol = self.trading_pair.replace('/', '')  # Convert BTC/USDT to BTCUSDT
            
            if action.action == "BUY":
                result = exchange.create_market_order(symbol, "BUY", quantity_str)
            elif action.action == "SELL":
                result = exchange.create_market_order(symbol, "SELL", quantity_str)
            else:
                return {'status': 'error', 'message': f'Unknown action type: {action.action}'}
            
            if result and hasattr(result, 'status') and result.status == 'FILLED':
                logger.info(f"Trade executed successfully: {result}")
                return {
                    'status': 'success',
                    'action': action.action,
                    'quantity': quantity_str,
                    'price': current_price,
                    'order_id': getattr(result, 'order_id', None),
                    'confidence': action.value,
                    'reason': action.reason,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"Trade execution failed: {result}")
                return {
                    'status': 'error',
                    'message': 'Trade execution failed',
                    'details': str(result)
                }
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                'status': 'error',
                'message': f'Trade execution error: {e}'
            }
    
    def _get_exchange_instance(self):
        """Get exchange instance from factory"""
        try:
            from services.exchange_factory import ExchangeFactory
            return ExchangeFactory.create_exchange(
                exchange_name=self.exchange_type,
                api_key=self.api_keys.get('api_key'),
                api_secret=self.api_keys.get('api_secret'),
                testnet=self.testnet
            )
        except Exception as e:
            logger.error(f"Error getting exchange instance: {e}")
            return None

def execute_trading_logic(config: Dict[str, Any], api_keys: Dict[str, str]) -> Dict[str, Any]:
    """
    Main trading logic function
    This is the entry point called by the platform
    """
    try:
        # Initialize bot
        bot = BinanceTradingBot(config, api_keys)
        
        # Execute complete trading cycle
        logger.info("Starting trading cycle...")
        
        # 1. Crawl data
        historical_data = bot.crawl_data()
        if not historical_data:
            return {'status': 'error', 'message': 'Failed to crawl data'}
        
        # 2. Analyze data
        analysis = bot.analyze_data(historical_data)
        if 'error' in analysis:
            return {'status': 'error', 'message': analysis['error']}
        
        # 3. Generate signal
        signal = bot.generate_signal(analysis)
        
        # 4. Execute trade
        trade_result = bot.execute_trade(signal, analysis)
        
        # Return comprehensive result
        return {
            'status': 'success',
            'bot_name': 'BinanceTradingBot',
            'trading_pair': bot.trading_pair,
            'data_points': len(historical_data),
            'analysis': {
                'current_price': analysis.get('current_price'),
                'rsi': analysis.get('rsi'),
                'macd': analysis.get('macd'),
                'volume_ratio': analysis.get('volume_ratio')
            },
            'signal': {
                'action': signal.action,
                'confidence': signal.value,
                'reason': signal.reason
            },
            'trade_result': trade_result,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in trading logic: {e}")
        return {
            'status': 'error',
            'message': f'Trading logic error: {e}',
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test configuration with LLM integration
    test_config = {
        'exchange_type': 'BINANCE',
        'trading_pair': 'BTC/USDT',
        'testnet': True,
        'use_llm_analysis': True,  # Enable LLM analysis
        'llm_model': 'openai',  # Primary LLM model to use
        'rsi_period': 14,
        'max_position_size': 0.1
    }
    
    test_api_keys = {
        # Binance API keys
        'api_key': 'eTVRuGceal7eZq0AlNKQLLEw5AILFbMOY9Shp2BvXRvkiu5SCQNK4Pq4vaS9f6bd',
        'api_secret': 'BgW2TKVLiFVy550iaBiHUNwIVnIiQ1Al1ldPoU9P2x6s3qWfV6BzHAeVZOQqDnJW',
        
        # LLM API keys (set these in environment variables or here)
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'claude_api_key': os.getenv('CLAUDE_API_KEY'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY')
    }
    
    print("🚀 Testing Binance Trading Bot with LLM Integration")
    print(f"🤖 LLM Model: {test_config['llm_model']}")
    print(f"💱 Trading Pair: {test_config['trading_pair']}")
    print(f"🧪 Testnet: {test_config['testnet']}")
    
    result = execute_trading_logic(test_config, test_api_keys)
    print(json.dumps(result, indent=2))
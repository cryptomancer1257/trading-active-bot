"""
LLM Integration Service for Crypto Trading Analysis
Supports OpenAI, Claude, and Gemini for advanced trading insights with Fibonacci analysis
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# LLM Client Imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available. Install with: pip install openai")

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    logging.warning("Claude not available. Install with: pip install anthropic")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Gemini not available. Install with: pip install google-generativeai")

logger = logging.getLogger(__name__)

class LLMIntegrationService:
    """
    LLM Integration Service for Crypto Trading Analysis
    Supports multiple AI models for advanced trading insights with Fibonacci analysis
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize LLM Integration Service
        
        Args:
            config: Configuration with API keys and model settings
        """
        self.config = config or {}
        
        # API Keys - prioritize config, fallback to environment
        self.openai_api_key = self.config.get('openai_api_key', os.getenv('OPENAI_API_KEY'))
        self.claude_api_key = self.config.get('claude_api_key', os.getenv('CLAUDE_API_KEY'))
        self.gemini_api_key = self.config.get('gemini_api_key', os.getenv('GEMINI_API_KEY'))
        
        # Model configurations - Updated model names for 2025
        self.openai_model = self.config.get('openai_model', 'gpt-4o')  # Balanced performance/cost
        self.claude_model = self.config.get('claude_model', 'claude-3-5-sonnet-20241022')  # Latest stable
        self.gemini_model = self.config.get('gemini_model', 'gemini-1.5-pro')
        
        # Initialize clients
        self._initialize_clients()
        
        # Note: analysis_prompt is now generated dynamically based on timeframes
        # in each analyze_with_* method
        
        logger.info("LLM Integration Service initialized")
    
    def _initialize_clients(self):
        """Initialize LLM clients"""
        # OpenAI
        if OPENAI_AVAILABLE and self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            self.openai_client = None
            logger.warning("OpenAI client not available")
        
        # Claude
        if CLAUDE_AVAILABLE and self.claude_api_key:
            self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
            logger.info("Claude client initialized")
        else:
            self.claude_client = None
            logger.warning("Claude client not available")
        
        # Gemini
        if GEMINI_AVAILABLE and self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_client = genai.GenerativeModel(self.gemini_model)
            logger.info("Gemini client initialized")
        else:
            self.gemini_client = None
            logger.warning("Gemini client not available")
    
    def _get_analysis_prompt(self, timeframes: list = None) -> str:
        """Get the high-quality trading analysis prompt with comprehensive technical analysis"""
        # Default timeframes if not provided - Optimized 3 timeframes
        if not timeframes:
            timeframes = ["30M", "1H", "4H"]
        
        # Format timeframes for display (e.g., ['5m', '30m', '1h'] -> "5M, 30M, 1H")
        formatted_timeframes = ", ".join([tf.upper() for tf in timeframes])
        
        # Generate analysis structure for each timeframe in JSON format
        analysis_section = ""
        for i, tf in enumerate(timeframes):
            tf_lower = tf.lower()
            if i == 0:
                # Full structure for first timeframe
                analysis_section += f'    "{tf_lower}": {{\n'
                analysis_section += '      "ma20": "value and position vs price",\n'
                analysis_section += '      "ma50": "value and position vs price",\n'
                analysis_section += '      "bollinger_bands": "position and signal",\n'
                analysis_section += '      "rsi": "value and interpretation",\n'
                analysis_section += '      "macd": "signal and trend",\n'
                analysis_section += '      "stoch_rsi": "value and signal",\n'
                analysis_section += '      "volume_trend": "rising/falling with analysis",\n'
                analysis_section += '      "fibonacci": {\n'
                analysis_section += '        "trend": "uptrend/downtrend",\n'
                analysis_section += '        "swing_high": "price_value",\n'
                analysis_section += '        "swing_low": "price_value",\n'
                analysis_section += '        "current_position": "above_618/between_382_618/below_382/etc",\n'
                analysis_section += '        "key_levels": {\n'
                analysis_section += '          "support": "nearest_fib_level_price",\n'
                analysis_section += '          "resistance": "nearest_fib_level_price"\n'
                analysis_section += '        }\n'
                analysis_section += '      }\n'
                analysis_section += '    }'
            else:
                # Reference structure for other timeframes
                analysis_section += f',\n    "{tf_lower}": {{ "similar structure as {timeframes[0].lower()}" }}'
        
        # Determine Fibonacci base timeframe (use longest available)
        fib_base_timeframe = "1D"
        if "1d" in [tf.lower() for tf in timeframes]:
            fib_base_timeframe = "1D"
        elif "1w" in [tf.lower() for tf in timeframes]:
            fib_base_timeframe = "1W"
        elif timeframes:
            fib_base_timeframe = timeframes[-1].upper()
        
        return f"""You are a professional crypto futures trading analyst.
I will provide you OHLCV data for multiple timeframes ({formatted_timeframes}) in JSON format.

Based on this data, please:

You are a professional crypto futures trading engine. Analyze OHLCV data across multiple timeframes and make autonomous BUY/SELL/HOLD decisions based on strict technical analysis criteria. 
CRITICAL REQUIREMENTS:
 - ONLY output valid JSON - no explanatory text outside JSON
 - STRICT volume confirmation - if volume fails, return HOLD immediately
 - Conservative approach - only trade high-probability setups
 - Risk management mandatory - all trades must have proper SL/TP
 - Multi-timeframe confluence - require agreement across timeframes

ANALYSIS WORKFLOW (STRICT ORDER):
STEP 1: VOLUME VALIDATION (MANDATORY FIRST CHECK)
    CALCULATE: Current volume vs Average of last 20 candles
    REQUIREMENTS:
    - BUY/SELL: Current volume ≥ 130% of 20-period average
    - HOLD: Current volume < 130% of 20-period average
    IF volume fails → STOP analysis → Return HOLD immediately

STEP 2: MULTI-TIMEFRAME TREND CONFIRMATION
    CALCULATE: MA5, MA10, MA20 for each timeframe
    BULLISH TREND: MA5 > MA10 > MA20 (all timeframes agree)
    BEARISH TREND: MA5 < MA10 < MA20 (all timeframes agree)
    SIDEWAYS: Mixed signals across timeframes
    REQUIREMENTS:
    - BUY: At least 2/3 timeframes show bullish alignment
    - SELL: At least 2/3 timeframes show bearish alignment
    - HOLD: Conflicting trends or sideways action
STEP 3: MOMENTUM ANALYSIS
    RSI(14):
    - BUY Zone: 40-65 (avoid overbought >70)
    - SELL Zone: 35-60 (avoid oversold <30)
    - EXCLUDE: RSI >75 or <25 (extreme zones)
    
    MACD:
    - BUY: MACD line > Signal line AND both trending up
    - SELL: MACD line < Signal line AND both trending down
    - PRIORITY: Recent crossover within 1-3 candles
STEP 4: SUPPORT/RESISTANCE VALIDATION
    BOLLINGER BANDS:
    - BUY: Price bounces from Lower BB OR breaks above Middle BB with volume
    - SELL: Price bounces from Upper BB OR breaks below Middle BB with volume
    - AVOID: Price in middle third of BB range (no clear signal)
    
    KEY LEVELS:
    - IDENTIFY: Recent swing highs/lows within 20 candles
    - CONFIRM: Price at or near significant support/resistance
STEP 5: FIBONACCI CONFLUENCE (BONUS)
    IF clear trend exists:
    - IDENTIFY: Recent swing high to swing low (or vice versa)
    - PRIORITY ZONES: 0.382, 0.5, 0.618 retracement levels
    - BONUS POINTS: Entry price within ±0.5% of Fibonacci level
    - SKIP: If no clear Fibonacci structure
EXCLUSION CRITERIA (AUTO-HOLD):
    Volume insufficient (< 130% average)
    Extreme RSI (>75 or <25)
    Conflicting timeframes (no 2/3 agreement)
    Sideways consolidation (price within 1.5% range for 10+ candles)
    Recent false breakout (failed breakout within 5 candles)
    Low volatility (ATR < 0.8% of current price)
CONFIDENCE SCORING:
    90-100%: 5+ indicators agree + volume spike (>150%) + clear trend
    75-89%:  4 indicators agree + good volume (>130%) + trend confirmation
    60-74%:  3 indicators agree + adequate volume + some trend signals
    55-59%:  2 indicators agree + minimum volume + weak signals
    <55%:    HOLD - insufficient setup quality
STOP-LOSS CALCULATION:
    BUY Stops:
        1. Below recent swing low (last 10 candles), OR
        2. Below Lower Bollinger Band, OR  
        3. 2-3% below entry (whichever is closer)
    SELL Stops:
        1. Above recent swing high (last 10 candles), OR
        2. Above Upper Bollinger Band, OR
        3. 2-3% above entry (whichever is closer)
TAKE-PROFIT TARGETS:
    BUY Targets:
        1. Next resistance level, OR
        2. Upper Bollinger Band, OR
        3. 1.5x stop-loss distance minimum
    
    SELL Targets:
        1. Next support level, OR
        2. Lower Bollinger Band, OR
        3. 1.5x stop-loss distance minimum
    MINIMUM R:R RATIO: 1.5:1 (prefer 2:1+)
OUTPUT FORMAT (STRICT JSON SCHEMA):
{{
  "recommendation": {{
    "action": "BUY" | "SELL" | "HOLD",
    "entry_price": "<string or null>",
    "take_profit": "<string or null>",
    "stop_loss": "<string or null>",
    "strategy": "<MA, MACD, RSI, BollingerBands, Fibonacci_Retracement hoặc kết hợp>",
    "risk_reward": "<string hoặc null>",
    "confidence": "<0-100>",
    "reasoning": "<ngắn gọn 1-2 câu giải thích tại sao>"
  }}
}}
OUTPUT RULES:
    HOLD actions: All price fields = null
    Decimal precision: 1 decimal place for all prices
    No text outside JSON: Pure JSON response only
    Confidence < 55%: Force action = "HOLD"
FINAL VALIDATION CHECKLIST:
    ✓ Volume > 130% average?
    ✓ 2/3 timeframes agree on trend?
    ✓ RSI in valid range (not extreme)?
    ✓ Clear support/resistance level?
    ✓ Risk:Reward ≥ 1.5:1?
    ✓ Confidence ≥ 55%?
    IF any ✗ → HOLD
DỮ LIỆU:"""
    
    def _get_capital_management_prompt(self) -> str:
        """Get the capital management prompt template for position sizing advice"""
        return """You are a professional risk management and capital allocation specialist for crypto futures trading.

I will provide you with account and market information to help determine optimal position sizing.

📊 Account Information:
- Total account balance
- Available balance for trading
- Current portfolio exposure
- Current drawdown status
- Historical performance metrics

📈 Market Analysis:
- Market volatility level
- Trading signal confidence
- Current price and ATR
- Risk/reward assessment

💰 Position Sizing Request:
Please provide specific recommendations for:

1. **Recommended Position Size**: 
   - Percentage of account balance to risk
   - Absolute dollar amount if beneficial
   - Reasoning for this specific size

2. **Risk Assessment**:
   - Market risk level (LOW/MEDIUM/HIGH)
   - Account risk level (LOW/MEDIUM/HIGH)
   - Overall trade risk rating

3. **Risk Management Factors**:
   - Volatility impact on sizing
   - Drawdown protection considerations
   - Portfolio correlation concerns
   - Maximum safe exposure limits

4. **Strategic Recommendations**:
   - Position sizing method used
   - Confidence-based adjustments
   - Long-term portfolio health considerations
   - Specific warnings or alerts

Please respond in JSON format:
{
  "capital_advice": {
    "recommended_size_pct": "percentage_0_to_100",
    "max_safe_size_pct": "percentage_0_to_100", 
    "risk_level": "LOW/MEDIUM/HIGH",
    "sizing_method": "method_used",
    "volatility_adjustment": "percentage_adjustment",
    "drawdown_adjustment": "percentage_adjustment",
    "confidence_factor": "factor_0_to_2",
    "reasoning": "detailed_explanation"
  },
  "risk_assessment": {
    "market_risk": "LOW/MEDIUM/HIGH",
    "account_risk": "LOW/MEDIUM/HIGH", 
    "overall_risk": "LOW/MEDIUM/HIGH",
    "key_concerns": ["list", "of", "main", "concerns"],
    "recommendations": ["specific", "risk", "management", "advice"]
  },
  "portfolio_management": {
    "current_exposure_evaluation": "assessment_of_current_exposure",
    "recommended_max_exposure": "percentage_for_this_strategy",
    "diversification_advice": "specific_advice",
    "position_correlation": "low/medium/high_correlation_with_existing"
  }
}"""
    
    def prepare_market_data(self, symbol: str, timeframes_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Prepare market data for LLM analysis
        """
        try:
            formatted_data = {
                "symbol": symbol,
                "analysis_timestamp": datetime.now().isoformat(),
                "timeframes": timeframes_data
            }
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error preparing market data: {e}")
            return {}
    
    async def analyze_with_openai(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data using OpenAI"""
        if not self.openai_client:
            return {"error": "OpenAI client not available"}
        
        try:
            # Extract timeframes from market_data
            timeframes = list(market_data.get("timeframes", {}).keys())
            
            # Generate dynamic prompt based on actual timeframes
            dynamic_prompt = self._get_analysis_prompt(timeframes)
            
            prompt = f"{dynamic_prompt}\n\nMarket Data:\n{json.dumps(market_data, indent=2)}"
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": f"You are a professional trading engine. Analyze OHLCV data for timeframes: {', '.join(timeframes)}. Focus on volume confirmation and quality entry points. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"OpenAI analysis error: {e}")
            return {"error": f"OpenAI analysis failed: {str(e)}"}
    
    async def analyze_with_claude(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data using Claude"""
        if not self.claude_client:
            return {"error": "Claude client not available"}
        
        try:
            # Extract timeframes from market_data
            timeframes = list(market_data.get("timeframes", {}).keys())
            
            # Generate dynamic prompt based on actual timeframes
            dynamic_prompt = self._get_analysis_prompt(timeframes)
            
            prompt = f"{dynamic_prompt}\n\nMarket Data:\n{json.dumps(market_data, indent=2)}"
            
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=self.claude_model,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"Claude analysis error: {e}")
            return {"error": f"Claude analysis failed: {str(e)}"}
    
    async def analyze_with_gemini(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data using Gemini"""
        if not self.gemini_client:
            return {"error": "Gemini client not available"}
        
        try:
            # Extract timeframes from market_data
            timeframes = list(market_data.get("timeframes", {}).keys())
            
            # Generate dynamic prompt based on actual timeframes
            dynamic_prompt = self._get_analysis_prompt(timeframes)
            
            prompt = f"{dynamic_prompt}\n\nMarket Data:\n{json.dumps(market_data, indent=2)}"
            
            response = await asyncio.to_thread(
                self.gemini_client.generate_content,
                prompt
            )
            
            content = response.text
            return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            return {"error": f"Gemini analysis failed: {str(e)}"}
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract trading analysis"""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                return {
                    "raw_response": response,
                    "parsed": False,
                    "error": "No JSON found in response"
                }
            
            parsed = json.loads(json_str)
            parsed["parsed"] = True
            parsed["raw_response"] = response
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                "raw_response": response,
                "parsed": False,
                "error": f"Parse error: {str(e)}"
            }
    
    async def analyze_market(self, symbol: str, timeframes_data: Dict[str, List[Dict]], 
                           model: str = "openai") -> Dict[str, Any]:
        """
        Main method to analyze market data with specified LLM
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            timeframes_data: OHLCV data for different timeframes
            model: LLM to use ("openai", "claude", "gemini")
            
        Returns:
            Complete trading analysis with Fibonacci
        """
        try:
            # Prepare market data
            market_data = self.prepare_market_data(symbol, timeframes_data)
            
            if not market_data:
                return {"error": "Failed to prepare market data"}
            
            # Analyze with specified model
            if model.lower() == "openai":
                analysis = await self.analyze_with_openai(market_data)
            elif model.lower() == "claude":
                analysis = await self.analyze_with_claude(market_data)
            elif model.lower() == "gemini":
                analysis = await self.analyze_with_gemini(market_data)
            else:
                return {"error": f"Unsupported model: {model}"}
            
            # Add metadata
            analysis["metadata"] = {
                "symbol": symbol,
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "timeframes_analyzed": list(timeframes_data.keys()),
                "service": "LLMIntegrationService"
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def get_capital_management_advice(self, capital_context: Dict[str, Any], 
                                          base_position_size: float, max_position_size: float,
                                          model: str = "openai") -> Dict[str, Any]:
        """
        Get capital management and position sizing advice from LLM
        
        Args:
            capital_context: Account and market information for position sizing
            base_position_size: Base position size percentage
            max_position_size: Maximum allowed position size percentage
            model: LLM to use for analysis
            
        Returns:
            Capital management recommendations
        """
        try:
            # Prepare capital management prompt
            prompt = self._get_capital_management_prompt()
            
            # Format the context data
            context_str = "\n".join([f"{key}: {value}" for key, value in capital_context.items()])
            
            # Create the full prompt
            full_prompt = f"""{prompt}

📊 Current Account & Market Context:
{context_str}

Base Position Size: {base_position_size*100:.1f}%
Maximum Position Size: {max_position_size*100:.1f}%

Please analyze this information and provide specific capital management recommendations."""
            
            # Prepare request data
            request_data = {
                "prompt": full_prompt,
                "context": capital_context,
                "constraints": {
                    "base_size": base_position_size,
                    "max_size": max_position_size
                }
            }
            
            # Get LLM analysis
            if model.lower() == "openai":
                response = await self._get_capital_advice_openai(request_data)
            elif model.lower() == "claude":
                response = await self._get_capital_advice_claude(request_data)
            elif model.lower() == "gemini":
                response = await self._get_capital_advice_gemini(request_data)
            else:
                return {"error": f"Unsupported model: {model}"}
            
            # Add metadata
            response["metadata"] = {
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "service": "LLMIntegrationService",
                "analysis_type": "capital_management"
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Capital management advice error: {e}")
            return {"error": f"Capital management analysis failed: {str(e)}"}
    
    async def _get_capital_advice_openai(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get capital management advice from OpenAI"""
        try:
            if not self.openai_client:
                return {"error": "OpenAI client not available"}
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a professional risk management specialist."},
                        {"role": "user", "content": request_data["prompt"]}
                    ],
                    max_tokens=1500,
                    temperature=0.3
                )
            )
            
            content = response.choices[0].message.content
            return self._parse_capital_response(content)
            
        except Exception as e:
            logger.error(f"OpenAI capital advice error: {e}")
            return {"error": f"OpenAI capital analysis failed: {str(e)}"}
    
    async def _get_capital_advice_claude(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get capital management advice from Claude"""
        try:
            if not self.claude_client:
                return {"error": "Claude client not available"}
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=1500,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": request_data["prompt"]}
                    ]
                )
            )
            
            content = response.content[0].text
            return self._parse_capital_response(content)
            
        except Exception as e:
            logger.error(f"Claude capital advice error: {e}")
            return {"error": f"Claude capital analysis failed: {str(e)}"}
    
    async def _get_capital_advice_gemini(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get capital management advice from Gemini"""
        try:
            if not self.gemini_client:
                return {"error": "Gemini client not available"}
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.gemini_client.generate_content(
                    request_data["prompt"],
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 2000,
                    }
                )
            )
            
            content = response.text
            return self._parse_capital_response(content)
            
        except Exception as e:
            logger.error(f"Gemini capital advice error: {e}")
            return {"error": f"Gemini capital analysis failed: {str(e)}"}
    
    def _parse_capital_response(self, response: str) -> Dict[str, Any]:
        """Parse capital management LLM response"""
        try:
            # Try to extract JSON from response
            parsed = self._parse_llm_response(response)
            
            if parsed.get("parsed", False):
                # Extract specific capital advice if available
                if "capital_advice" in parsed:
                    capital_advice = parsed["capital_advice"]
                    
                    # Extract recommended size percentage
                    recommended_size = capital_advice.get("recommended_size_pct", "2.0")
                    if isinstance(recommended_size, str):
                        recommended_size = float(recommended_size.replace("%", ""))
                    
                    # Add to response for easy access
                    parsed["recommended_size_pct"] = recommended_size
                    parsed["risk_level"] = capital_advice.get("risk_level", "MEDIUM")
                    parsed["sizing_method"] = capital_advice.get("sizing_method", "llm_analysis")
                
                return parsed
            else:
                # If JSON parsing fails, return basic response
                return {
                    "raw_response": response,
                    "parsed": False,
                    "recommended_size_pct": 2.0,  # Conservative fallback
                    "risk_level": "MEDIUM",
                    "sizing_method": "fallback",
                    "error": "Failed to parse capital management response"
                }
                
        except Exception as e:
            logger.error(f"Error parsing capital management response: {e}")
            return {
                "raw_response": response,
                "parsed": False,
                "recommended_size_pct": 2.0,  # Conservative fallback
                "risk_level": "MEDIUM", 
                "sizing_method": "fallback",
                "error": f"Parse error: {str(e)}"
            }

# Factory function to create service instance
def create_llm_service(config: Dict[str, Any] = None) -> LLMIntegrationService:
    """
    Factory function to create LLM Integration Service
    
    Args:
        config: Optional configuration dict
        
    Returns:
        LLMIntegrationService instance
    """
    return LLMIntegrationService(config)

# Test function
def test_llm_integration():
    """Test LLM integration service"""
    
    # Sample market data with realistic patterns
    sample_data = {
        "1h": [
            {"timestamp": 1640995200000, "open": 47000, "high": 48000, "low": 46500, "close": 47500, "volume": 1000},
            {"timestamp": 1640998800000, "open": 47500, "high": 49000, "low": 47000, "close": 48500, "volume": 1200},
            {"timestamp": 1641002400000, "open": 48500, "high": 50000, "low": 48000, "close": 49500, "volume": 1500},
            {"timestamp": 1641006000000, "open": 49500, "high": 51000, "low": 49000, "close": 50500, "volume": 1800},
            {"timestamp": 1641009600000, "open": 50500, "high": 52000, "low": 50000, "close": 51500, "volume": 2000}
        ],
        "4h": [
            {"timestamp": 1640995200000, "open": 47000, "high": 50000, "low": 46000, "close": 49000, "volume": 5000},
            {"timestamp": 1641009600000, "open": 49000, "high": 52000, "low": 48500, "close": 51500, "volume": 6000}
        ],
        "1d": [
            {"timestamp": 1640995200000, "open": 47000, "high": 52000, "low": 45000, "close": 51500, "volume": 25000}
        ]
    }
    
    # Initialize service
    service = create_llm_service()
    
    print("✅ LLM Integration Service initialized!")
    print(f"   OpenAI: {'✅' if service.openai_client else '❌'}")
    print(f"   Claude: {'✅' if service.claude_client else '❌'}")
    print(f"   Gemini: {'✅' if service.gemini_client else '❌'}")
    
    return service

if __name__ == "__main__":
    test_llm_integration()
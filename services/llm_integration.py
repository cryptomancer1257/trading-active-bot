"""
LLM Integration Service for Crypto Trading Analysis
Supports OpenAI, Claude, and Gemini for advanced trading insights with Fibonacci analysis
"""

import os
import json
import logging
import asyncio
import time
import hashlib
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
    
    def __init__(self, config: Dict[str, Any] = None, developer_id: int = None, db = None, 
                 preferred_provider: str = None, bot_id: int = None):
        """
        Initialize LLM Integration Service
        
        Args:
            config: Configuration with API keys and model settings
            developer_id: Developer ID to load their configured LLM providers (BYOK)
            db: Database session for loading provider configs
            preferred_provider: Preferred provider ("openai", "claude", "gemini") - from bot config
            bot_id: Bot ID for logging
        """
        self.config = config or {}
        self.developer_id = developer_id
        self.db = db
        self.bot_id = bot_id
        
        # Try to load developer's LLM provider configuration first (BYOK - Priority!)
        provider_config = None
        if developer_id and db:
            try:
                from services.llm_provider_selector import LLMProviderSelector
                selector = LLMProviderSelector(db)
                
                # Get developer's configured provider (with bot's preference!)
                source_type, provider_config = selector.get_provider_for_developer(
                    developer_id=developer_id,
                    bot_id=bot_id,
                    preferred_provider=preferred_provider  # ✅ Use bot's preference!
                )
                
                if source_type == "USER_CONFIGURED":
                    logger.info(f"✅ Using developer's LLM provider: {provider_config['provider']} ({provider_config['model']})")
                    
                    # Override config with developer's provider
                    # Extract the enum value and convert to uppercase for comparison
                    provider_enum = provider_config['provider']
                    provider_type = str(provider_enum.value).upper() if hasattr(provider_enum, 'value') else str(provider_enum).upper()
                    
                    if provider_type == 'OPENAI':
                        self.config['openai_api_key'] = provider_config['api_key']
                        self.config['openai_model'] = provider_config['model']
                    elif provider_type in ['ANTHROPIC']:
                        self.config['claude_api_key'] = provider_config['api_key']
                        self.config['claude_model'] = provider_config['model']
                    elif provider_type == 'GEMINI':
                        self.config['gemini_api_key'] = provider_config['api_key']
                        self.config['gemini_model'] = provider_config['model']
                    elif provider_type == 'GROQ':
                        self.config['groq_api_key'] = provider_config['api_key']
                        self.config['groq_model'] = provider_config['model']
                    elif provider_type == 'COHERE':
                        self.config['cohere_api_key'] = provider_config['api_key']
                        self.config['cohere_model'] = provider_config['model']
                    
                    # Store for usage logging later
                    self._provider_config = provider_config
                    self._provider_selector = selector
                else:
                    logger.warning(f"⚠️ Developer {developer_id} is using platform provider (not implemented yet)")
                    self._provider_config = None
                    self._provider_selector = None
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not load developer's LLM provider: {e}")
                logger.info("   Falling back to environment variables")
                self._provider_config = None
                self._provider_selector = None
        else:
            self._provider_config = None
            self._provider_selector = None
        
        # API Keys - prioritize config (from developer), fallback to environment
        self.openai_api_key = self.config.get('openai_api_key', os.getenv('OPENAI_API_KEY'))
        self.claude_api_key = self.config.get('claude_api_key', os.getenv('CLAUDE_API_KEY'))
        self.gemini_api_key = self.config.get('gemini_api_key', os.getenv('GEMINI_API_KEY'))
        
        # Model configurations - Updated model names for 2025
        self.openai_model = self.config.get('openai_model', 'gpt-4o-mini')  # More cost-effective with good performance
        self.claude_model = self.config.get('claude_model', 'claude-3-5-sonnet-20241022')  # Latest stable
        self.gemini_model = self.config.get('gemini_model', 'gemini-2.5-flash')  # Updated: Latest balanced model (Oct 2025)
        
        # Performance and reliability settings
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)  # seconds
        self.timeout = self.config.get('timeout', 30)  # seconds
        self.enable_caching = self.config.get('enable_caching', True)
        
        # Cache for analysis results (simple in-memory cache)
        self._analysis_cache = {} if self.enable_caching else None
        
        # Initialize clients
        self._initialize_clients()
        
        # Note: analysis_prompt is now generated dynamically based on timeframes
        # in each analyze_with_* method
        
        if self._provider_config:
            logger.info(f"✅ LLM Integration initialized with developer's {self._provider_config['provider']} provider (FREE)")
        else:
            logger.info("ℹ️  LLM Integration initialized with environment variables")
    
    def _generate_cache_key(self, symbol: str, timeframes_data: Dict[str, List[Dict]], model: str) -> str:
        """Generate cache key for analysis results"""
        if not self.enable_caching:
            return None
        
        # Create a hash of the input data
        data_str = json.dumps({
            'symbol': symbol,
            'timeframes': timeframes_data,
            'model': model
        }, sort_keys=True)
        
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result"""
        if not self.enable_caching or not cache_key or not self._analysis_cache:
            return None
        
        cached_result = self._analysis_cache.get(cache_key)
        if cached_result:
            # Check if cache is still valid (5 minutes)
            cache_time = cached_result.get('cache_timestamp', 0)
            if time.time() - cache_time < 300:  # 5 minutes
                logger.info("Using cached analysis result")
                return cached_result.get('analysis')
            else:
                # Remove expired cache
                del self._analysis_cache[cache_key]
        
        return None
    
    def _cache_analysis(self, cache_key: str, analysis: Dict[str, Any]) -> None:
        """Cache analysis result"""
        if not self.enable_caching or not cache_key:
            return
        
        if not self._analysis_cache:
            self._analysis_cache = {}
        
        self._analysis_cache[cache_key] = {
            'analysis': analysis,
            'cache_timestamp': time.time()
        }
        
        # Limit cache size (keep only last 50 entries)
        if len(self._analysis_cache) > 50:
            oldest_key = min(self._analysis_cache.keys(), 
                           key=lambda k: self._analysis_cache[k]['cache_timestamp'])
            del self._analysis_cache[oldest_key]
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed. Last error: {e}")
        
        raise last_exception
    
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
    
    def _get_analysis_prompt(self, bot_id: int = None, timeframes: list = None) -> str:
        """Get dynamic trading analysis prompt from bot's attached prompt template"""
        # Default timeframes if not provided - Optimized 3 timeframes
        if not timeframes:
            timeframes = ["30M", "1H", "4H"]
        
        # Format timeframes for display (e.g., ['5m', '30m', '1h'] -> "5M, 30M, 1H")
        formatted_timeframes = ", ".join([tf.upper() for tf in timeframes])
        
        logger.info(f"🔍 _get_analysis_prompt called with bot_id={bot_id}, timeframes={timeframes}")
        
        # If bot_id is provided, try to get prompt from bot's attached prompt
        if bot_id:
            try:
                from core.database import get_db
                from core import crud, models
                from sqlalchemy.orm import Session
                
                # Get database session
                db = next(get_db())
                
                # Get bot to check bot_type for SIGNALS_FUTURES
                bot = crud.get_bot_by_id(db, bot_id)
                bot_type_str = str(bot.bot_type).upper().strip() if bot and bot.bot_type else None
                if bot_type_str and "." in bot_type_str:
                    bot_type_str = bot_type_str.split(".")[-1]
                
                is_signals_futures = (bot_type_str == "SIGNALS_FUTURES")
                
                # Get bot's attached prompt
                bot_prompts = crud.get_bot_prompts(db, bot_id)
                logger.info(f"📋 Found {len(bot_prompts) if bot_prompts else 0} bot prompts for bot {bot_id}")
                if bot_prompts:
                    # Get the active prompt (highest priority)
                    active_prompt = max(bot_prompts, key=lambda x: x.priority)
                    # Use relationship instead of separate query
                    prompt_template = active_prompt.llm_prompt_template
                    
                    if prompt_template and prompt_template.content:
                        logger.info(f"✅ Using custom prompt template: {prompt_template.name} (ID: {prompt_template.id})")
                        logger.info(f"📝 Prompt content preview: {prompt_template.content[:100]}...")
                        # Use bot's custom prompt with variable injection
                        bot_prompt = prompt_template.content
                        
                        # Inject variables into the prompt
                        variables = {
                            'formatted_timeframes': formatted_timeframes,
                            'current_price': '{current_price}',  # Will be replaced by actual price
                            'symbol': '{symbol}',  # Will be replaced by actual symbol
                            'exchange': '{exchange}',  # Will be replaced by actual exchange
                            'timeframe': '{timeframe}',  # Will be replaced by primary timeframe
                            'timestamp': '{timestamp}',  # Will be replaced by current timestamp
                            'user_id': '{user_id}',  # Will be replaced by actual user ID
                            'bot_id': str(bot_id)
                        }
                        
                        # Replace variables in the prompt
                        for key, value in variables.items():
                            bot_prompt = bot_prompt.replace(f'{{{key}}}', value)
                        
                        # Append mandatory output format (different for SIGNALS_FUTURES)
                        if is_signals_futures:
                            output_format = """

                                    OUTPUT FORMAT (STRICT JSON SCHEMA):
                                    {
                                        "recommendation": {
                                            "action": "BUY" | "SELL" | "HOLD",
                                            "entry_price": "<numeric price>",
                                            "stop_loss": "<numeric price>",
                                            "take_profit": "<numeric price>",
                                            "risk_reward": "<string like '1:2' or null>",
                                            "strategy": "<MA, MACD, RSI, BollingerBands, Fibonacci_Retracement or combination>",
                                            "confidence": "<0-100>",
                                            "reasoning": "<DETAILED 3-5 sentences: analyze the trend, entry point, technical/fundamental reasons, and risk management>",
                                            "market_volatility": "LOW" | "MEDIUM" | "HIGH"
                                        }
                                    }
                                    
                                    SIGNALS BOT REQUIREMENTS - CRITICAL:
                                    - **Entry Price**: Use current market price or specific level based on technical analysis
                                    - **Stop Loss**: Set below entry for BUY (e.g., entry * 0.99), above entry for SELL (e.g., entry * 1.01)
                                    - **Take Profit**: MUST BE DIFFERENT from entry price!
                                      * For BUY: take_profit MUST be HIGHER than entry_price (e.g., entry + risk_amount * reward_ratio)
                                      * For SELL: take_profit MUST be LOWER than entry_price (e.g., entry - risk_amount * reward_ratio)
                                      * Example: If entry=3892, SL=3870 (risk=$22), then TP for 1:1 = 3892 + 22 = 3914 (NOT 3892!)
                                    - **Risk/Reward**: Calculate as (TP - Entry) / (Entry - SL) for BUY, or (Entry - TP) / (SL - Entry) for SELL
                                    - **Reasoning**: DETAILED explanation with trend analysis, entry rationale, and risk considerations
                                    - **Market Volatility**: Assess current market conditions (ATR, volume, price swings)
                                    - RETURN ONLY VALID JSON - no additional text outside the JSON object
                                    """
                        else:
                            output_format = """

                                    OUTPUT FORMAT (STRICT JSON SCHEMA):
                                    {
                                    "recommendation": {
                                        "action": "BUY" | "SELL" | "HOLD",
                                        "entry_price": "<string or null>",
                                        "strategy": "<MA, MACD, RSI, BollingerBands, Fibonacci_Retracement hoặc kết hợp>",
                                        "confidence": "<0-100>",
                                        "reasoning": "<briefly explain in 1–2 sentences why>"
                                    }
                                    }
                                    
                                    NOTE: Stop Loss and Take Profit are automatically calculated from Risk Config (developer-configured parameters), not from LLM.
                                    """
                        
                        bot_prompt = bot_prompt + output_format
                        
                        logger.info(f"Using dynamic prompt from bot {bot_id} (bot_type={bot_type_str}) with {'SIGNALS' if is_signals_futures else 'STANDARD'} output format")
                        logger.info(f"📄 Final prompt length: {len(bot_prompt)} chars")
                        logger.info(f"📄 Output format preview: {output_format[:150]}...")
                        return bot_prompt
                        
            except Exception as e:
                logger.error(f"❌ Failed to get bot prompt for bot {bot_id}: {e}")
                import traceback
                traceback.print_exc()
                # Fall back to default prompt
        
        # Fallback to default prompt if no bot_id or error
        logger.warning(f"⚠️  Using DEFAULT prompt (bot_id={bot_id})")
        return self._get_default_analysis_prompt(timeframes)
    
    def _get_default_analysis_prompt(self, timeframes: list) -> str:
        """Get the default high-quality trading analysis prompt"""
        # Format timeframes for display
        formatted_timeframes = ", ".join([tf.upper() for tf in timeframes])
        
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
    - BUY/SELL: Current volume ≥ 110% of 20-period average
    - HOLD: Current volume < 110% of 20-period average
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
    Volume insufficient (< 110% average)
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
    "entry_price": "<string | null>",
    "strategy": "<MA, MACD, RSI, BollingerBands, Fibonacci_Retracement hoặc kết hợp>",
    "confidence": "<number 0-100>",
    "reasoning": "<ngắn gọn 1-2 câu giải thích tại sao>"
  }}
}}

NOTE: Stop Loss and Take Profit are automatically calculated from Risk Config (developer-configured parameters), not from LLM.
OUTPUT RULES:
    HOLD actions: All price fields = null
    Decimal precision: 1 decimal place for all prices
    No text outside JSON: Pure JSON response only
    Confidence < 55%: Force action = "HOLD"
FINAL VALIDATION CHECKLIST:
    ✓ Volume > 110% average?
    ✓ 2/3 timeframes agree on trend?
    ✓ RSI in valid range (not extreme)?
    ✓ Clear support/resistance level?
    ✓ Risk:Reward ≥ 1.5:1?
    ✓ Confidence ≥ 55%?
    IF any ✗ → HOLD
DỮ LIỆU:"""
    
    def _get_capital_management_prompt(self, bot_id: int = None) -> str:
        """Get dynamic capital management prompt from bot's attached risk management prompt template"""
        # If bot_id is provided, try to get risk management prompt from bot's attached prompts
        if bot_id:
            try:
                from core.database import get_db
                from core import crud, models
                from sqlalchemy.orm import Session
                
                # Get database session
                db = next(get_db())
                
                # Get bot's attached prompts
                bot_prompts = crud.get_bot_prompts(db, bot_id)
                if bot_prompts:
                    # Filter for risk management prompts
                    risk_prompts = [bp for bp in bot_prompts if bp.prompt_template and bp.prompt_template.category == 'RISK_MANAGEMENT']
                    
                    if risk_prompts:
                        # Get the highest priority risk management prompt
                        active_risk_prompt = max(risk_prompts, key=lambda x: x.priority)
                        prompt_template = crud.get_prompt_template_by_id(db, active_risk_prompt.prompt_id)
                        
                        if prompt_template and prompt_template.content:
                            # Use bot's custom risk management prompt with variable injection
                            bot_prompt = prompt_template.content
                            
                            # Inject variables into the prompt
                            variables = {
                                'current_price': '{current_price}',  # Will be replaced by actual price
                                'symbol': '{symbol}',  # Will be replaced by actual symbol
                                'exchange': '{exchange}',  # Will be replaced by actual exchange
                                'timestamp': '{timestamp}',  # Will be replaced by current timestamp
                                'user_id': '{user_id}',  # Will be replaced by actual user ID
                                'bot_id': str(bot_id)
                            }
                            
                            # Replace variables in the prompt
                            for key, value in variables.items():
                                bot_prompt = bot_prompt.replace(f'{{{key}}}', value)
                            
                            logger.info(f"Using dynamic risk management prompt from bot {bot_id}")
                            return bot_prompt
                            
            except Exception as e:
                logger.warning(f"Failed to get risk management prompt for bot {bot_id}: {e}")
                # Fall back to default prompt
        
        # Fallback to default capital management prompt if no bot_id or error
        return self._get_default_capital_management_prompt()
    
    def _get_default_capital_management_prompt(self) -> str:
        """Get the default capital management prompt template"""
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
    
    async def analyze_with_openai(self, market_data: Dict[str, Any], bot_id: int = None) -> Dict[str, Any]:
        """Analyze market data using OpenAI"""
        if not self.openai_client:
            return {"error": "OpenAI client not available"}
        
        try:
            # Extract timeframes from market_data
            timeframes = list(market_data.get("timeframes", {}).keys())
            
            # Generate dynamic prompt based on actual timeframes and bot_id
            dynamic_prompt = self._get_analysis_prompt(bot_id, timeframes)
            
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
    
    async def analyze_with_claude(self, market_data: Dict[str, Any], bot_id: int = None) -> Dict[str, Any]:
        """Analyze market data using Claude"""
        if not self.claude_client:
            return {"error": "Claude client not available"}
        
        try:
            # Extract timeframes from market_data
            timeframes = list(market_data.get("timeframes", {}).keys())
            
            # Generate dynamic prompt based on actual timeframes and bot_id
            dynamic_prompt = self._get_analysis_prompt(bot_id, timeframes)
            
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
    
    async def analyze_with_gemini(self, market_data: Dict[str, Any], bot_id: int = None) -> Dict[str, Any]:
        """Analyze market data using Gemini"""
        if not self.gemini_client:
            return {"error": "Gemini client not available"}
        
        try:
            # Extract timeframes from market_data
            timeframes = list(market_data.get("timeframes", {}).keys())
            
            # Generate dynamic prompt based on actual timeframes and bot_id
            dynamic_prompt = self._get_analysis_prompt(bot_id, timeframes)
            
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
                           model: str = "openai", bot_id: int = None) -> Dict[str, Any]:
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
            # Check cache first
            cache_key = self._generate_cache_key(symbol, timeframes_data, model)
            cached_analysis = self._get_cached_analysis(cache_key)
            if cached_analysis:
                return cached_analysis
            
            # Prepare market data
            market_data = self.prepare_market_data(symbol, timeframes_data)
            
            if not market_data:
                return {"error": "Failed to prepare market data"}
            
            # Analyze with specified model using retry mechanism
            # Support both provider type ("openai") and full model name ("gpt-4o-mini")
            model_lower = model.lower()
            if model_lower == "openai" or model_lower.startswith("gpt"):
                analysis = await self._retry_with_backoff(self.analyze_with_openai, market_data, bot_id)
            elif model_lower == "claude" or model_lower.startswith("claude") or model_lower == "anthropic":
                analysis = await self._retry_with_backoff(self.analyze_with_claude, market_data, bot_id)
            elif model_lower == "gemini" or model_lower.startswith("gemini"):
                analysis = await self._retry_with_backoff(self.analyze_with_gemini, market_data, bot_id)
            else:
                return {"error": f"Unsupported model: {model}"}
            
            # Add metadata
            analysis["metadata"] = {
                "symbol": symbol,
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "timeframes_analyzed": list(timeframes_data.keys()),
                "service": "LLMIntegrationService",
                "cached": False
            }
            
            # Cache the result
            if cache_key:
                self._cache_analysis(cache_key, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def analyze_sentiment(self, news_data: List[Dict[str, Any]], 
                               model: str = "openai") -> Dict[str, Any]:
        """
        Analyze market sentiment from news data
        
        Args:
            news_data: List of news articles with title, content, timestamp
            model: LLM to use for sentiment analysis
            
        Returns:
            Sentiment analysis with confidence score
        """
        try:
            if not news_data:
                return {"error": "No news data provided"}
            
            # Prepare sentiment analysis prompt
            sentiment_prompt = """You are a financial sentiment analyst. Analyze the provided news articles and determine the overall market sentiment for cryptocurrency trading.

News Articles:
{news_data}

Please provide sentiment analysis in JSON format:
{{
  "overall_sentiment": "BULLISH/NEUTRAL/BEARISH",
  "confidence": "0-100",
  "key_themes": ["theme1", "theme2", "theme3"],
  "market_impact": "HIGH/MEDIUM/LOW",
  "trading_implications": "brief explanation",
  "risk_factors": ["risk1", "risk2"],
  "opportunities": ["opportunity1", "opportunity2"]
}}"""
            
            # Format news data
            formatted_news = []
            for article in news_data[:10]:  # Limit to 10 most recent articles
                formatted_news.append({
                    "title": article.get("title", ""),
                    "content": article.get("content", "")[:500],  # Limit content length
                    "timestamp": article.get("timestamp", ""),
                    "source": article.get("source", "")
                })
            
            prompt = sentiment_prompt.format(news_data=json.dumps(formatted_news, indent=2))
            
            # Get LLM analysis
            # Support both provider type ("openai") and full model name ("gpt-4o-mini")
            model_lower = model.lower()
            if model_lower == "openai" or model_lower.startswith("gpt"):
                response = await self._retry_with_backoff(
                    self._get_sentiment_analysis_openai, prompt
                )
            elif model_lower == "claude" or model_lower.startswith("claude") or model_lower == "anthropic":
                response = await self._retry_with_backoff(
                    self._get_sentiment_analysis_claude, prompt
                )
            elif model_lower == "gemini" or model_lower.startswith("gemini"):
                response = await self._retry_with_backoff(
                    self._get_sentiment_analysis_gemini, prompt
                )
            else:
                return {"error": f"Unsupported model: {model}"}
            
            # Add metadata
            response["metadata"] = {
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "articles_analyzed": len(formatted_news),
                "service": "LLMIntegrationService",
                "analysis_type": "sentiment"
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"error": f"Sentiment analysis failed: {str(e)}"}
    
    async def _get_sentiment_analysis_openai(self, prompt: str) -> Dict[str, Any]:
        """Get sentiment analysis from OpenAI"""
        if not self.openai_client:
            return {"error": "OpenAI client not available"}
        
        response = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model=self.openai_model,
            messages=[
                {"role": "system", "content": "You are a financial sentiment analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        return self._parse_llm_response(content)
    
    async def _get_sentiment_analysis_claude(self, prompt: str) -> Dict[str, Any]:
        """Get sentiment analysis from Claude"""
        if not self.claude_client:
            return {"error": "Claude client not available"}
        
        response = await asyncio.to_thread(
            self.claude_client.messages.create,
            model=self.claude_model,
            max_tokens=1000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        return self._parse_llm_response(content)
    
    async def _get_sentiment_analysis_gemini(self, prompt: str) -> Dict[str, Any]:
        """Get sentiment analysis from Gemini"""
        if not self.gemini_client:
            return {"error": "Gemini client not available"}
        
        response = await asyncio.to_thread(
            self.gemini_client.generate_content,
            prompt
        )
        
        content = response.text
        return self._parse_llm_response(content)
    
    async def comprehensive_analysis(self, symbol: str, timeframes_data: Dict[str, List[Dict]], 
                                   news_data: List[Dict[str, Any]] = None,
                                   model: str = "openai", bot_id: int = None) -> Dict[str, Any]:
        """
        Comprehensive market analysis combining technical analysis and sentiment
        
        Args:
            symbol: Trading symbol
            timeframes_data: OHLCV data for different timeframes
            news_data: Optional news data for sentiment analysis
            model: LLM to use
            
        Returns:
            Combined technical and sentiment analysis
        """
        try:
            # Get technical analysis
            technical_analysis = await self.analyze_market(symbol, timeframes_data, model, bot_id)
            
            # Get sentiment analysis if news data provided
            sentiment_analysis = None
            if news_data:
                sentiment_analysis = await self.analyze_sentiment(news_data, model)
            
            # Combine analyses
            comprehensive_result = {
                "technical_analysis": technical_analysis,
                "sentiment_analysis": sentiment_analysis,
                "combined_recommendation": self._combine_analyses(technical_analysis, sentiment_analysis),
                "metadata": {
                    "symbol": symbol,
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                    "analysis_type": "comprehensive",
                    "has_sentiment": sentiment_analysis is not None
                }
            }
            
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"Comprehensive analysis error: {e}")
            return {"error": f"Comprehensive analysis failed: {str(e)}"}
    
    def _combine_analyses(self, technical_analysis: Dict[str, Any], 
                         sentiment_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Combine technical and sentiment analyses into final recommendation"""
        try:
            # Start with technical analysis
            combined = {
                "action": "HOLD",
                "confidence": 0,
                "reasoning": "Insufficient data for analysis"
            }
            
            # Extract technical recommendation
            if technical_analysis and not technical_analysis.get("error"):
                tech_rec = technical_analysis.get("recommendation", {})
                combined["technical_action"] = tech_rec.get("action", "HOLD")
                combined["technical_confidence"] = int(tech_rec.get("confidence", 0))
                combined["technical_reasoning"] = tech_rec.get("reasoning", "")
                
                # Use technical as base
                combined["action"] = combined["technical_action"]
                combined["confidence"] = combined["technical_confidence"]
                combined["reasoning"] = combined["technical_reasoning"]
            
            # Incorporate sentiment if available
            if sentiment_analysis and not sentiment_analysis.get("error"):
                sent_data = sentiment_analysis
                combined["sentiment"] = sent_data.get("overall_sentiment", "NEUTRAL")
                combined["sentiment_confidence"] = int(sent_data.get("confidence", 50))
                combined["market_impact"] = sent_data.get("market_impact", "MEDIUM")
                
                # Adjust recommendation based on sentiment
                if combined["sentiment"] == "BULLISH" and combined["technical_action"] == "BUY":
                    combined["confidence"] = min(100, combined["confidence"] + 10)
                    combined["reasoning"] += " + Bullish sentiment confirmation"
                elif combined["sentiment"] == "BEARISH" and combined["technical_action"] == "SELL":
                    combined["confidence"] = min(100, combined["confidence"] + 10)
                    combined["reasoning"] += " + Bearish sentiment confirmation"
                elif combined["sentiment"] == "BEARISH" and combined["technical_action"] == "BUY":
                    combined["confidence"] = max(0, combined["confidence"] - 15)
                    combined["reasoning"] += " - Bearish sentiment conflict"
                elif combined["sentiment"] == "BULLISH" and combined["technical_action"] == "SELL":
                    combined["confidence"] = max(0, combined["confidence"] - 15)
                    combined["reasoning"] += " - Bullish sentiment conflict"
            
            # Final validation
            if combined["confidence"] < 55:
                combined["action"] = "HOLD"
                combined["reasoning"] = "Low confidence - holding position"
            
            return combined
            
        except Exception as e:
            logger.error(f"Error combining analyses: {e}")
            return {
                "action": "HOLD",
                "confidence": 0,
                "reasoning": f"Analysis combination error: {str(e)}"
            }
    
    async def get_capital_management_advice(self, capital_context: Dict[str, Any], 
                                          base_position_size: float, max_position_size: float,
                                          model: str = "openai", bot_id: int = None) -> Dict[str, Any]:
        """
        Get capital management and position sizing advice from LLM
        
        Args:
            capital_context: Account and market information for position sizing
            base_position_size: Base position size percentage
            max_position_size: Maximum allowed position size percentage
            model: LLM to use for analysis
            bot_id: Optional bot ID to use bot's attached risk management prompt
            
        Returns:
            Capital management recommendations
        """
        try:
            # Prepare capital management prompt (dynamic from bot's risk management prompt)
            prompt = self._get_capital_management_prompt(bot_id)
            
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
            # Support both provider type ("openai") and full model name ("gpt-4o-mini")
            model_lower = model.lower()
            if model_lower == "openai" or model_lower.startswith("gpt"):
                response = await self._get_capital_advice_openai(request_data)
            elif model_lower == "claude" or model_lower.startswith("claude") or model_lower == "anthropic":
                response = await self._get_capital_advice_claude(request_data)
            elif model_lower == "gemini" or model_lower.startswith("gemini"):
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
def create_llm_service(config: Dict[str, Any] = None, developer_id: int = None, db = None,
                       preferred_provider: str = None, bot_id: int = None) -> LLMIntegrationService:
    """
    Factory function to create LLM Integration Service
    
    Args:
        config: Optional configuration dict
        developer_id: Developer ID to load their configured LLM providers (BYOK)
        db: Database session for loading provider configs
        preferred_provider: Preferred provider ("openai", "claude", "gemini") - from bot config
        bot_id: Bot ID for logging
        
    Returns:
        LLMIntegrationService instance
    """
    return LLMIntegrationService(config=config, developer_id=developer_id, db=db,
                                 preferred_provider=preferred_provider, bot_id=bot_id)

# Test function
def test_llm_integration():
    """Test LLM integration service with enhanced features"""
    
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
    
    # Sample news data for sentiment analysis
    sample_news = [
        {
            "title": "Bitcoin Reaches New All-Time High",
            "content": "Bitcoin has reached a new all-time high of $52,000, driven by institutional adoption and positive market sentiment.",
            "timestamp": "2024-01-15T10:00:00Z",
            "source": "CryptoNews"
        },
        {
            "title": "Major Bank Announces Bitcoin Investment",
            "content": "A major investment bank has announced a $1 billion Bitcoin investment, signaling growing institutional confidence.",
            "timestamp": "2024-01-15T09:30:00Z",
            "source": "Financial Times"
        }
    ]
    
    # Initialize service with enhanced configuration
    config = {
        'enable_caching': True,
        'max_retries': 3,
        'retry_delay': 1.0,
        'timeout': 30
    }
    
    service = create_llm_service(config)
    
    print("✅ Enhanced LLM Integration Service initialized!")
    print(f"   OpenAI: {'✅' if service.openai_client else '❌'}")
    print(f"   Claude: {'✅' if service.claude_client else '❌'}")
    print(f"   Gemini: {'✅' if service.gemini_client else '❌'}")
    print(f"   Caching: {'✅' if service.enable_caching else '❌'}")
    print(f"   Max Retries: {service.max_retries}")
    print(f"   Timeout: {service.timeout}s")
    
    return service

async def test_enhanced_features():
    """Test enhanced LLM integration features"""
    service = test_llm_integration()
    
    # Test data
    sample_data = {
        "1h": [
            {"timestamp": 1640995200000, "open": 47000, "high": 48000, "low": 46500, "close": 47500, "volume": 1000},
            {"timestamp": 1640998800000, "open": 47500, "high": 49000, "low": 47000, "close": 48500, "volume": 1200}
        ]
    }
    
    sample_news = [
        {
            "title": "Bitcoin Bull Run Continues",
            "content": "Bitcoin shows strong momentum with institutional adoption increasing.",
            "timestamp": "2024-01-15T10:00:00Z",
            "source": "CryptoNews"
        }
    ]
    
    print("\n🧪 Testing Enhanced Features:")
    
    # Test 1: Basic market analysis
    print("\n1. Testing Market Analysis...")
    try:
        result = await service.analyze_market("BTC/USDT", sample_data, "gemini")
        print(f"   ✅ Market Analysis: {result.get('recommendation', {}).get('action', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Market Analysis failed: {e}")
    
    # Test 2: Sentiment Analysis
    print("\n2. Testing Sentiment Analysis...")
    try:
        result = await service.analyze_sentiment(sample_news, "gemini")
        print(f"   ✅ Sentiment: {result.get('overall_sentiment', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Sentiment Analysis failed: {e}")
    
    # Test 3: Comprehensive Analysis
    print("\n3. Testing Comprehensive Analysis...")
    try:
        result = await service.comprehensive_analysis("BTC/USDT", sample_data, sample_news, "gemini")
        combined = result.get('combined_recommendation', {})
        print(f"   ✅ Combined Analysis: {combined.get('action', 'N/A')} (Confidence: {combined.get('confidence', 0)}%)")
    except Exception as e:
        print(f"   ❌ Comprehensive Analysis failed: {e}")
    
    print("\n🎉 Enhanced LLM Integration testing completed!")

if __name__ == "__main__":
    test_llm_integration()
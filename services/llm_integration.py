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

class QuotaExceededException(Exception):
    """Raised when user exceeds LLM quota"""
    pass

class LLMIntegrationService:
    """
    LLM Integration Service for Crypto Trading Analysis
    Supports multiple AI models for advanced trading insights with Fibonacci analysis
    """
    
    def __init__(self, config: Dict[str, Any] = None, developer_id: int = None, db = None, 
                 preferred_provider: str = None, bot_id: int = None, subscription_id: int = None):
        """
        Initialize LLM Integration Service
        
        Args:
            config: Configuration with API keys and model settings
            developer_id: Developer ID to load their configured LLM providers (BYOK)
            db: Database session for loading provider configs
            preferred_provider: Preferred provider ("openai", "claude", "gemini") - from bot config
            bot_id: Bot ID for logging
            subscription_id: Subscription ID for usage tracking
        """
        self.config = config or {}
        self.developer_id = developer_id
        self.db = db
        self.bot_id = bot_id
        self.subscription_id = subscription_id
        
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
                
                if source_type in ["USER_CONFIGURED", "PLATFORM"]:
                    logger.info(f"✅ Using {source_type} LLM provider: {provider_config['provider']} ({provider_config['model']})")
                    
                    # Override config with provider (developer's or platform's)
                    # Extract the enum value and convert to uppercase for comparison
                    provider_enum = provider_config['provider']
                    provider_type = str(provider_enum.value).upper() if hasattr(provider_enum, 'value') else str(provider_enum).upper()
                    
                    if provider_type == 'OPENAI':
                        self.config['openai_api_key'] = provider_config['api_key']
                        self.config['openai_model'] = provider_config['model']
                    elif provider_type in ['ANTHROPIC', 'CLAUDE']:
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
                    logger.warning(f"⚠️ Unknown provider source type: {source_type}")
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
            source = "PLATFORM" if self._provider_config.get('is_platform_managed') else "DEVELOPER"
            logger.info(f"✅ LLM Integration initialized with {source} {self._provider_config['provider']} provider")
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
    
    def _log_llm_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        request_type: str = "market_analysis",
        success: bool = True,
        error_message: str = None,
        request_duration_ms: int = None,
        bot_id: int = None,
        task_type: str = None
    ):
        """
        Log LLM API usage to database
        
        Args:
            provider: Provider name (OPENAI, CLAUDE, GEMINI)
            model: Model name used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            request_type: Type of request (market_analysis, zone_finding, etc.)
            success: Whether request succeeded
            error_message: Error message if failed
            request_duration_ms: Request duration in milliseconds
            bot_id: Optional bot ID for reference
            task_type: Optional task type (reserved for future use)
        """
        if not self.developer_id or not self.db:
            logger.debug("Skipping usage logging - no developer_id or db session")
            return
        
        try:
            from services.llm_provider_selector import LLMProviderSelector
            from core import models
            
            # Use cached provider config from __init__ (already selected with preferred_provider)
            if not self._provider_config or not self._provider_selector:
                logger.warning("⚠️ No provider config cached, skipping usage logging")
                return
            
            provider_config = self._provider_config
            selector = self._provider_selector
            
            # Calculate cost based on LATEST VERIFIED pricing (per 1M tokens)
            # Source: Official provider pricing pages (verified October 2024)
            # Note: LLM providers do NOT return cost in API response, only token counts
            cost_usd = 0.0
            model_lower = model.lower()
            
            if provider.upper() == 'OPENAI':
                # OpenAI pricing (verified October 2024: openai.com/pricing)
                # Order matters: check specific models before generic ones
                if 'o1-mini' in model_lower:
                    # o1-mini: $3.00/1M input, $12.00/1M output
                    cost_usd = (input_tokens / 1_000_000 * 3.00) + (output_tokens / 1_000_000 * 12.00)
                elif 'o1-preview' in model_lower or model_lower == 'o1':
                    # o1-preview or o1: $15.00/1M input, $60.00/1M output
                    cost_usd = (input_tokens / 1_000_000 * 15.00) + (output_tokens / 1_000_000 * 60.00)
                elif 'gpt-4o-mini' in model_lower:
                    # gpt-4o-mini: $0.150/1M input, $0.600/1M output
                    cost_usd = (input_tokens / 1_000_000 * 0.150) + (output_tokens / 1_000_000 * 0.600)
                elif 'gpt-4o' in model_lower:
                    # gpt-4o: $2.50/1M input, $10.00/1M output
                    cost_usd = (input_tokens / 1_000_000 * 2.50) + (output_tokens / 1_000_000 * 10.00)
                elif 'gpt-4-turbo' in model_lower or 'gpt-4-1106' in model_lower:
                    # gpt-4-turbo: $10.00/1M input, $30.00/1M output
                    cost_usd = (input_tokens / 1_000_000 * 10.00) + (output_tokens / 1_000_000 * 30.00)
                elif 'gpt-4' in model_lower:
                    # gpt-4 (8K context): $30.00/1M input, $60.00/1M output
                    cost_usd = (input_tokens / 1_000_000 * 30.00) + (output_tokens / 1_000_000 * 60.00)
                elif 'gpt-3.5-turbo' in model_lower:
                    # gpt-3.5-turbo: $0.50/1M input, $1.50/1M output
                    cost_usd = (input_tokens / 1_000_000 * 0.50) + (output_tokens / 1_000_000 * 1.50)
                else:
                    # Default to gpt-4o-mini pricing (most cost-effective)
                    cost_usd = (input_tokens / 1_000_000 * 0.150) + (output_tokens / 1_000_000 * 0.600)
                    
            elif provider.upper() in ['CLAUDE', 'ANTHROPIC']:
                # Claude pricing (verified October 2024: docs.anthropic.com/pricing)
                # Order matters: check specific versions before generic names
                if 'opus' in model_lower:
                    # claude-3-opus-20240229: $15.00/1M input, $75.00/1M output
                    cost_usd = (input_tokens / 1_000_000 * 15.00) + (output_tokens / 1_000_000 * 75.00)
                elif ('3-7-sonnet' in model_lower or '3.7-sonnet' in model_lower or 
                      '3-5-sonnet' in model_lower or '3.5-sonnet' in model_lower or 
                      'sonnet' in model_lower):
                    # claude-3-7-sonnet-latest, claude-3-5-sonnet-*: $3.00/1M input, $15.00/1M output
                    # Note: >200K context has higher rates ($6/$22.50) but we use base rate
                    cost_usd = (input_tokens / 1_000_000 * 3.00) + (output_tokens / 1_000_000 * 15.00)
                elif ('3-5-haiku' in model_lower or '3.5-haiku' in model_lower):
                    # claude-3-5-haiku-20241022: $0.80/1M input, $4.00/1M output
                    cost_usd = (input_tokens / 1_000_000 * 0.80) + (output_tokens / 1_000_000 * 4.00)
                elif 'haiku' in model_lower:
                    # claude-3-haiku-20240307: $0.25/1M input, $1.25/1M output
                    cost_usd = (input_tokens / 1_000_000 * 0.25) + (output_tokens / 1_000_000 * 1.25)
                else:
                    # Default to Sonnet pricing
                    cost_usd = (input_tokens / 1_000_000 * 3.00) + (output_tokens / 1_000_000 * 15.00)
                    
            elif provider.upper() == 'GEMINI':
                # Gemini pricing (verified October 2024: ai.google.dev/pricing)
                # Order matters: check specific versions before generic names
                if '2.5' in model_lower and 'pro' in model_lower:
                    # gemini-2.5-pro: $1.25/1M input, $5.00/1M output
                    cost_usd = (input_tokens / 1_000_000 * 1.25) + (output_tokens / 1_000_000 * 5.00)
                elif '2.5' in model_lower and 'flash-lite' in model_lower:
                    # gemini-2.5-flash-lite: $0.038/1M input, $0.15/1M output
                    cost_usd = (input_tokens / 1_000_000 * 0.038) + (output_tokens / 1_000_000 * 0.15)
                elif '2.5' in model_lower and 'flash' in model_lower:
                    # gemini-2.5-flash: $0.075/1M input, $0.30/1M output
                    cost_usd = (input_tokens / 1_000_000 * 0.075) + (output_tokens / 1_000_000 * 0.30)
                elif '2.0' in model_lower and 'flash' in model_lower:
                    # gemini-2.0-flash-001: FREE during experimental phase
                    cost_usd = 0.0
                elif '1.5' in model_lower and 'pro' in model_lower:
                    # gemini-1.5-pro: $1.25/1M input, $5.00/1M output
                    cost_usd = (input_tokens / 1_000_000 * 1.25) + (output_tokens / 1_000_000 * 5.00)
                elif '1.5' in model_lower and 'flash' in model_lower:
                    # gemini-1.5-flash-002: $0.075/1M input, $0.30/1M output
                    cost_usd = (input_tokens / 1_000_000 * 0.075) + (output_tokens / 1_000_000 * 0.30)
                elif '1.0' in model_lower and 'pro' in model_lower:
                    # gemini-1.0-pro: $0.50/1M input, $1.50/1M output
                    cost_usd = (input_tokens / 1_000_000 * 0.50) + (output_tokens / 1_000_000 * 1.50)
                elif 'flash-lite' in model_lower:
                    # Default Flash Lite pricing (2.5 Flash Lite)
                    cost_usd = (input_tokens / 1_000_000 * 0.038) + (output_tokens / 1_000_000 * 0.15)
                elif 'flash' in model_lower:
                    # Default Flash pricing (2.5 Flash)
                    cost_usd = (input_tokens / 1_000_000 * 0.075) + (output_tokens / 1_000_000 * 0.30)
                elif 'pro' in model_lower:
                    # Default Pro pricing (2.5 Pro)
                    cost_usd = (input_tokens / 1_000_000 * 1.25) + (output_tokens / 1_000_000 * 5.00)
                else:
                    # Default to Flash pricing (most cost-effective non-free option)
                    cost_usd = (input_tokens / 1_000_000 * 0.075) + (output_tokens / 1_000_000 * 0.30)
            
            # Log usage
            selector.log_usage(
                developer_id=self.developer_id,
                provider_config=provider_config,
                bot_id=self.bot_id,
                subscription_id=self.subscription_id,
                request_type=request_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                success=success,
                error_message=error_message,
                request_duration_ms=request_duration_ms
            )
            
            logger.info(f"✅ Logged LLM usage: {provider}/{model} - {input_tokens + output_tokens} tokens (${cost_usd:.4f})")
            
        except Exception as e:
            logger.error(f"Failed to log LLM usage: {e}")
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks
        
        Args:
            content: Raw LLM response content
            
        Returns:
            Parsed JSON dict or None if parsing failed
        """
        try:
            # Remove markdown code blocks if present
            json_str = content.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            elif json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            json_str = json_str.strip()
            
            # Parse JSON
            parsed = json.loads(json_str)
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Content: {content[:500]}")
            return None
    
    def _format_final_prompt(self, strategy_prompt: str, market_data: Dict[str, Any], 
                            historical_transactions: List[Dict] = None, bot_id: int = None) -> str:
        """
        Format final prompt with clear separation between strategy instructions and market data
        
        Args:
            strategy_prompt: User's trading strategy + data guide
            market_data: Actual market data to analyze
            historical_transactions: Optional list of past transactions for learning
            bot_id: Optional bot ID to determine output format (SIGNALS vs STANDARD)
            
        Returns:
            Well-structured prompt with visual separators and historical context
        """
        # Determine if this is a SIGNALS_FUTURES bot
        is_signals_futures = False
        if bot_id:
            try:
                from core.database import get_db
                from core import crud
                
                db = next(get_db())
                bot = crud.get_bot_by_id(db, bot_id)
                bot_type_str = str(bot.bot_type).upper().strip() if bot and bot.bot_type else None
                if bot_type_str and "." in bot_type_str:
                    bot_type_str = bot_type_str.split(".")[-1]
                
                is_signals_futures = (bot_type_str == "SIGNALS_FUTURES")
            except Exception as e:
                logger.warning(f"Could not determine bot_type for bot {bot_id}: {e}")
        
        # Filter market data - only send indicators (no raw OHLCV)
        filtered_data = {
            'symbol': market_data.get('symbol'),
            'analysis_timestamp': market_data.get('analysis_timestamp'),
            'indicators': market_data.get('indicators', {})
        }
        
        # Base prompt with filtered market data
        prompt = f"""{strategy_prompt}

╔══════════════════════════════════════════════════════════════════╗
║ 📈 MARKET DATA TO ANALYZE                                        ║
╚══════════════════════════════════════════════════════════════════╝

{json.dumps(filtered_data, indent=2)}
"""
        
        # Add historical transactions section if available
        if historical_transactions and len(historical_transactions) > 0:
            historical_section = self._format_historical_section(historical_transactions)
            prompt += "\n" + historical_section
        
        # Add instructions recap
        prompt += """
═══════════════════════════════════════════════════════════════════
⚡ INSTRUCTIONS RECAP:
1. Analyze all indicators from data["indicators"][timeframe]
2. Check support/resistance levels, market structure, trend strength"""
        
        if historical_transactions and len(historical_transactions) > 0:
            prompt += "\n3. LEARN from historical_transactions (validate similar patterns)"
            prompt += "\n4. Apply YOUR STRATEGY rules above"
            prompt += "\n5. Return STRICT JSON format below"
        else:
            prompt += "\n3. Apply YOUR STRATEGY rules above"
            prompt += "\n4. Return STRICT JSON format below"
        
        prompt += "\n═══════════════════════════════════════════════════════════════════\n"
        
        # Add OUTPUT FORMAT as separate section at the end
        prompt += """
╔══════════════════════════════════════════════════════════════════╗
║ 📤 OUTPUT FORMAT (STRICT JSON SCHEMA)                           ║
╚══════════════════════════════════════════════════════════════════╝
"""
        
        if is_signals_futures:
            # SIGNALS_FUTURES format with SL/TP
            prompt += """
{
  "recommendation": {
    "action": "BUY" | "SELL" | "HOLD",
    "entry_price": "<numeric price>",
    "stop_loss": "<numeric price>",
    "take_profit": "<numeric price>",
    "risk_reward": "<string like '1:2' or null>",
    "strategy": "<MA, MACD, RSI, BollingerBands, Fibonacci_Retracement or combination>",
    "confidence": "<0-100>",
    "reasoning": "<DETAILED 3-5 sentences: analyze trend, entry, technical/fundamental reasons, risk management>",
    "market_volatility": "LOW" | "MEDIUM" | "HIGH"
  }
}

SIGNALS BOT REQUIREMENTS - CRITICAL:
• Entry Price: Use current market price or specific level from technical analysis
• Stop Loss: Set below entry for BUY (e.g., entry * 0.99), above for SELL (e.g., entry * 1.01)
• Take Profit: MUST BE DIFFERENT from entry!
  - For BUY: take_profit MUST be HIGHER than entry_price
  - For SELL: take_profit MUST be LOWER than entry_price
  - Example: If entry=3892, SL=3870 (risk=$22), then TP for 1:1 = 3892 + 22 = 3914
• Risk/Reward: Calculate as (TP - Entry) / (Entry - SL) for BUY
• Reasoning: DETAILED explanation with trend, entry rationale, risk considerations
• Market Volatility: Assess from ATR, volume, price swings
• RETURN ONLY VALID JSON - no text outside JSON structure

═══════════════════════════════════════════════════════════════════
"""
        else:
            # STANDARD format
            prompt += """
{
  "recommendation": {
    "action": "BUY" | "SELL" | "HOLD",
    "entry_price": "<string or null>",
    "strategy": "<MA, MACD, RSI, BollingerBands, Fibonacci_Retracement or combination>",
    "confidence": "<0-100>",
    "reasoning": "<briefly explain in 1–2 sentences why>"
  }
}

OUTPUT RULES:
• ONLY valid JSON - no text outside JSON structure
• HOLD actions: entry_price = null
• Confidence < 55%: FORCE action = "HOLD"
• No explanatory text, no markdown, pure JSON only

═══════════════════════════════════════════════════════════════════
"""
        
        return prompt
    
    def _format_historical_section(self, transactions: List[Dict]) -> str:
        """
        Format historical transactions for LLM learning
        
        Args:
            transactions: List of formatted transactions
            
        Returns:
            Formatted historical section for prompt
        """
        try:
            # Calculate statistics
            total = len(transactions)
            wins = sum(1 for t in transactions if t['result'] == 'WIN')
            losses = total - wins
            win_rate = (wins / total * 100) if total > 0 else 0
            
            avg_win = sum(t['profit_loss_pct'] for t in transactions if t['result'] == 'WIN') / wins if wins > 0 else 0
            avg_loss = sum(t['profit_loss_pct'] for t in transactions if t['result'] == 'LOSS') / losses if losses > 0 else 0
            risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            
            section = f"""
╔══════════════════════════════════════════════════════════════════╗
║ 🧠 HISTORICAL TRANSACTIONS (Learn from Past Performance)        ║
╚══════════════════════════════════════════════════════════════════╝

📊 **Performance Summary** (Last {total} Trades):
   • Win Rate: {win_rate:.1f}% ({wins} wins, {losses} losses)
   • Avg Win: +{avg_win:.2f}%
   • Avg Loss: {avg_loss:.2f}%
   • Risk/Reward: {risk_reward:.2f}:1

🎯 **Key Learnings**:
   • Identify patterns from winning trades
   • Avoid conditions that led to losses
   • Consider market conditions when those trades were made
   • Use this history to improve current decision

📋 **Recent Transactions** (Most recent first):
"""
            
            # Add transaction details (limit to top 10 for prompt brevity)
            for i, t in enumerate(transactions[:10], 1):
                result_emoji = "✅" if t['result'] == 'WIN' else "❌" if t['result'] == 'LOSS' else "⚖️"
                
                # Format indicators (take first 3 if available)
                indicators_str = "N/A"
                if t.get('indicators_used') and isinstance(t['indicators_used'], list):
                    indicators_str = ', '.join(t['indicators_used'][:3])
                elif t.get('indicators_used'):
                    indicators_str = str(t['indicators_used'])[:50]  # Limit length
                
                section += f"""
   {i}. {result_emoji} {t['side']} {t['symbol']} | {t['timeframe']}
      • Entry: ${t['entry_price']:.2f} → Exit: ${t['exit_price']:.2f}
      • PnL: {t['profit_loss_pct']:+.2f}% | Duration: {t.get('duration', 'N/A')}
      • Strategy: {t.get('strategy', 'N/A')[:50]}
      • Indicators: {indicators_str}
"""
            
            if total > 10:
                section += f"\n   ... and {total - 10} more transactions\n"
            
            section += """
⚠️ **CRITICAL - Use this historical context to**:
   1. Validate if current market conditions match past winners
   2. Avoid repeating mistakes from losing trades
   3. Adjust confidence based on similar past scenarios
   4. Consider if strategy performed well in similar conditions
   5. Look for volume, indicator, and price patterns that worked/failed
"""
            
            return section
        
        except Exception as e:
            logger.error(f"Error formatting historical section: {e}")
            return ""
    
    def _generate_data_structure_guide(self, timeframes: list, indicators_analysis: Dict[str, Dict[str, Any]] = None, 
                                        has_historical_data: bool = False) -> str:
        """
        Generate dynamic data structure guide based on available indicators and historical transactions
        
        Args:
            timeframes: List of timeframes
            indicators_analysis: Indicators data to detect available indicators
            has_historical_data: Whether historical transactions are available
        """
        formatted_timeframes = ", ".join([tf.upper() for tf in timeframes])
        
        # Detect available indicators DYNAMICALLY from actual data
        available_indicators = []
        indicator_categories = {
            'momentum': [],
            'trend': [],
            'volatility': [],
            'volume': [],
            'levels': []
        }
        
        if indicators_analysis:
            # Check first timeframe for available indicators
            first_tf = list(indicators_analysis.keys())[0] if indicators_analysis else None
            if first_tf:
                # Check for nested 'indicators' key (from bot's multi_timeframe structure)
                if 'indicators' in indicators_analysis[first_tf]:
                    ind_data = indicators_analysis[first_tf]['indicators']
                else:
                    # Direct structure (from market_data after prepare_market_data)
                    ind_data = indicators_analysis[first_tf]
                
                # Map of indicator patterns to their display names and categories
                indicator_mapping = {
                    # Momentum indicators
                    'rsi': ('RSI (Relative Strength Index)', 'momentum'),
                    'stochastic': ('Stochastic Oscillator', 'momentum'),
                    'williams': ('Williams %R', 'momentum'),
                    'cci': ('Commodity Channel Index (CCI)', 'momentum'),
                    'roc': ('Rate of Change (ROC)', 'momentum'),
                    'mfi': ('Money Flow Index (MFI)', 'momentum'),
                    
                    # Trend indicators
                    'macd': ('MACD (line, signal, histogram)', 'trend'),
                    'sma': ('Moving Averages (SMA)', 'trend'),
                    'ema': ('Exponential Moving Averages (EMA)', 'trend'),
                    'adx': ('Average Directional Index (ADX)', 'trend'),
                    'supertrend': ('Supertrend', 'trend'),
                    'ichimoku': ('Ichimoku Cloud', 'trend'),
                    
                    # Volatility indicators
                    'atr': ('ATR (Average True Range)', 'volatility'),
                    'bollinger': ('Bollinger Bands (upper, middle, lower)', 'volatility'),
                    'bb_': ('Bollinger Bands', 'volatility'),
                    'keltner': ('Keltner Channels', 'volatility'),
                    'donchian': ('Donchian Channels', 'volatility'),
                    
                    # Volume indicators
                    'volume': ('Volume Analysis', 'volume'),
                    'obv': ('On-Balance Volume (OBV)', 'volume'),
                    'cmf': ('Chaikin Money Flow (CMF)', 'volume'),
                    'vwma': ('Volume Weighted MA (VWMA)', 'volume'),
                    
                    # Support/Resistance levels
                    'pivot': ('Pivot Points', 'levels'),
                    'fibonacci': ('Fibonacci Levels', 'levels'),
                    'parabolic': ('Parabolic SAR', 'levels'),
                }
                
                # Detect all indicators by scanning keys
                detected = set()  # Track what we've already added
                for key in ind_data.keys():
                    key_lower = key.lower()
                    
                    # Skip meta fields
                    if key_lower in ['current_price', 'timestamp', 'trend_bullish', 
                                      'rsi_oversold', 'rsi_overbought', 'macd_bullish',
                                      'volatility']:
                        continue
                    
                    # Try to match with known patterns
                    matched = False
                    for pattern, (display_name, category) in indicator_mapping.items():
                        if pattern in key_lower and display_name not in detected:
                            indicator_categories[category].append(display_name)
                            detected.add(display_name)
                            matched = True
                            break
                    
                    # If no match, add as generic indicator (for user's custom indicators)
                    if not matched and key not in ['current_price', 'timestamp']:
                        generic_name = f"{key.replace('_', ' ').title()}"
                        if generic_name not in detected:
                            indicator_categories['momentum'].append(generic_name)
                            detected.add(generic_name)
                
                # Build categorized list
                for category, indicators in indicator_categories.items():
                    if indicators:
                        # Remove duplicates and sort
                        indicators = sorted(list(set(indicators)))
                        available_indicators.extend(indicators)
                
                # Log detected indicators
                total_detected = len(available_indicators)
                logger.info(f"📊 Detected {total_detected} indicator types in data")
                if available_indicators:
                    logger.info(f"   Available: {', '.join([ind.split('(')[0].strip() for ind in available_indicators[:5]])}{'...' if total_detected > 5 else ''}")
        
        indicators_list = "\n   - ".join(available_indicators) if available_indicators else "Will be calculated from OHLCV data"
        
        # Generate dynamic access examples based on actual indicators
        access_examples = []
        if indicators_analysis and first_tf:
            # Get actual indicator keys
            if 'indicators' in indicators_analysis[first_tf]:
                ind_data = indicators_analysis[first_tf]['indicators']
            else:
                ind_data = indicators_analysis[first_tf]
            
            # Generate examples for first few indicators (max 5)
            example_keys = [k for k in ind_data.keys() if k not in 
                           ['current_price', 'timestamp', 'trend_bullish', 
                            'rsi_oversold', 'rsi_overbought', 'macd_bullish', 'volatility']][:5]
            
            for key in example_keys:
                access_examples.append(f'       {key} = data["indicators"]["1h"]["{key}"]')
        
        # Fallback examples if no indicators detected
        if not access_examples:
            access_examples = [
                '       rsi = data["indicators"]["1h"]["rsi"]',
                '       macd = data["indicators"]["1h"]["macd"]',
                '       sma_20 = data["indicators"]["1h"]["sma_20"]'
            ]
        
        examples_text = "\n".join(access_examples)
        
        # Add historical data section if available
        historical_section = ""
        historical_step = ""
        step_adjust = ""
        
        if has_historical_data:
            historical_section = """
   
3. **HISTORICAL TRANSACTIONS** (Past Performance Data)
   - Win/Loss record, P&L percentages, strategy performance
   - Use for: Learning from past mistakes, validating current strategy, pattern recognition
   - Location: Separate section below market data"""
            
            historical_step = """

STEP 4: LEARN FROM HISTORICAL TRANSACTIONS (if provided)
   • Review past win/loss patterns for similar market conditions
   • Identify what indicators/strategies worked or failed
   • Validate if current signals match past winners or losers
   • Adjust confidence based on historical performance
   • Avoid repeating mistakes from losing trades"""
   
            step_adjust = " + Historical Learning"
        
        guide = f"""
╔══════════════════════════════════════════════════════════════════╗
║ 📊 DATA STRUCTURE GUIDE                                          ║
╚══════════════════════════════════════════════════════════════════╝

1. **PRE-CALCULATED TECHNICAL INDICATORS** (timeframes: {formatted_timeframes})
   - {indicators_list}
   
2. **ADVANCED MARKET ANALYSIS**:
   - Support/Resistance levels (price, strength, touches)
   - Market Structure (phase, pattern, breakout detection)
   - Trend Strength (strength, direction, divergence %)
   - Bollinger Bands (upper, middle, lower)
   - Pivot Points{historical_section}

⚡ CRITICAL INSTRUCTIONS:
   • ALL indicators are PRE-CALCULATED - use values directly from data["indicators"]
   • Access pattern: data["indicators"][timeframe][indicator_name]
   • Multi-timeframe analysis: Check ALL timeframes for confluence{step_adjust}

───────────────────────────────────────────────────────────────────
🎯 HOW TO USE THE DATA:

STEP 1: ACCESS PRE-CALCULATED INDICATORS
   # All indicators are pre-calculated and ready to use
   # Access pattern: data["indicators"][timeframe][indicator_name]
   
   # Examples based on YOUR available indicators:
{examples_text}

STEP 2: ANALYZE MARKET STRUCTURE
   • Check price_levels: Support/resistance strength and touches
   • Check market_structure: Phase (trending/ranging/consolidation)
   • Check trend_strength: Direction and divergence percentage
   • Identify patterns: triangles, channels, breakout signals

STEP 3: COMBINE INDICATORS FOR BETTER DECISIONS
   A. Momentum Confirmation:
      • RSI + MACD + CMF = Strong momentum signal
      • Multiple oscillators agreeing = Higher confidence
   
   B. Entry/Exit Optimization:
      • Price near support + RSI oversold = BUY opportunity
      • Price near resistance + RSI overbought = SELL signal
      • Bollinger Bands squeeze + volume spike = Breakout trade

⚠️ IMPORTANT CHECKS:
   ✓ Volume confirmation: volume_ratio > 1.1 for entry signals
   ✓ Multi-timeframe alignment: Check ALL timeframes agree on trend
   ✓ RSI range: Avoid extreme zones (>75 or <25)
   ✓ Trend confirmation: trend_bullish + trend_strength direction
   ✓ Support/Resistance: Check "major" strength levels (5+ touches)

═══════════════════════════════════════════════════════════════════
"""
        return guide
    
    def _get_analysis_prompt(self, bot_id: int = None, timeframes: list = None, 
                            indicators_analysis: Dict[str, Dict[str, Any]] = None,
                            historical_transactions: List[Dict] = None) -> str:
        """
        Get dynamic trading analysis prompt from bot's attached prompt template
        
        Args:
            bot_id: Bot ID to get custom prompt
            timeframes: List of timeframes being analyzed
            indicators_analysis: Available indicators data for dynamic guide generation
            historical_transactions: Historical transaction data for learning
        """
        # Default timeframes if not provided - Optimized 3 timeframes
        if not timeframes:
            timeframes = ["30M", "1H", "4H"]
        
        # Format timeframes for display (e.g., ['5m', '30m', '1h'] -> "5M, 30M, 1H")
        formatted_timeframes = ", ".join([tf.upper() for tf in timeframes])
        
        logger.info(f"🔍 _get_analysis_prompt called with bot_id={bot_id}, timeframes={timeframes}")
        
        # Check if historical data is available
        has_historical_data = historical_transactions and len(historical_transactions) > 0
        
        # Generate dynamic data structure guide
        data_guide = self._generate_data_structure_guide(timeframes, indicators_analysis, has_historical_data)
        
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
                        
                        # Prepend data structure guide and add clear strategy header
                        strategy_header = """
╔══════════════════════════════════════════════════════════════════╗
║ 🎯 YOUR TRADING STRATEGY                                         ║
╚══════════════════════════════════════════════════════════════════╝
"""
                        bot_prompt = data_guide + "\n" + strategy_header + "\n" + bot_prompt
                        
                        logger.info(f"Using dynamic prompt from bot {bot_id} (bot_type={bot_type_str}) - OUTPUT FORMAT will be added by _format_final_prompt")
                        logger.info(f"📄 Strategy prompt length: {len(bot_prompt)} chars")
                        return bot_prompt
                        
            except Exception as e:
                logger.error(f"❌ Failed to get bot prompt for bot {bot_id}: {e}")
                import traceback
                traceback.print_exc()
                # Fall back to default prompt
        
        # Fallback to default prompt if no bot_id or error
        logger.warning(f"⚠️  Using DEFAULT prompt (bot_id={bot_id})")
        # Default prompt already has data guide built-in
        return self._get_default_analysis_prompt(timeframes)
    
    def _get_default_analysis_prompt(self, timeframes: list) -> str:
        """Get the default high-quality trading analysis prompt"""
        # Format timeframes for display
        formatted_timeframes = ", ".join([tf.upper() for tf in timeframes])
        
        return f"""You are a professional cryptocurrency trading engine. Analyze market data to make autonomous BUY/SELL/HOLD decisions.

═══════════════════════════════════════════════════════════════════
📊 DATA PROVIDED TO YOU:
═══════════════════════════════════════════════════════════════════

1. **PRE-CALCULATED TECHNICAL INDICATORS** (timeframes: {formatted_timeframes})
   - RSI (Relative Strength Index)
   - MACD (line, signal, histogram)
   - Moving Averages (SMA, EMA)
   - Bollinger Bands (upper, middle, lower)
   - Volume analysis (volume_ratio, CMF)
   - Volatility (ATR)
   
2. **ADVANCED MARKET ANALYSIS**:
   - Support/Resistance levels (price, strength, touches)
   - Market Structure (phase, pattern, breakout detection)
   - Trend Strength (strength, direction, divergence %)
   - Pivot Points
   
⚡ IMPORTANT: ALL indicators are PRE-CALCULATED. Use values directly from data["indicators"][timeframe].

═══════════════════════════════════════════════════════════════════
🎯 ANALYSIS WORKFLOW (STRICT ORDER):
═══════════════════════════════════════════════════════════════════

STEP 1: VOLUME VALIDATION ⚠️ MANDATORY FIRST
────────────────────────────────────────────────────────────────
✓ Check volume_ratio in indicators
✓ Volume Check: volume_ratio MUST be ≥ 1.1 (110% of average)
  → If volume fails: IMMEDIATELY return HOLD (no further analysis)

STEP 2: MULTI-TIMEFRAME TREND CONFIRMATION 📈
────────────────────────────────────────────────────────────────
Analyze EACH timeframe using pre-calculated indicators:
  A. Trend Direction:
     • Check trend_bullish and trend_strength
     • Check market_structure.phase (trending/ranging/consolidation)
  
  B. Moving Average Alignment:
     • BULLISH: current_price > sma_20 > sma_50 AND ema_12 > ema_26
     • BEARISH: current_price < sma_20 < sma_50 AND ema_12 < ema_26
     • Check trend_strength.direction for confirmation
  
  C. Consensus Rule:
     • BUY: At least 2/3 timeframes show bullish alignment
     • SELL: At least 2/3 timeframes show bearish alignment
     • HOLD: Conflicting trends or sideways action

STEP 3: MOMENTUM & OSCILLATORS ANALYSIS 🎢
────────────────────────────────────────────────────────────────
Use pre-calculated indicators directly:

  RSI (14-period):
  ✓ BUY Zone: 40-65 (healthy bullish momentum)
  ✓ SELL Zone: 35-60 (healthy bearish momentum)  
  ✓ AVOID: RSI >75 (extreme overbought) or <25 (extreme oversold)
  ✓ Divergences: Price vs RSI divergence = strong signal

  MACD:
  ✓ BUY: MACD > Signal line + histogram expanding upward
  ✓ SELL: MACD < Signal line + histogram expanding downward
  ✓ PRIORITY: Recent crossovers within 1-3 candles
  ✓ Zero-line crossovers = momentum shift confirmation

STEP 4: SUPPORT/RESISTANCE & PRICE LEVELS 🎯
────────────────────────────────────────────────────────────────
Combine OHLCV patterns with indicator levels:

  From OHLCV Historical Data:
  • Identify recent swing highs/lows (last 20 candles)
  • Find consolidation zones (price clustering)
  • Detect breakouts or fakeouts
  
  From Bollinger Bands (indicators):
  • BUY: Price bounces from Lower BB OR breaks Middle BB upward with volume
  • SELL: Price bounces from Upper BB OR breaks Middle BB downward with volume
  • AVOID: Price in middle 33% of BB range (no clear signal)
  
  Key Levels Validation:
  ✓ Price must be at/near significant support (for BUY) or resistance (for SELL)
  ✓ Previous level touches increase significance (2+ touches better)

STEP 5: FIBONACCI & ADVANCED PATTERNS (BONUS) 🌟
────────────────────────────────────────────────────────────────
If clear trend exists in OHLCV data:
  • Identify swing high to swing low (or vice versa)
  • PRIORITY ZONES: 0.382, 0.5, 0.618 retracement levels
  • BONUS POINTS: Entry within ±0.5% of Fib level
  • Combine with support/resistance for confluence

STEP 6: FINAL SIGNAL GENERATION 🎲
────────────────────────────────────────────────────────────────
Combine ALL analysis above:
  
  Signal Strength Matrix:
  ┌─────────────────────────────────────────────────────────┐
  │ STRONG BUY:  4+ bullish signals + volume confirmation  │
  │ MODERATE BUY: 3 bullish signals + adequate volume      │
  │ WEAK BUY:    2 bullish signals + minimum volume        │
  │ HOLD:        Mixed signals OR failed volume check      │
  │ WEAK SELL:   2 bearish signals + minimum volume        │
  │ MODERATE SELL: 3 bearish signals + adequate volume     │
  │ STRONG SELL: 4+ bearish signals + volume confirmation  │
  └─────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════
🚫 EXCLUSION CRITERIA (AUTOMATIC HOLD):
═══════════════════════════════════════════════════════════════════
• Volume insufficient (< 110% of average)
• Extreme RSI (>75 or <25) without clear reversal pattern
• Conflicting timeframes (no 2/3 agreement)
• Sideways consolidation (price within 1.5% range for 10+ candles)
• Recent false breakout (failed breakout within 5 candles)
• Low volatility (ATR < 0.8% of current price)

═══════════════════════════════════════════════════════════════════
📊 CONFIDENCE SCORING:
═══════════════════════════════════════════════════════════════════
90-100%: 5+ indicators agree + volume spike (>150%) + clear trend + price at key level
75-89%:  4 indicators agree + good volume (>130%) + trend confirmation + pattern support
60-74%:  3 indicators agree + adequate volume (>110%) + some trend signals
55-59%:  2 indicators agree + minimum volume + weak signals
<55%:    HOLD - insufficient setup quality

═══════════════════════════════════════════════════════════════════
✅ FINAL VALIDATION CHECKLIST:
═══════════════════════════════════════════════════════════════════
Before outputting BUY/SELL:
  ✓ Volume > 110% average?
  ✓ 2/3 timeframes agree on trend?
  ✓ RSI in valid range (not extreme)?
  ✓ Clear support/resistance level nearby?
  ✓ Confidence ≥ 55%?
  ✓ No conflicting signals from indicators?
  
IF ANY CHECKBOX FAILS → Return HOLD

═══════════════════════════════════════════════════════════════════
📥 MARKET DATA:
═══════════════════════════════════════════════════════════════════"""
    
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
    
    def prepare_market_data(self, symbol: str, timeframes_data: Dict[str, List[Dict]], 
                           indicators_analysis: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepare market data for LLM analysis
        
        Args:
            symbol: Trading symbol
            timeframes_data: Raw OHLCV data
            indicators_analysis: Calculated indicators for each timeframe
        """
        try:
            formatted_data = {
                "symbol": symbol,
                "analysis_timestamp": datetime.now().isoformat(),
                "timeframes": timeframes_data
            }
            
            # Add indicators if available
            if indicators_analysis:
                formatted_data["indicators"] = {}
                indicators_count = 0
                for timeframe, indicators in indicators_analysis.items():
                    # Clean indicators data - remove historical_data to reduce size
                    cleaned_indicators = {k: v for k, v in indicators.items() if k != 'historical_data'}
                    formatted_data["indicators"][timeframe] = cleaned_indicators
                    
                    # Count indicator types
                    if 'indicators' in indicators:
                        indicators_count += len(indicators['indicators'])
                
                logger.info(f"📊 Added pre-calculated indicators for {len(indicators_analysis)} timeframes to LLM prompt")
                logger.info(f"   → Indicators attached: RSI, MACD, Moving Averages, Bollinger Bands, Volume analysis")
                logger.info(f"   → LLM will USE these indicators directly (no re-calculation needed)")
            else:
                logger.warning(f"⚠️  No indicators provided - LLM will calculate from OHLCV data")
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error preparing market data: {e}")
            return {}
    
    def _check_quota(self, developer_id: int) -> bool:
        """
        Check if user has remaining LLM quota
        
        Args:
            developer_id: Developer ID to check quota for
            
        Returns:
            bool: True if quota available, False if exceeded
            
        Raises:
            QuotaExceededException: If quota is exceeded
        """
        if not self.db or not developer_id:
            logger.warning("⚠️ No database or developer_id provided for quota check")
            return True  # Allow if no quota system available
        
        try:
            from core import models
            
            # Get user's plan
            user_plan = self.db.query(models.UserPlan).filter(
                models.UserPlan.user_id == developer_id,
                models.UserPlan.status == models.PlanStatus.ACTIVE
            ).first()
            
            if not user_plan:
                logger.warning(f"⚠️ No active plan found for developer {developer_id}")
                return True  # Allow if no plan found
            
            # Check if quota has expired (reset period)
            if user_plan.llm_quota_reset_at and user_plan.llm_quota_reset_at < datetime.now():
                logger.info(f"🔄 Quota expired for developer {developer_id}, resetting...")
                # Reset quota
                user_plan.llm_quota_used = 0
                user_plan.llm_quota_reset_at = datetime.now() + timedelta(days=30)
                self.db.commit()
                logger.info(f"✅ Quota reset for developer {developer_id}")
            
            # Check remaining quota
            remaining = user_plan.llm_quota_total - user_plan.llm_quota_used
            if remaining <= 0:
                logger.warning(f"❌ Quota exceeded for developer {developer_id}: {user_plan.llm_quota_used}/{user_plan.llm_quota_total}")
                
                # Send notification to developer
                self._send_quota_exhausted_notification(developer_id, user_plan)
                
                raise QuotaExceededException(
                    f"LLM quota exceeded. Used: {user_plan.llm_quota_used}/{user_plan.llm_quota_total}. "
                    f"Please upgrade your plan or purchase additional quota."
                )
            
            logger.info(f"✅ Quota check passed for developer {developer_id}: {remaining} calls remaining")
            return True
            
        except QuotaExceededException:
            # Re-raise QuotaExceededException to block LLM calls
            raise
        except Exception as e:
            logger.error(f"❌ Error checking quota for developer {developer_id}: {e}")
            # Allow execution if quota check fails for other reasons (fail open)
            return True
    
    def _send_quota_exhausted_notification(self, developer_id: int, user_plan):
        """
        Send notification to developer when quota is exhausted
        Rate-limited to avoid spam (max 1 notification per hour per user)
        
        Args:
            developer_id: Developer ID
            user_plan: UserPlan object with quota info
        """
        try:
            from core import models
            
            # Get user info
            user = self.db.query(models.User).filter(
                models.User.id == developer_id
            ).first()
            
            if not user:
                logger.warning(f"⚠️ User {developer_id} not found for notification")
                return
            
            # Rate limiting: Check if notification was sent recently (within last hour)
            cache_key = f"quota_notification_sent:{developer_id}"
            # Use a simple in-memory check with datetime
            if not hasattr(self, '_notification_cache'):
                self._notification_cache = {}
            
            last_sent = self._notification_cache.get(cache_key)
            if last_sent and (datetime.now() - last_sent).total_seconds() < 3600:
                logger.info(f"⏭️ Skipping quota notification for user {developer_id} (sent recently)")
                return
            
            # Mark notification as sent
            self._notification_cache[cache_key] = datetime.now()
            
            # Generate top-up link
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            topup_link = f"{frontend_url}/dashboard#quota"
            
            # Prepare notification message
            message = f"""
🚨 **LLM Quota Exhausted**

Your LLM quota has been exhausted:
- Used: {user_plan.llm_quota_used}/{user_plan.llm_quota_total} calls
- Plan: {user_plan.plan_name.value.upper()}
- Reset Date: {user_plan.llm_quota_reset_at.strftime('%Y-%m-%d') if user_plan.llm_quota_reset_at else 'N/A'}

Your bots using LLM features will be paused until you purchase more quota.

**Top-up Options:**
• $20 → 300 calls
• $50 → 700 calls  
• $100 → 1500 calls

👉 **Purchase More Quota:** {topup_link}

Need help? Contact support or upgrade your plan.
            """.strip()
            
            # Send Telegram notification
            if user.telegram_chat_id:
                try:
                    # Try to use Telegram bot if available
                    telegram_enabled = os.getenv('ENABLE_TELEGRAM_BOT', 'false').lower() == 'true'
                    if telegram_enabled:
                        from services.telegram_service import TelegramService
                        telegram_service = TelegramService()
                        
                        telegram_message = (
                            f"🚨 *LLM Quota Exhausted*\n\n"
                            f"Used: {user_plan.llm_quota_used}/{user_plan.llm_quota_total} calls\n"
                            f"Plan: {user_plan.plan_name.value.upper()}\n\n"
                            f"Your bots are paused\\. Purchase more quota to continue\\.\n\n"
                            f"💎 *Top\\-up Options:*\n"
                            f"• $20 → 300 calls\n"
                            f"• $50 → 700 calls\n"
                            f"• $100 → 1500 calls\n\n"
                            f"👉 [Buy Quota]({topup_link})"
                        )
                        
                        telegram_service.send_message(user.telegram_chat_id, telegram_message)
                        logger.info(f"✅ Telegram notification sent to user {developer_id}")
                    else:
                        logger.info(f"📱 Telegram notification (would be sent to chat_id: {user.telegram_chat_id})")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send Telegram notification: {e}")
            
            # Send Discord notification
            if user.discord_user_id:
                try:
                    # Discord notifications not yet implemented
                    logger.info(f"💬 Discord notification (would be sent to user_id: {user.discord_user_id})")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send Discord notification: {e}")
            
            # Send Email notification
            if user.email:
                try:
                    email_subject = "🚨 LLM Quota Exhausted - Action Required"
                    display_name = user.developer_name or user.email.split('@')[0] if user.email else f"User {developer_id}"
                    email_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; border-radius: 10px;">
        <h2 style="color: #ef4444;">🚨 LLM Quota Exhausted</h2>
        
        <p>Hello {display_name},</p>
        
        <p>Your LLM quota has been exhausted:</p>
        
        <div style="background-color: #fff; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <ul style="list-style: none; padding: 0;">
                <li>📊 <strong>Used:</strong> {user_plan.llm_quota_used}/{user_plan.llm_quota_total} calls</li>
                <li>💎 <strong>Plan:</strong> {user_plan.plan_name.value.upper()}</li>
                <li>🔄 <strong>Reset Date:</strong> {user_plan.llm_quota_reset_at.strftime('%Y-%m-%d') if user_plan.llm_quota_reset_at else 'N/A'}</li>
            </ul>
        </div>
        
        <p style="color: #dc2626; font-weight: bold;">⚠️ Your bots using LLM features are currently paused.</p>
        
        <h3 style="color: #7c3aed;">💎 Top-up Options:</h3>
        <div style="background-color: #fff; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <ul>
                <li><strong>$20</strong> → 300 calls</li>
                <li><strong>$50</strong> → 700 calls</li>
                <li><strong>$100</strong> → 1500 calls</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{topup_link}" 
               style="display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%); 
                      color: white; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                💳 Purchase More Quota
            </a>
        </div>
        
        <p style="color: #666; font-size: 14px;">
            Need help? Contact our support team or upgrade your plan for higher quota limits.
        </p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        
        <p style="color: #999; font-size: 12px; text-align: center;">
            This is an automated notification from QuantumForge AI Trading Platform.
        </p>
    </div>
</body>
</html>
                    """.strip()
                    
                    # Try to send email using existing email service
                    try:
                        from services.email_service import EmailService
                        email_service = EmailService()
                        email_service.send_email(
                            to_email=user.email,
                            subject=email_subject,
                            html_content=email_body
                        )
                        logger.info(f"✅ Email notification sent to user {developer_id}")
                    except ImportError:
                        logger.info(f"📧 Email notification (would be sent to {user.email}):")
                        logger.info(f"   Subject: {email_subject}")
                        logger.info(f"   To: {user.email}")
                except Exception as e:
                    logger.error(f"❌ Failed to send email notification: {e}")
            
            # Log notification
            display_name = user.developer_name or user.email or f"User {developer_id}"
            logger.info(f"📧 Quota exhausted notification sent to developer {developer_id} ({display_name})")
            
        except Exception as e:
            logger.error(f"❌ Error sending quota exhausted notification: {e}")
    
    def _decrement_quota(self, developer_id: int):
        """
        Decrement user's LLM quota by 1 after successful API call
        
        Args:
            developer_id: Developer ID to decrement quota for
        """
        if not self.db or not developer_id:
            logger.warning("⚠️ No database or developer_id provided for quota decrement")
            return
        
        try:
            from core import models
            
            # Get user's plan
            user_plan = self.db.query(models.UserPlan).filter(
                models.UserPlan.user_id == developer_id,
                models.UserPlan.status == models.PlanStatus.ACTIVE
            ).first()
            
            if user_plan:
                user_plan.llm_quota_used += 1
                self.db.commit()
                remaining = user_plan.llm_quota_total - user_plan.llm_quota_used
                logger.info(f"📉 Quota decremented for developer {developer_id}: {user_plan.llm_quota_used}/{user_plan.llm_quota_total} ({remaining} remaining)")
                
                # Send warning notifications at certain thresholds
                if remaining <= 50 and remaining > 0:
                    logger.warning(f"⚠️ Low quota warning for developer {developer_id}: {remaining} calls remaining")
                elif remaining == 0:
                    logger.warning(f"🚨 Quota exhausted for developer {developer_id}")
            else:
                logger.warning(f"⚠️ No active plan found for developer {developer_id} to decrement quota")
                
        except Exception as e:
            logger.error(f"❌ Error decrementing quota for developer {developer_id}: {e}")
    
    async def analyze_with_openai(self, market_data: Dict[str, Any], bot_id: int = None,
                                  historical_transactions: List[Dict] = None) -> Dict[str, Any]:
        """Analyze market data using OpenAI with optional historical learning"""
        if not self.openai_client:
            return {"error": "OpenAI client not available"}
        
        # Check quota before making API call
        if self.developer_id:
            try:
                self._check_quota(self.developer_id)
            except QuotaExceededException as e:
                logger.warning(f"❌ Quota exceeded for developer {self.developer_id}: {e}")
                return {"error": "quota_exceeded", "message": str(e)}
        
        start_time = time.time()
        try:
            # Extract timeframes and indicators from market_data
            timeframes = list(market_data.get("timeframes", {}).keys())
            indicators_from_data = market_data.get("indicators", None)
            
            # Generate dynamic prompt based on actual timeframes, bot_id, available indicators, and historical data
            strategy_prompt = self._get_analysis_prompt(bot_id, timeframes, indicators_from_data, historical_transactions)
            
            # Format final prompt with clear sections and historical context
            prompt = self._format_final_prompt(strategy_prompt, market_data, historical_transactions, bot_id)
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": f"You are a professional trading engine. Analyze the following indicator schema for timeframes: {', '.join(timeframes)} to determine the current market phase and possible trigger zones for BUY or SELL entries. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Log usage
            duration_ms = int((time.time() - start_time) * 1000)
            input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
            output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0
            
            self._log_llm_usage(
                provider='OPENAI',
                model=self.openai_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_type='market_analysis',
                success=True,
                request_duration_ms=duration_ms
            )
            
            # Decrement quota after successful API call
            if self.developer_id:
                self._decrement_quota(self.developer_id)
            
            content = response.choices[0].message.content
            return self._parse_llm_response(content)
            
        except Exception as e:
            # Log failed request
            duration_ms = int((time.time() - start_time) * 1000)
            self._log_llm_usage(
                provider='OPENAI',
                model=self.openai_model,
                input_tokens=0,
                output_tokens=0,
                request_type='market_analysis',
                success=False,
                error_message=str(e),
                request_duration_ms=duration_ms
            )
            
            logger.error(f"OpenAI analysis error: {e}")
            return {"error": f"OpenAI analysis failed: {str(e)}"}
    
    async def analyze_with_claude(self, market_data: Dict[str, Any], bot_id: int = None,
                                  historical_transactions: List[Dict] = None) -> Dict[str, Any]:
        """Analyze market data using Claude with optional historical learning"""
        if not self.claude_client:
            return {"error": "Claude client not available"}
        
        # Check quota before making API call
        if self.developer_id:
            try:
                self._check_quota(self.developer_id)
            except QuotaExceededException as e:
                logger.warning(f"❌ Quota exceeded for developer {self.developer_id}: {e}")
                return {"error": "quota_exceeded", "message": str(e)}
        
        start_time = time.time()
        try:
            # Extract timeframes and indicators from market_data
            timeframes = list(market_data.get("timeframes", {}).keys())
            indicators_from_data = market_data.get("indicators", None)
            
            # Generate dynamic prompt based on actual timeframes, bot_id, available indicators, and historical data
            strategy_prompt = self._get_analysis_prompt(bot_id, timeframes, indicators_from_data, historical_transactions)
            
            # Format final prompt with clear sections and historical context
            prompt = self._format_final_prompt(strategy_prompt, market_data, historical_transactions, bot_id)
            
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=self.claude_model,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Log usage
            duration_ms = int((time.time() - start_time) * 1000)
            input_tokens = response.usage.input_tokens if hasattr(response, 'usage') else 0
            output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else 0
            
            self._log_llm_usage(
                provider='CLAUDE',
                model=self.claude_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_type='market_analysis',
                success=True,
                request_duration_ms=duration_ms
            )
            
            # Decrement quota after successful API call
            if self.developer_id:
                self._decrement_quota(self.developer_id)
            
            content = response.content[0].text
            return self._parse_llm_response(content)
            
        except Exception as e:
            # Log failed request
            duration_ms = int((time.time() - start_time) * 1000)
            self._log_llm_usage(
                provider='CLAUDE',
                model=self.claude_model,
                input_tokens=0,
                output_tokens=0,
                request_type='market_analysis',
                success=False,
                error_message=str(e),
                request_duration_ms=duration_ms
            )
            
            logger.error(f"Claude analysis error: {e}")
            return {"error": f"Claude analysis failed: {str(e)}"}
    
    async def analyze_with_gemini(self, market_data: Dict[str, Any], bot_id: int = None,
                                  historical_transactions: List[Dict] = None) -> Dict[str, Any]:
        """Analyze market data using Gemini with optional historical learning"""
        if not self.gemini_client:
            return {"error": "Gemini client not available"}
        
        # Check quota before making API call
        if self.developer_id:
            try:
                self._check_quota(self.developer_id)
            except QuotaExceededException as e:
                logger.warning(f"❌ Quota exceeded for developer {self.developer_id}: {e}")
                return {"error": "quota_exceeded", "message": str(e)}
        
        start_time = time.time()
        try:
            # Extract timeframes and indicators from market_data
            timeframes = list(market_data.get("timeframes", {}).keys())
            indicators_from_data = market_data.get("indicators", None)
            
            # Generate dynamic prompt based on actual timeframes, bot_id, available indicators, and historical data
            strategy_prompt = self._get_analysis_prompt(bot_id, timeframes, indicators_from_data, historical_transactions)
            
            # Format final prompt with clear sections and historical context
            prompt = self._format_final_prompt(strategy_prompt, market_data, historical_transactions, bot_id)
            
            response = await asyncio.to_thread(
                self.gemini_client.generate_content,
                prompt
            )
            
            # Log usage
            duration_ms = int((time.time() - start_time) * 1000)
            # Gemini usage metadata
            input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
            output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
            
            self._log_llm_usage(
                provider='GEMINI',
                model=self.gemini_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_type='market_analysis',
                success=True,
                request_duration_ms=duration_ms
            )
            
            # Decrement quota after successful API call
            if self.developer_id:
                self._decrement_quota(self.developer_id)
            
            content = response.text
            return self._parse_llm_response(content)
            
        except Exception as e:
            # Log failed request
            duration_ms = int((time.time() - start_time) * 1000)
            self._log_llm_usage(
                provider='GEMINI',
                model=self.gemini_model,
                input_tokens=0,
                output_tokens=0,
                request_type='market_analysis',
                success=False,
                error_message=str(e),
                request_duration_ms=duration_ms
            )
            
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
                           indicators_analysis: Dict[str, Dict[str, Any]] = None,
                           model: str = "openai", bot_id: int = None,
                           historical_transactions: List[Dict] = None) -> Dict[str, Any]:
        """
        Main method to analyze market data with specified LLM
        
        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            timeframes_data: OHLCV data for different timeframes
            indicators_analysis: Calculated technical indicators for each timeframe
            model: LLM to use ("openai", "claude", "gemini")
            bot_id: Bot ID for quota tracking
            historical_transactions: Optional list of past transactions for learning
            
        Returns:
            Complete trading analysis with Fibonacci and historical learning
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(symbol, timeframes_data, model)
            cached_analysis = self._get_cached_analysis(cache_key)
            if cached_analysis:
                return cached_analysis
            
            # Prepare market data with indicators
            market_data = self.prepare_market_data(symbol, timeframes_data, indicators_analysis)
            
            if not market_data:
                return {"error": "Failed to prepare market data"}
            
            # Analyze with specified model using retry mechanism
            # Support both provider type ("openai") and full model name ("gpt-4o-mini")
            model_lower = model.lower()
            if model_lower == "openai" or model_lower.startswith("gpt"):
                analysis = await self._retry_with_backoff(self.analyze_with_openai, market_data, bot_id, historical_transactions)
            elif model_lower == "claude" or model_lower.startswith("claude") or model_lower == "anthropic":
                analysis = await self._retry_with_backoff(self.analyze_with_claude, market_data, bot_id, historical_transactions)
            elif model_lower == "gemini" or model_lower.startswith("gemini"):
                analysis = await self._retry_with_backoff(self.analyze_with_gemini, market_data, bot_id, historical_transactions)
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
    
    async def find_trigger_zones(
        self,
        symbol: str,
        timeframes_data: Dict[str, List[Dict]],
        indicators_analysis: Dict[str, Dict[str, Any]],
        bot_id: int = None,
        model: str = "openai"
    ) -> Dict[str, Any]:
        """
        Analyze market to find optimal BUY/SELL trigger zones
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            timeframes_data: OHLCV data for different timeframes (not used, for compatibility)
            indicators_analysis: Calculated technical indicators for each timeframe
            bot_id: Bot ID for quota tracking
            model: LLM to use ("openai", "claude", "gemini")
            
        Returns:
            {
                "trigger_zones": [
                    {"type": "BUY", "range": [880000, 920000], "confidence": 82},
                    {"type": "SELL", "range": [1450000, 1500000], "confidence": 71}
                ],
                "reasoning": "RSI oversold on 1H/2H, strong 4H uptrend"
            }
        """
        try:
            logger.info(f"🎯 Finding trigger zones for {symbol} using {model}")
            
            # Prepare filtered market data (indicators only)
            filtered_data = {
                'symbol': symbol,
                'analysis_timestamp': datetime.now().isoformat(),
                'indicators': indicators_analysis
            }
            
            # Generate zone-finding prompt
            timeframes = list(indicators_analysis.keys()) if indicators_analysis else []
            zone_prompt = self._generate_zone_finding_prompt(timeframes)
            
            # Create final prompt with data
            prompt = f"""{zone_prompt}

╔══════════════════════════════════════════════════════════════════╗
║ 📈 MARKET DATA TO ANALYZE                                        ║
╚══════════════════════════════════════════════════════════════════╝

{json.dumps(filtered_data, indent=2)}

⚡ INSTRUCTIONS RECAP:
1. Analyze all indicators across timeframes
2. Identify strong support zones (BUY zones)
3. Identify strong resistance zones (SELL zones)
4. Return STRICT JSON format with trigger_zones array

═══════════════════════════════════════════════════════════════════
"""
            
            # Call LLM based on model type
            model_lower = model.lower()
            if model_lower == "openai" or model_lower.startswith("gpt"):
                result = await self._find_zones_with_openai(prompt, bot_id)
            elif model_lower == "claude" or model_lower.startswith("claude"):
                result = await self._find_zones_with_claude(prompt, bot_id)
            elif model_lower == "gemini" or model_lower.startswith("gemini"):
                result = await self._find_zones_with_gemini(prompt, bot_id)
            else:
                return {"error": f"Unsupported model: {model}"}
            
            logger.info(f"✅ Found {len(result.get('trigger_zones', []))} trigger zones")
            return result
            
        except Exception as e:
            logger.error(f"❌ Find trigger zones error: {e}")
            return {"error": f"Zone finding failed: {str(e)}"}
    
    async def confirm_zone_trade(
        self,
        zone: Dict[str, Any],
        current_price: float,
        indicators_analysis: Dict[str, Dict[str, Any]],
        symbol: str,
        bot_id: int = None,
        model: str = "openai"
    ) -> Dict[str, Any]:
        """
        Confirm whether to execute a trade when price enters a trigger zone
        
        Args:
            zone: Trigger zone info (type, price_min, price_max, confidence, reasoning)
            current_price: Current market price that triggered the zone
            indicators_analysis: Pre-calculated indicators for all timeframes
            symbol: Trading symbol
            bot_id: Optional bot ID for custom prompts
            model: LLM model to use
            
        Returns:
            Dict with recommendation (action: BUY/SELL/HOLD, entry_price, confidence, reasoning)
        """
        try:
            # Filter data - only send indicators
            filtered_data = {
                'symbol': symbol,
                'current_price': current_price,
                'analysis_timestamp': datetime.now().isoformat(),
                'indicators': indicators_analysis,
                'trigger_zone': zone
            }
            
            # Generate zone confirmation prompt
            prompt = self._generate_zone_confirmation_prompt(zone, current_price, filtered_data)
            
            # Call LLM based on model type
            model_lower = model.lower()
            if model_lower == "openai" or model_lower.startswith("gpt"):
                result = await self._confirm_zone_with_openai(prompt, bot_id)
            elif model_lower == "claude" or model_lower.startswith("claude"):
                result = await self._confirm_zone_with_claude(prompt, bot_id)
            elif model_lower == "gemini" or model_lower.startswith("gemini"):
                result = await self._confirm_zone_with_gemini(prompt, bot_id)
            else:
                return {"error": f"Unsupported model: {model}"}
            
            action = result.get('recommendation', {}).get('action', 'HOLD')
            logger.info(f"✅ Zone confirmation: {action}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Zone confirmation error: {e}")
            return {"error": f"Zone confirmation failed: {str(e)}"}
    
    def _generate_zone_finding_prompt(self, timeframes: List[str]) -> str:
        """Generate prompt for finding trigger zones"""
        formatted_timeframes = ", ".join([tf.upper() for tf in timeframes])
        
        return f"""You are a professional trading zone finder. Analyze market indicators to identify HIGH-PROBABILITY trigger zones for BUY and SELL entries.

═══════════════════════════════════════════════════════════════════
🎯 YOUR MISSION: FIND TRIGGER ZONES
═══════════════════════════════════════════════════════════════════

A TRIGGER ZONE is a price range where:
• Multiple technical factors align (support/resistance + indicators)
• High probability of price reversal or continuation
• LLM will be called again when price enters this zone for final confirmation

TIMEFRAMES ANALYZED: {formatted_timeframes}

ZONE REQUIREMENTS:
1. BUY ZONES (Support Areas):
   • Strong support levels (multiple touches, major levels)
   • RSI oversold (<40) or showing bullish divergence
   • Price near lower Bollinger Band
   • CMF showing accumulation (positive)
   • MACD bullish crossover potential

2. SELL ZONES (Resistance Areas):
   • Strong resistance levels (multiple touches, major levels)
   • RSI overbought (>60) or showing bearish divergence
   • Price near upper Bollinger Band
   • CMF showing distribution (negative)
   • MACD bearish crossover potential

ZONE QUALITY SCORING:
• CONFIDENCE 80-100%: 3+ confirming factors, major level (5+ touches)
• CONFIDENCE 60-79%: 2-3 confirming factors, strong level (3-4 touches)
• CONFIDENCE < 60%: Don't include (not worth monitoring)

═══════════════════════════════════════════════════════════════════
📤 OUTPUT FORMAT (STRICT JSON SCHEMA)
═══════════════════════════════════════════════════════════════════

{{
  "trigger_zones": [
    {{
      "type": "BUY",
      "range": [<min_price>, <max_price>],
      "confidence": <60-100>
    }},
    {{
      "type": "SELL",
      "range": [<min_price>, <max_price>],
      "confidence": <60-100>
    }}
  ],
  "reasoning": "<1-2 sentences explaining why these zones were selected>"
}}

OUTPUT RULES:
• Return 2-4 zones maximum (1-2 BUY, 1-2 SELL)
• Range width should be 1-3% of current price
• Only include zones with confidence >= 60%
• RETURN ONLY VALID JSON - no explanatory text outside JSON
• If no high-quality zones found, return empty trigger_zones array

═══════════════════════════════════════════════════════════════════
"""
    
    async def _find_zones_with_openai(self, prompt: str, bot_id: int = None) -> Dict[str, Any]:
        """Find trigger zones using OpenAI"""
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a professional trading zone finder. Analyze indicators to identify trigger zones. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Log usage if bot_id provided
            if bot_id:
                self._log_llm_usage(
                    provider="openai",
                    model=self.openai_model,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    request_type="zone_finding",
                    bot_id=bot_id
                )
            
            # Parse JSON
            parsed = self._parse_json_response(content)
            if not parsed:
                return {"error": "Failed to parse zone finding response"}
            
            return parsed
            
        except Exception as e:
            logger.error(f"OpenAI zone finding error: {e}")
            return {"error": str(e)}
    
    async def _find_zones_with_claude(self, prompt: str, bot_id: int = None) -> Dict[str, Any]:
        """Find trigger zones using Claude"""
        try:
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=self.claude_model,
                max_tokens=1000,
                temperature=0.3,
                system="You are a professional trading zone finder. Analyze indicators to identify trigger zones. Return ONLY valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            
            # Log usage if bot_id provided
            if bot_id:
                self._log_llm_usage(
                    provider="claude",
                    model=self.claude_model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    request_type="zone_finding",
                    bot_id=bot_id
                )
            
            # Parse JSON
            parsed = self._parse_json_response(content)
            if not parsed:
                return {"error": "Failed to parse zone finding response"}
            
            return parsed
            
        except Exception as e:
            logger.error(f"Claude zone finding error: {e}")
            return {"error": str(e)}
    
    async def _find_zones_with_gemini(self, prompt: str, bot_id: int = None) -> Dict[str, Any]:
        """Find trigger zones using Gemini"""
        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1000,
                    "response_mime_type": "application/json"
                }
            )
            
            content = response.text.strip()
            
            # Log usage (Gemini doesn't provide token counts in response)
            if bot_id:
                self._log_llm_usage(
                    provider="gemini",
                    model=self.gemini_model_name,
                    input_tokens=len(prompt.split()) * 1.3,  # Estimate
                    output_tokens=len(content.split()) * 1.3,  # Estimate
                    request_type="zone_finding",
                    bot_id=bot_id
                )
            
            # Parse JSON
            parsed = self._parse_json_response(content)
            if not parsed:
                return {"error": "Failed to parse zone finding response"}
            
            return parsed
            
        except Exception as e:
            logger.error(f"Gemini zone finding error: {e}")
            return {"error": str(e)}
    
    def _generate_zone_confirmation_prompt(self, zone: Dict[str, Any], current_price: float, filtered_data: Dict[str, Any]) -> str:
        """Generate prompt for confirming zone trade"""
        zone_type = zone.get('type', 'UNKNOWN')
        price_min = zone.get('price_min', zone.get('range', [0])[0] if isinstance(zone.get('range'), list) else 0)
        price_max = zone.get('price_max', zone.get('range', [0, 0])[1] if isinstance(zone.get('range'), list) else 0)
        confidence = zone.get('confidence', 0)
        reasoning = zone.get('reasoning', 'No reasoning provided')
        
        timeframes = list(filtered_data.get('indicators', {}).keys())
        formatted_timeframes = ", ".join([tf.upper() for tf in timeframes])
        
        return f"""╔══════════════════════════════════════════════════════════════════╗
║ ⚡ ZONE TRADE CONFIRMATION REQUEST                                ║
╚══════════════════════════════════════════════════════════════════╝

You are confirming whether to execute a trade in a PRE-IDENTIFIED trigger zone.

🎯 TRIGGER ZONE DETECTED:
  • Type: {zone_type}
  • Price Range: ${price_min:,.2f} - ${price_max:,.2f}
  • Current Price: ${current_price:,.2f} (✓ IN ZONE)
  • Confidence: {confidence}%
  • Reasoning: {reasoning}

📊 YOUR TASK:
Analyze the current market indicators to CONFIRM or REJECT this {zone_type} trade.

⚡ KEY QUESTIONS TO ANSWER:
1. Do current indicators support a {zone_type} at this price?
2. Is momentum/trend aligned with {zone_type} direction?
3. Are there any WARNING SIGNS (divergence, weak volume, extreme RSI)?
4. What is the risk/reward at current price ${current_price:,.2f}?

═══════════════════════════════════════════════════════════════════
╔══════════════════════════════════════════════════════════════════╗
║ 📊 CURRENT MARKET INDICATORS (Timeframes: {formatted_timeframes})           ║
╚══════════════════════════════════════════════════════════════════╝

{json.dumps(filtered_data, indent=2)}

═══════════════════════════════════════════════════════════════════
🎯 CONFIRMATION GUIDELINES:

FOR {zone_type} CONFIRMATION:
✓ If {zone_type}: Check trend_bullish/trend_strength direction aligns
✓ If BUY: RSI < 50, price near support, positive momentum
✓ If SELL: RSI > 50, price near resistance, negative momentum  
✓ Volume confirmation: volume_ratio > 1.0
✓ Multi-timeframe alignment: Check at least 2 timeframes agree

WARNING SIGNS (→ HOLD):
✗ Divergence between price and indicators
✗ Extreme RSI (>80 or <20)
✗ Volume too low (volume_ratio < 0.8)
✗ Conflicting signals across timeframes
✗ Price far from zone center (near zone edge)

═══════════════════════════════════════════════════════════════════
╔══════════════════════════════════════════════════════════════════╗
║ 📤 OUTPUT FORMAT (STRICT JSON SCHEMA)                            ║
╚══════════════════════════════════════════════════════════════════╝

{{
  "recommendation": {{
    "action": "{zone_type}" | "HOLD",
    "entry_price": {current_price},
    "confidence": <0-100>,
    "reasoning": "<1-2 sentences: why confirm or reject based on indicators>"
  }}
}}

OUTPUT RULES:
• ONLY return valid JSON (no markdown, no extra text)
• action MUST be "{zone_type}" (to confirm) or "HOLD" (to reject)
• If confidence < 60%: action MUST be "HOLD"
• entry_price = {current_price} (the triggered price)
• reasoning: Brief explanation based on actual indicator values

RESPOND NOW WITH JSON ONLY:
"""
    
    async def _confirm_zone_with_openai(self, prompt: str, bot_id: int = None) -> Dict[str, Any]:
        """Confirm zone trade using OpenAI"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a professional trading confirmation engine. Analyze indicators and respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            
            # Log usage
            if bot_id:
                self._log_llm_usage(
                    provider="openai",
                    model=self.openai_model,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    request_type="zone_confirmation",
                    bot_id=bot_id
                )
            
            # Parse JSON
            parsed = self._parse_json_response(content)
            if not parsed:
                return {"error": "Failed to parse zone confirmation response"}
            
            return parsed
            
        except Exception as e:
            logger.error(f"OpenAI zone confirmation error: {e}")
            return {"error": str(e)}
    
    async def _confirm_zone_with_claude(self, prompt: str, bot_id: int = None) -> Dict[str, Any]:
        """Confirm zone trade using Claude"""
        try:
            response = await asyncio.to_thread(
                self.claude_client.messages.create,
                model=self.claude_model,
                max_tokens=500,
                temperature=0.3,
                system="You are a professional trading confirmation engine. Analyze indicators and respond ONLY with valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text.strip()
            
            # Log usage
            if bot_id:
                self._log_llm_usage(
                    provider="claude",
                    model=self.claude_model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    request_type="zone_confirmation",
                    bot_id=bot_id
                )
            
            # Parse JSON
            parsed = self._parse_json_response(content)
            if not parsed:
                return {"error": "Failed to parse zone confirmation response"}
            
            return parsed
            
        except Exception as e:
            logger.error(f"Claude zone confirmation error: {e}")
            return {"error": str(e)}
    
    async def _confirm_zone_with_gemini(self, prompt: str, bot_id: int = None) -> Dict[str, Any]:
        """Confirm zone trade using Gemini"""
        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 500,
                    "response_mime_type": "application/json"
                }
            )
            
            content = response.text.strip()
            
            # Log usage
            if bot_id:
                self._log_llm_usage(
                    provider="gemini",
                    model=self.gemini_model_name,
                    input_tokens=len(prompt.split()) * 1.3,  # Estimate
                    output_tokens=len(content.split()) * 1.3,  # Estimate
                    request_type="zone_confirmation",
                    bot_id=bot_id
                )
            
            # Parse JSON
            parsed = self._parse_json_response(content)
            if not parsed:
                return {"error": "Failed to parse zone confirmation response"}
            
            return parsed
            
        except Exception as e:
            logger.error(f"Gemini zone confirmation error: {e}")
            return {"error": str(e)}
    
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
                       preferred_provider: str = None, bot_id: int = None, subscription_id: int = None) -> LLMIntegrationService:
    """
    Factory function to create LLM Integration Service
    
    Args:
        config: Optional configuration dict
        developer_id: Developer ID to load their configured LLM providers (BYOK)
        db: Database session for loading provider configs
        preferred_provider: Preferred provider ("openai", "claude", "gemini") - from bot config
        bot_id: Bot ID for logging
        subscription_id: Subscription ID for usage tracking
        
    Returns:
        LLMIntegrationService instance
    """
    return LLMIntegrationService(config=config, developer_id=developer_id, db=db,
                                 preferred_provider=preferred_provider, bot_id=bot_id, 
                                 subscription_id=subscription_id)

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
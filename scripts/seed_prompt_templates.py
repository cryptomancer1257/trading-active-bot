#!/usr/bin/env python3
"""
Seed script to create default prompt templates
Based on LLM integration service prompts
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core import models, crud
from core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_default_prompts():
    """Create default prompt templates"""
    
    # Trading Analysis Prompt
    trading_prompt = """You are a professional crypto futures trading engine. Analyze OHLCV data across multiple timeframes and make autonomous BUY/SELL/HOLD decisions based on strict technical analysis criteria. 

**CRITICAL REQUIREMENTS:**
- ONLY output valid JSON - no explanatory text outside JSON
- STRICT volume confirmation - if volume fails, return HOLD immediately
- Conservative approach - only trade high-probability setups
- Risk management mandatory - all trades must have proper SL/TP
- Multi-timeframe confluence - require agreement across timeframes

**ANALYSIS WORKFLOW (STRICT ORDER):**

**STEP 1: VOLUME VALIDATION (MANDATORY FIRST CHECK)**
- CALCULATE: Current volume vs Average of last 20 candles
- REQUIREMENTS:
  - BUY/SELL: Current volume ≥ 110% of 20-period average
  - HOLD: Current volume < 110% of 20-period average
- IF volume fails → STOP analysis → Return HOLD immediately

**STEP 2: MULTI-TIMEFRAME TREND CONFIRMATION**
- CALCULATE: MA5, MA10, MA20 for each timeframe
- BULLISH TREND: MA5 > MA10 > MA20 (all timeframes agree)
- BEARISH TREND: MA5 < MA10 < MA20 (all timeframes agree)
- SIDEWAYS: Mixed signals across timeframes
- REQUIREMENTS:
  - BUY: At least 2/3 timeframes show bullish alignment
  - SELL: At least 2/3 timeframes show bearish alignment
  - HOLD: Conflicting trends or sideways action

**STEP 3: MOMENTUM ANALYSIS**
- RSI(14):
  - BUY Zone: 40-65 (avoid overbought >70)
  - SELL Zone: 35-60 (avoid oversold <30)
  - EXCLUDE: RSI >75 or <25 (extreme zones)
- MACD:
  - BUY: MACD line > Signal line AND both trending up
  - SELL: MACD line < Signal line AND both trending down
  - PRIORITY: Recent crossover within 1-3 candles

**STEP 4: SUPPORT/RESISTANCE VALIDATION**
- BOLLINGER BANDS:
  - BUY: Price bounces from Lower BB OR breaks above Middle BB with volume
  - SELL: Price bounces from Upper BB OR breaks below Middle BB with volume
  - AVOID: Price in middle third of BB range (no clear signal)
- KEY LEVELS:
  - IDENTIFY: Recent swing highs/lows within 20 candles
  - CONFIRM: Price at or near significant support/resistance

**STEP 5: FIBONACCI CONFLUENCE (BONUS)**
- IF clear trend exists:
  - IDENTIFY: Recent swing high to swing low (or vice versa)
  - PRIORITY ZONES: 0.382, 0.5, 0.618 retracement levels
  - BONUS POINTS: Entry price within ±0.5% of Fibonacci level
  - SKIP: If no clear Fibonacci structure

**EXCLUSION CRITERIA (AUTO-HOLD):**
- Volume insufficient (< 110% average)
- Extreme RSI (>75 or <25)
- Conflicting timeframes (no 2/3 agreement)
- Sideways consolidation (price within 1.5% range for 10+ candles)
- Recent false breakout (failed breakout within 5 candles)
- Low volatility (ATR < 0.8% of current price)

**CONFIDENCE SCORING:**
- 90-100%: 5+ indicators agree + volume spike (>150%) + clear trend
- 75-89%: 4 indicators agree + good volume (>130%) + trend confirmation
- 60-74%: 3 indicators agree + adequate volume + some trend signals
- 55-59%: 2 indicators agree + minimum volume + weak signals
- <55%: HOLD - insufficient setup quality

**STOP-LOSS CALCULATION:**
- BUY Stops:
  1. Below recent swing low (last 10 candles), OR
  2. Below Lower Bollinger Band, OR  
  3. 2-3% below entry (whichever is closer)
- SELL Stops:
  1. Above recent swing high (last 10 candles), OR
  2. Above Upper Bollinger Band, OR
  3. 2-3% above entry (whichever is closer)

**TAKE-PROFIT TARGETS:**
- BUY Targets:
  1. Next resistance level, OR
  2. Upper Bollinger Band, OR
  3. 1.5x stop-loss distance minimum
- SELL Targets:
  1. Next support level, OR
  2. Lower Bollinger Band, OR
  3. 1.5x stop-loss distance minimum
- MINIMUM R:R RATIO: 1.5:1 (prefer 2:1+)

**OUTPUT FORMAT (STRICT JSON SCHEMA):**
```json
{
  "recommendation": {
    "action": "BUY" | "SELL" | "HOLD",
    "entry_price": "<string or null>",
    "take_profit": "<string or null>",
    "stop_loss": "<string or null>",
    "strategy": "<MA, MACD, RSI, BollingerBands, Fibonacci_Retracement or combination>",
    "risk_reward": "<string or null>",
    "confidence": "<0-100>",
    "reasoning": "<brief 1-2 sentence explanation>"
  }
}
```

**OUTPUT RULES:**
- HOLD actions: All price fields = null
- Decimal precision: 1 decimal place for all prices
- No text outside JSON: Pure JSON response only
- Confidence < 55%: Force action = "HOLD"

**FINAL VALIDATION CHECKLIST:**
✓ Volume > 110% average?
✓ 2/3 timeframes agree on trend?
✓ RSI in valid range (not extreme)?
✓ Clear support/resistance level?
✓ Risk:Reward ≥ 1.5:1?
✓ Confidence ≥ 55%?
IF any ✗ → HOLD"""

    # Risk Management Prompt
    risk_management_prompt = """You are a professional risk management and capital allocation specialist for crypto futures trading.

I will provide you with account and market information to help determine optimal position sizing.

**📊 Account Information:**
- Total account balance
- Available balance for trading
- Current portfolio exposure
- Current drawdown status
- Historical performance metrics

**📈 Market Analysis:**
- Market volatility level
- Trading signal confidence
- Current price and ATR
- Risk/reward assessment

**💰 Position Sizing Request:**
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

**Please respond in JSON format:**
```json
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
}```"""

    # Market Analysis Prompt
    analysis_prompt = """You are a professional crypto futures trading analyst.
I will provide you OHLCV data for multiple timeframes in JSON format.

Based on this data, please:

**You are a professional crypto futures trading engine. Analyze OHLCV data across multiple timeframes and make autonomous BUY/SELL/HOLD decisions based on strict technical analysis criteria.**

**CRITICAL REQUIREMENTS:**
- ONLY output valid JSON - no explanatory text outside JSON
- STRICT volume confirmation - if volume fails, return HOLD immediately
- Conservative approach - only trade high-probability setups
- Risk management mandatory - all trades must have proper SL/TP
- Multi-timeframe confluence - require agreement across timeframes

**ANALYSIS WORKFLOW (STRICT ORDER):**

**STEP 1: VOLUME VALIDATION (MANDATORY FIRST CHECK)**
- CALCULATE: Current volume vs Average of last 20 candles
- REQUIREMENTS:
  - BUY/SELL: Current volume ≥ 110% of 20-period average
  - HOLD: Current volume < 110% of 20-period average
- IF volume fails → STOP analysis → Return HOLD immediately

**STEP 2: MULTI-TIMEFRAME TREND CONFIRMATION**
- CALCULATE: MA5, MA10, MA20 for each timeframe
- BULLISH TREND: MA5 > MA10 > MA20 (all timeframes agree)
- BEARISH TREND: MA5 < MA10 < MA20 (all timeframes agree)
- SIDEWAYS: Mixed signals across timeframes
- REQUIREMENTS:
  - BUY: At least 2/3 timeframes show bullish alignment
  - SELL: At least 2/3 timeframes show bearish alignment
  - HOLD: Conflicting trends or sideways action

**STEP 3: MOMENTUM ANALYSIS**
- RSI(14):
  - BUY Zone: 40-65 (avoid overbought >70)
  - SELL Zone: 35-60 (avoid oversold <30)
  - EXCLUDE: RSI >75 or <25 (extreme zones)
- MACD:
  - BUY: MACD line > Signal line AND both trending up
  - SELL: MACD line < Signal line AND both trending down
  - PRIORITY: Recent crossover within 1-3 candles

**STEP 4: SUPPORT/RESISTANCE VALIDATION**
- BOLLINGER BANDS:
  - BUY: Price bounces from Lower BB OR breaks above Middle BB with volume
  - SELL: Price bounces from Upper BB OR breaks below Middle BB with volume
  - AVOID: Price in middle third of BB range (no clear signal)
- KEY LEVELS:
  - IDENTIFY: Recent swing highs/lows within 20 candles
  - CONFIRM: Price at or near significant support/resistance

**STEP 5: FIBONACCI CONFLUENCE (BONUS)**
- IF clear trend exists:
  - IDENTIFY: Recent swing high to swing low (or vice versa)
  - PRIORITY ZONES: 0.382, 0.5, 0.618 retracement levels
  - BONUS POINTS: Entry price within ±0.5% of Fibonacci level
  - SKIP: If no clear Fibonacci structure

**EXCLUSION CRITERIA (AUTO-HOLD):**
- Volume insufficient (< 110% average)
- Extreme RSI (>75 or <25)
- Conflicting timeframes (no 2/3 agreement)
- Sideways consolidation (price within 1.5% range for 10+ candles)
- Recent false breakout (failed breakout within 5 candles)
- Low volatility (ATR < 0.8% of current price)

**CONFIDENCE SCORING:**
- 90-100%: 5+ indicators agree + volume spike (>150%) + clear trend
- 75-89%: 4 indicators agree + good volume (>130%) + trend confirmation
- 60-74%: 3 indicators agree + adequate volume + some trend signals
- 55-59%: 2 indicators agree + minimum volume + weak signals
- <55%: HOLD - insufficient setup quality

**STOP-LOSS CALCULATION:**
- BUY Stops:
  1. Below recent swing low (last 10 candles), OR
  2. Below Lower Bollinger Band, OR  
  3. 2-3% below entry (whichever is closer)
- SELL Stops:
  1. Above recent swing high (last 10 candles), OR
  2. Above Upper Bollinger Band, OR
  3. 2-3% above entry (whichever is closer)

**TAKE-PROFIT TARGETS:**
- BUY Targets:
  1. Next resistance level, OR
  2. Upper Bollinger Band, OR
  3. 1.5x stop-loss distance minimum
- SELL Targets:
  1. Next support level, OR
  2. Lower Bollinger Band, OR
  3. 1.5x stop-loss distance minimum
- MINIMUM R:R RATIO: 1.5:1 (prefer 2:1+)

**OUTPUT FORMAT (STRICT JSON SCHEMA):**
```json
{
  "recommendation": {
    "action": "BUY" | "SELL" | "HOLD",
    "entry_price": "<string or null>",
    "take_profit": "<string or null>",
    "stop_loss": "<string or null>",
    "strategy": "<MA, MACD, RSI, BollingerBands, Fibonacci_Retracement or combination>",
    "risk_reward": "<string or null>",
    "confidence": "<0-100>",
    "reasoning": "<brief 1-2 sentence explanation>"
  }
}
```

**OUTPUT RULES:**
- HOLD actions: All price fields = null
- Decimal precision: 1 decimal place for all prices
- No text outside JSON: Pure JSON response only
- Confidence < 55%: Force action = "HOLD"

**FINAL VALIDATION CHECKLIST:**
✓ Volume > 110% average?
✓ 2/3 timeframes agree on trend?
✓ RSI in valid range (not extreme)?
✓ Clear support/resistance level?
✓ Risk:Reward ≥ 1.5:1?
✓ Confidence ≥ 55%?
IF any ✗ → HOLD

**DỮ LIỆU:**"""

    # Sentiment Analysis Prompt
    sentiment_prompt = """You are a financial sentiment analyst. Analyze the provided news articles and determine the overall market sentiment for cryptocurrency trading.

**News Articles:**
{news_data}

Please provide sentiment analysis in JSON format:
```json
{
  "overall_sentiment": "BULLISH/NEUTRAL/BEARISH",
  "confidence": "0-100",
  "key_themes": ["theme1", "theme2", "theme3"],
  "market_impact": "HIGH/MEDIUM/LOW",
  "trading_implications": "brief explanation",
  "risk_factors": ["risk1", "risk2"],
  "opportunities": ["opportunity1", "opportunity2"]
}
```"""

    # Default prompts to create
    default_prompts = [
        {
            "name": "Advanced Trading Analysis",
            "description": "Comprehensive trading analysis with Fibonacci, volume confirmation, and multi-timeframe analysis",
            "content": trading_prompt,
            "category": "TRADING",
            "is_active": True,
            "is_default": True
        },
        {
            "name": "Risk Management & Capital Allocation",
            "description": "Professional risk management and position sizing for crypto futures trading",
            "content": risk_management_prompt,
            "category": "RISK_MANAGEMENT",
            "is_active": True,
            "is_default": True
        },
        {
            "name": "Market Analysis Engine",
            "description": "Multi-timeframe market analysis with technical indicators and Fibonacci retracements",
            "content": analysis_prompt,
            "category": "ANALYSIS",
            "is_active": True,
            "is_default": True
        },
        {
            "name": "News Sentiment Analysis",
            "description": "Analyze news articles and market sentiment for trading decisions",
            "content": sentiment_prompt,
            "category": "ANALYSIS",
            "is_active": True,
            "is_default": False
        }
    ]
    
    return default_prompts

def seed_prompt_templates():
    """Seed prompt templates into database"""
    db = SessionLocal()
    
    try:
        # Check if prompts already exist
        existing_prompts = db.query(models.PromptTemplate).count()
        if existing_prompts > 0:
            logger.info(f"Found {existing_prompts} existing prompt templates. Skipping seed.")
            return
        
        # Get or create a default user (admin)
        admin_user = db.query(models.User).filter(models.User.role == "ADMIN").first()
        if not admin_user:
            logger.error("No admin user found. Please create an admin user first.")
            return
        
        # Create default prompts
        default_prompts = create_default_prompts()
        
        for prompt_data in default_prompts:
            try:
                # Create prompt template directly
                prompt = models.PromptTemplate(
                    name=prompt_data["name"],
                    description=prompt_data["description"],
                    content=prompt_data["content"],
                    category=prompt_data["category"],
                    is_active=prompt_data["is_active"],
                    is_default=prompt_data["is_default"],
                    created_by=admin_user.id
                )
                db.add(prompt)
                db.commit()
                db.refresh(prompt)
                logger.info(f"✅ Created prompt template: {prompt.name}")
            except Exception as e:
                logger.error(f"❌ Failed to create prompt '{prompt_data['name']}': {e}")
                db.rollback()
        
        db.commit()
        logger.info("🎉 Successfully seeded prompt templates!")
        
    except Exception as e:
        logger.error(f"❌ Error seeding prompt templates: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_prompt_templates()

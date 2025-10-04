#!/usr/bin/env python3
"""
Seed Risk Management Position Sizing Prompts
Creates comprehensive position sizing templates for different trading scenarios
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core import models
import json

def seed_risk_management_prompts():
    """Seed Risk Management position sizing prompt templates"""
    db = SessionLocal()
    
    try:
        print("🚀 Starting Risk Management prompts seeding...")
        
        # Define all Risk Management prompts
        risk_prompts = [
            # BASIC PROMPTS
            {
                "template_id": "basic_position_calculator",
                "title": "Basic Position Size Calculator",
                "category": "Risk Management - Basic",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Analyze this trade setup and provide position sizing in JSON format:

ACCOUNT INFO:
- Account Balance: $[amount]
- Current Drawdown: [%]
- Open Positions Value: $[amount]
- Available Capital: $[amount]

TRADE SETUP:
- Asset: [coin/token]
- Entry Price: $[price]
- Stop Loss Price: $[price]
- Take Profit Target: $[price]
- Direction: [LONG/SHORT]
- Timeframe: [1H/4H/1D/1W]

RISK PARAMETERS:
- Max Risk Per Trade: [1-2]%
- Risk Tolerance: [Conservative/Moderate/Aggressive]
- Win Rate History: [%]
- Average R/R Ratio: [x:x]

Please calculate and provide response in JSON format with recommended position size, risk assessment, and portfolio management advice.""",
                "risk_management": "Max 2% risk per trade, position sizing based on stop loss distance",
                "best_for": "Daily trading decisions, simple position sizing",
                "metadata": json.dumps({
                    "tags": ["Basic", "Position Sizing", "Daily Trading"],
                    "difficulty": "Beginner",
                    "use_case": "Daily trading decisions, simple position sizing"
                })
            },
            {
                "template_id": "scale_in_position_sizing",
                "title": "Scale-In Position Sizing",
                "category": "Risk Management - Basic",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Calculate position sizing for scale-in strategy:

ACCOUNT:
- Total Capital: $[amount]
- Risk Budget: [%]
- Current Positions: [list]

SCALE-IN PLAN:
- Asset: [coin]
- Number of Entries: [2-4]
- Entry Points: $[price1], $[price2], $[price3]
- Stop Loss: $[price]
- Direction: [LONG/SHORT]

MARKET CONDITION:
- Volatility (ATR): [HIGH/MEDIUM/LOW]
- Trend Strength: [Strong/Moderate/Weak]
- Market Phase: [Accumulation/Markup/Distribution/Markdown]

Provide JSON output with position size for each entry, cumulative risk, and scaling strategy.""",
                "risk_management": "Progressive risk management with DCA entries",
                "best_for": "DCA strategies, building positions gradually",
                "metadata": json.dumps({
                    "tags": ["Scale-In", "DCA", "Position Building"],
                    "difficulty": "Beginner",
                    "use_case": "DCA strategies, building positions gradually"
                })
            },
            
            # ADVANCED PROMPTS
            {
                "template_id": "atr_volatility_sizing",
                "title": "ATR Volatility-Adjusted Sizing",
                "category": "Risk Management - Advanced",
                "timeframe": "4H, Daily",
                "win_rate_estimate": "N/A",
                "prompt": """Calculate position size with ATR volatility adjustment:

MARKET DATA:
- Asset: [coin]
- Current Price: $[price]
- ATR (14-period): $[value]
- ATR Percentage: [%]
- Timeframe: [4H/1D]
- Historical Volatility (30d): [%]

ACCOUNT:
- Balance: $[amount]
- Standard Risk: [%]
- Volatility Tolerance: [Low/Medium/High]

SETUP:
- Entry: $[price]
- ATR Stop Distance: [1.5x/2x/3x] ATR
- Target: [R:R ratio]

Provide JSON with base position size, volatility-adjusted size, ATR impact analysis, and dynamic adjustment rules.""",
                "risk_management": "Volatility-adjusted position sizing using ATR",
                "best_for": "Volatile markets, adaptive risk management",
                "metadata": json.dumps({
                    "tags": ["ATR", "Volatility", "Advanced"],
                    "difficulty": "Intermediate",
                    "use_case": "Volatile markets, adaptive risk management"
                })
            },
            {
                "template_id": "correlation_adjusted_sizing",
                "title": "Correlation-Adjusted Position Sizing",
                "category": "Risk Management - Advanced",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Calculate position size considering portfolio correlation:

CURRENT PORTFOLIO:
- Asset 1: [coin] - $[value] - [%]
- Asset 2: [coin] - $[value] - [%]
- Asset 3: [coin] - $[value] - [%]
- Total Portfolio Value: $[amount]

NEW POSITION:
- Asset: [coin]
- Proposed Size: $[amount]
- Direction: [LONG/SHORT]

CORRELATION DATA:
- Correlation with BTC: [0-1]
- Correlation with existing positions: [list]
- Sector: [DeFi/L1/L2/Meme/AI]
- Market Cap: [Large/Mid/Small]

Provide JSON analyzing correlation risk, adjusted position size, portfolio concentration, sector exposure, and diversification score.""",
                "risk_management": "Portfolio-wide correlation and diversification management",
                "best_for": "Multi-asset portfolios, diversification management",
                "metadata": json.dumps({
                    "tags": ["Correlation", "Portfolio", "Diversification"],
                    "difficulty": "Advanced",
                    "use_case": "Multi-asset portfolios, diversification management"
                })
            },
            {
                "template_id": "kelly_criterion_calculator",
                "title": "Kelly Criterion Calculator",
                "category": "Risk Management - Advanced",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Calculate optimal position size using Kelly Criterion:

TRADING HISTORY:
- Win Rate: [%]
- Average Win: [%]
- Average Loss: [%]
- Number of Trades: [count]
- Consecutive Losses (max): [count]

CURRENT TRADE:
- Asset: [coin]
- Expected Win Probability: [%]
- Risk/Reward Ratio: [x:x]
- Entry: $[price]
- Stop: $[price]
- Target: $[price]

ACCOUNT:
- Balance: $[amount]
- Risk Tolerance: [Conservative/Moderate/Aggressive]

Provide JSON with full Kelly, half Kelly, quarter Kelly percentages, comparison with fixed % risk, and recommended position size with crypto volatility adjustments.""",
                "risk_management": "Mathematical optimization using Kelly Criterion",
                "best_for": "Mathematical optimization, systematic trading",
                "metadata": json.dumps({
                    "tags": ["Kelly Criterion", "Mathematical", "Optimization"],
                    "difficulty": "Advanced",
                    "use_case": "Mathematical optimization, systematic trading"
                })
            },
            {
                "template_id": "drawdown_adjusted_sizing",
                "title": "Drawdown-Adjusted Sizing",
                "category": "Risk Management - Advanced",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Calculate position size during account drawdown:

DRAWDOWN STATUS:
- Peak Balance: $[amount]
- Current Balance: $[amount]
- Drawdown: [%]
- Days in Drawdown: [days]
- Drawdown Phase: [Early/Mid/Deep/Recovery]

NORMAL PARAMETERS:
- Standard Risk Per Trade: [%]
- Standard Position Size: $[amount]
- Win Rate (last 20 trades): [%]

PROPOSED TRADE:
- Asset: [coin]
- Setup Quality: [A/B/C]
- Confidence Level: [1-10]
- Market Condition: [Favorable/Neutral/Unfavorable]

Provide JSON with reduced risk per trade, drawdown reduction factor, position size recommendation, recovery plan, and psychological risk assessment.""",
                "risk_management": "Conservative sizing during drawdown periods",
                "best_for": "Loss recovery periods, capital preservation",
                "metadata": json.dumps({
                    "tags": ["Drawdown", "Recovery", "Capital Preservation"],
                    "difficulty": "Intermediate",
                    "use_case": "Loss recovery periods, capital preservation"
                })
            },
            
            # LEVERAGE PROMPTS
            {
                "template_id": "leverage_safety_calculator",
                "title": "Leverage Safety Calculator",
                "category": "Risk Management - Leverage",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Calculate safe position size with leverage:

ACCOUNT:
- Balance: $[amount]
- Available Margin: $[amount]
- Margin Mode: [Cross/Isolated]
- Exchange: [Binance/Bybit/etc]

LEVERAGE SETUP:
- Intended Leverage: [x]
- Asset: [coin]
- Entry: $[price]
- Liquidation Tolerance: [%]
- Stop Loss: $[price]

RISK MANAGEMENT:
- Max Account Risk: [%]
- Leverage Experience: [Beginner/Intermediate/Advanced]
- Market Volatility: [Low/Medium/High]

Provide JSON with recommended position size in contracts, actual leverage, liquidation price, distance to liquidation, margin required, risk calculations, and safer leverage recommendation.""",
                "risk_management": "Safe leverage usage with liquidation risk management",
                "best_for": "Futures trading, leverage management",
                "metadata": json.dumps({
                    "tags": ["Leverage", "Futures", "Liquidation Risk"],
                    "difficulty": "Intermediate",
                    "use_case": "Futures trading, leverage management"
                })
            },
            {
                "template_id": "multi_position_margin_manager",
                "title": "Multi-Position Margin Manager",
                "category": "Risk Management - Leverage",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Analyze total margin exposure across positions:

OPEN POSITIONS:
Position 1: [coin] - $[value] - [x]leverage - [%]PnL
Position 2: [coin] - $[value] - [x]leverage - [%]PnL
Position 3: [coin] - $[value] - [x]leverage - [%]PnL

NEW POSITION REQUEST:
- Asset: [coin]
- Proposed Size: $[value]
- Leverage: [x]
- Direction: [LONG/SHORT]

ACCOUNT:
- Total Balance: $[amount]
- Used Margin: $[amount]
- Available Margin: $[amount]
- Maintenance Margin: $[amount]

Provide JSON analyzing total portfolio leverage, margin utilization, cross-position correlation, recommended new position size, liquidation risk, and position reduction recommendations.""",
                "risk_management": "Portfolio-wide margin and leverage management",
                "best_for": "Multiple open positions, portfolio-wide risk",
                "metadata": json.dumps({
                    "tags": ["Multi-Position", "Margin", "Portfolio Risk"],
                    "difficulty": "Advanced",
                    "use_case": "Multiple open positions, portfolio-wide risk"
                })
            },
            
            # CONFIDENCE PROMPTS
            {
                "template_id": "setup_quality_adjustment",
                "title": "Setup Quality Adjustment",
                "category": "Risk Management - Confidence",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Adjust position size based on setup quality:

TECHNICAL SETUP:
- Pattern: [type]
- Confirmation Signals: [list]
- Timeframe Confluence: [Yes/No]
- Volume Profile: [Strong/Normal/Weak]
- Support/Resistance Quality: [Strong/Medium/Weak]
- Setup Grade: [A+/A/B/C]

FUNDAMENTAL FACTORS:
- News Catalyst: [Yes/No]
- Sector Momentum: [Strong/Neutral/Weak]
- Market Sentiment: [Bullish/Neutral/Bearish]
- Liquidity: [High/Medium/Low]

TRADER FACTORS:
- Experience with this pattern: [High/Medium/Low]
- Emotional State: [Calm/Neutral/Anxious]
- Recent Performance: [Win streak/Neutral/Loss streak]

BASE PARAMETERS:
- Standard Position Size: [%]
- Account Balance: $[amount]

Provide JSON with base position size, quality multiplier (0.5x-2x), adjusted size, confidence score breakdown, and risk level justification.""",
                "risk_management": "Quality-based position scaling",
                "best_for": "Quality-based position scaling, discretionary trading",
                "metadata": json.dumps({
                    "tags": ["Setup Quality", "Confidence", "Discretionary"],
                    "difficulty": "Intermediate",
                    "use_case": "Quality-based position scaling, discretionary trading"
                })
            },
            {
                "template_id": "market_regime_sizing",
                "title": "Market Regime Position Sizing",
                "category": "Risk Management - Confidence",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Adjust position size for current market regime:

MARKET REGIME ANALYSIS:
- Overall Trend: [Strong Bull/Bull/Neutral/Bear/Strong Bear]
- BTC Dominance: [%] - [Rising/Falling]
- Market Volatility Index: [Low/Medium/High/Extreme]
- Fear & Greed Index: [0-100]
- Volume Trend: [Increasing/Stable/Decreasing]
- Liquidity Conditions: [Abundant/Normal/Tight]

REGIME CLASSIFICATION:
- Regime Type: [Risk-On/Risk-Off/Rotation/Uncertainty]
- Regime Stability: [Stable/Transitioning/Volatile]
- Historical Win Rate in this Regime: [%]

TRADE DETAILS:
- Asset: [coin]
- Strategy Type: [Trend/Mean Reversion/Breakout]
- Normal Position Size: [%]
- Account: $[amount]

Provide JSON with regime-adjusted position size, adjustment factor, recommended strategy modifications, risk level in current regime, and regime change indicators.""",
                "risk_management": "Market regime-based position adjustment",
                "best_for": "Macro-aware trading, regime-based adaptation",
                "metadata": json.dumps({
                    "tags": ["Market Regime", "Macro", "Adaptation"],
                    "difficulty": "Advanced",
                    "use_case": "Macro-aware trading, regime-based adaptation"
                })
            },
            
            # COMPREHENSIVE PROMPTS
            {
                "template_id": "complete_position_analysis",
                "title": "Complete Position Sizing Analysis",
                "category": "Risk Management - Comprehensive",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Perform comprehensive position sizing analysis:

=== ACCOUNT STATUS ===
- Total Balance: $[amount]
- Available Capital: $[amount]
- Current Drawdown: [%]
- Open Positions: [list]
- Used Margin: $[amount]
- Daily Loss Limit: [%]
- Weekly Loss Limit: [%]

=== TRADE DETAILS ===
- Asset: [coin]
- Direction: [LONG/SHORT]
- Entry Price: $[price]
- Stop Loss: $[price]
- Take Profit: $[price]
- Timeframe: [timeframe]
- Leverage (if any): [x]

=== RISK FACTORS ===
- ATR (14): $[value]
- Volatility (30d): [%]
- Market Condition: [description]
- Correlation with BTC: [0-1]
- Liquidity Score: [1-10]
- Setup Quality: [A/B/C]

=== TRADER PROFILE ===
- Risk Tolerance: [Conservative/Moderate/Aggressive]
- Win Rate (last 30 trades): [%]
- Average R/R: [x:x]
- Experience Level: [Beginner/Intermediate/Advanced]
- Emotional State: [1-10]

=== MARKET CONTEXT ===
- BTC Trend: [Bull/Bear/Sideways]
- Sector Performance: [Strong/Normal/Weak]
- Fear & Greed Index: [0-100]
- Recent News Impact: [Positive/Neutral/Negative]

Provide comprehensive JSON with multiple sizing methods, risk assessment across all dimensions, final recommendation with full reasoning, portfolio impact, adjustment factors, confidence score, and monitoring alerts.""",
                "risk_management": "Comprehensive multi-factor risk analysis",
                "best_for": "Critical trades, full analysis required",
                "metadata": json.dumps({
                    "tags": ["Comprehensive", "Multi-Factor", "Full Analysis"],
                    "difficulty": "Advanced",
                    "use_case": "Critical trades, full analysis required"
                })
            },
            {
                "template_id": "position_size_validator",
                "title": "Position Size Validator",
                "category": "Risk Management - Comprehensive",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Validate and optimize my planned position size:

PLANNED TRADE:
- Asset: [coin]
- Planned Position Size: $[amount] or [%]
- Entry: $[price]
- Stop Loss: $[price]
- Take Profit: $[price]
- Leverage: [x]
- Reasoning: [your reasoning]

ACCOUNT:
- Balance: $[amount]
- Current Risk Exposure: [%]
- Recent Performance: [pattern]

VALIDATION CHECKS:
✓ Risk per trade within limits?
✓ Portfolio correlation acceptable?
✓ Leverage safe for volatility?
✓ Sizing consistent with setup quality?
✓ Margin sufficient with buffer?
✓ Emotional/psychological factors considered?
✓ Drawdown impact acceptable?
✓ Exit strategy feasible?

Provide JSON with validation results, overall approval status (APPROVED/APPROVED WITH CHANGES/REJECTED), specific adjustments needed, risk score (1-10), warnings, and alternative suggestions.""",
                "risk_management": "Pre-trade validation and optimization",
                "best_for": "Pre-trade validation, second opinion checks",
                "metadata": json.dumps({
                    "tags": ["Validation", "Pre-Trade Check", "Optimization"],
                    "difficulty": "Intermediate",
                    "use_case": "Pre-trade validation, second opinion checks"
                })
            },
            
            # SPECIALIZED PROMPTS
            {
                "template_id": "news_event_sizing",
                "title": "News/Event Position Sizing",
                "category": "Risk Management - Specialized",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Calculate position size for news-driven trade:

EVENT DETAILS:
- Event: [type]
- Expected Volatility: [Low/Medium/High/Extreme]
- Historical Price Impact: [%]
- Time Until Event: [hours/days]
- Outcome Scenarios: [list]

TRADE PLAN:
- Asset: [coin]
- Direction: [LONG/SHORT/NEUTRAL]
- Strategy: [Before/After/Straddle]
- Normal Position Size: [%]

RISK CONSIDERATIONS:
- Gap Risk: [Low/Medium/High]
- Liquidity Risk: [Low/Medium/High]
- Slippage Expectation: [%]
- Stop Loss Reliability: [High/Medium/Low]

Provide JSON with event-adjusted position size, risk reduction factor, pre-event vs post-event sizing, contingency sizes, maximum safe exposure, and exit timing recommendations.""",
                "risk_management": "Event-driven risk adjustment",
                "best_for": "FOMC, earnings, forks, major announcements",
                "metadata": json.dumps({
                    "tags": ["News Events", "Volatility", "Event-Driven"],
                    "difficulty": "Advanced",
                    "use_case": "FOMC, earnings, forks, major announcements"
                })
            },
            {
                "template_id": "recovery_phase_sizing",
                "title": "Recovery Phase Position Sizing",
                "category": "Risk Management - Specialized",
                "timeframe": "All",
                "win_rate_estimate": "N/A",
                "prompt": """Calculate position sizing during account recovery:

RECOVERY STATUS:
- Starting Drawdown: [%]
- Current Drawdown: [%]
- Recovery Progress: [%]
- Days in Recovery: [days]
- Recovery Target: [target]

RECOVERY PERFORMANCE:
- Win Rate in Recovery: [%]
- Average Win: [%]
- Average Loss: [%]
- Consecutive Wins: [count]
- Confidence Level: [1-10]

TRADE OPPORTUNITY:
- Asset: [coin]
- Setup Quality: [A/B/C]
- Standard Size (if at peak): [%]
- Risk Level: [Low/Medium/High]

PSYCHOLOGICAL FACTORS:
- Pressure Level: [Low/Medium/High]
- Patience Level: [Low/Medium/High]
- Temptation to Over-trade: [Low/Medium/High]

Provide JSON with conservative position size, progressive sizing plan, milestones to increase size, win rate needed for recovery, time estimate, psychological checkpoints, and red flags to watch.""",
                "risk_management": "Progressive recovery-based sizing",
                "best_for": "After drawdown, rebuilding confidence",
                "metadata": json.dumps({
                    "tags": ["Recovery", "Drawdown", "Psychology"],
                    "difficulty": "Intermediate",
                    "use_case": "After drawdown, rebuilding confidence"
                })
            },
        ]
        
        # Insert prompts
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for prompt_data in risk_prompts:
            # Check if template already exists
            existing = db.query(models.TradingPromptTemplate).filter(
                models.TradingPromptTemplate.template_id == prompt_data["template_id"]
            ).first()
            
            if existing:
                # Update existing template
                for key, value in prompt_data.items():
                    setattr(existing, key, value)
                updated_count += 1
                print(f"   ✅ Updated: {prompt_data['title']}")
            else:
                # Create new template
                new_template = models.TradingPromptTemplate(**prompt_data)
                db.add(new_template)
                created_count += 1
                print(f"   ✨ Created: {prompt_data['title']}")
        
        db.commit()
        
        print(f"\n✅ Seeding completed!")
        print(f"   Created: {created_count}")
        print(f"   Updated: {updated_count}")
        print(f"   Total: {created_count + updated_count} Risk Management templates")
        
    except Exception as e:
        print(f"❌ Error seeding prompts: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_risk_management_prompts()


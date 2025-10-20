-- Migration: Create prompt templates table and seed trading prompts
-- Created: 2025-10-01
-- Description: Store trading strategy prompts for AI trading bots

-- Create prompt templates table
CREATE TABLE IF NOT EXISTS prompt_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    timeframe VARCHAR(50),
    win_rate_estimate VARCHAR(50),
    prompt TEXT NOT NULL,
    risk_management TEXT,
    best_for TEXT,
    metadata JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_template_id (template_id),
    INDEX idx_category (category),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed trading strategy prompts
INSERT INTO prompt_templates (template_id, title, category, timeframe, win_rate_estimate, prompt, risk_management, best_for, metadata) VALUES

-- EMA Ribbon System
('ema_ribbon_precise', 'EMA Ribbon System (High Win Rate)', 'Technical - Refined', '4H, Daily', '65-72%',
'ENTRY: BUY when price closes above EMA8, EMA21, EMA55 in order AND EMA8 crosses above EMA21 in last 3 candles. RSI must be 45-65. Volume > 1.5x of 20-period MA. STOP LOSS: 2% below entry OR below EMA55, whichever is closer. TAKE PROFIT: TP1 at 1:1.5 RR (take 40%), TP2 at 1:2.5 RR (take 40%), TP3 at 1:4 RR (let 20% run with trailing stop). TRAILING STOP: After TP1 hit, move SL to breakeven. After TP2, trail with EMA21. EXIT SIGNAL: Close below EMA21 on 4H. AVOID: ADX < 25 (weak trend).',
'Max 2% per trade, position size = (Account * 2%) / SL distance',
'BTC, ETH on trending markets',
JSON_OBJECT('tags', JSON_ARRAY('EMA', 'Trend Following', 'High Win Rate'), 'difficulty', 'Intermediate')),

-- Order Flow Imbalance
('order_flow_imbalance', 'Order Flow Imbalance (Institutional)', 'Smart Money - Advanced', '15m, 1H', '58-65%',
'ENTRY: BUY when CVD shows 3+ consecutive green bars AND price sweeps liquidity below recent low. Enter on first bullish engulfing after sweep. STOP LOSS: 1.5% below liquidity sweep low. TAKE PROFIT: TP1 at previous range midpoint (50% position), TP2 at range high (30%), TP3 at 1:4 RR (20% runner). TRAILING STOP: Use 15m swing lows after TP1. MAX HOLD TIME: Exit within 8 hours if no movement. INVALIDATION: If price re-enters sweep zone.',
'1.5% risk, scale out in 3 tranches: 50%-30%-20%',
'High liquidity pairs, BTC/USDT futures',
JSON_OBJECT('tags', JSON_ARRAY('Smart Money', 'Order Flow', 'Advanced'), 'difficulty', 'Advanced')),

-- VWAP Mean Reversion
('vwap_deviation_mean_reversion', 'VWAP Mean Reversion (Proven)', 'Technical - Statistical', '5m, 15m, 1H', '70-78%',
'ENTRY: BUY when price drops 2+ std below VWAP, RSI < 30, volume spike > 2x. Enter on first green candle close. STOP LOSS: 1.5% OR below next support level, whichever is tighter. TAKE PROFIT: TP1 at VWAP (take 60%), TP2 at VWAP + 0.5 std (30%), TP3 at VWAP + 1 std (10%). TIME LIMIT: Exit all within 6 candles if no reversion. REVERSE SETUP: SELL when 2+ std above VWAP, RSI > 70. Same SL/TP logic inverted.',
'3% max risk, tight stops due to high win rate',
'Intraday, range-bound markets',
JSON_OBJECT('tags', JSON_ARRAY('VWAP', 'Mean Reversion', 'Statistical'), 'difficulty', 'Intermediate')),

-- Supply Demand Zone
('supply_demand_zone_pro', 'Supply/Demand Zone Entry (Institutional)', 'Smart Money - Refined', '1H, 4H', '62-68%',
'ENTRY: BUY at demand zone with bullish rejection (wick > 50% candle). Volume 1.5x on rejection. STOP LOSS: 10 pips below demand zone OR 2% max. TAKE PROFIT: TP1 at 50% to previous swing high (40% out), TP2 at swing high (40% out), TP3 at 1:4 RR if zone was fresh (20% runner). ZONE VALIDITY: Only use zones touched < 3 times. Fresh zones preferred. INVALIDATION: If price closes below zone.',
'2% risk, prefer 1:3 minimum RR',
'All major pairs, trending conditions',
JSON_OBJECT('tags', JSON_ARRAY('Supply Demand', 'Smart Money', 'Zones'), 'difficulty', 'Intermediate')),

-- Turtle Soup
('turtle_soup_false_breakout', 'Turtle Soup (False Breakout Reversal)', 'Price Action - Classic', '4H, Daily', '55-63%',
'ENTRY: When breakout fails within 2 candles, enter opposite direction. STOP LOSS: 1% beyond false breakout extreme. TAKE PROFIT: TP1 at range midpoint (50%), TP2 at opposite range boundary (30%), TP3 at 1:3 RR if momentum continues (20%). TRAILING: After TP1, move SL to breakeven. After TP2, trail with 4H swing points. TIME LIMIT: Exit within 48 hours if consolidating.',
'2.5% risk, wider stop due to volatility',
'Volatile altcoins, news-driven false moves',
JSON_OBJECT('tags', JSON_ARRAY('False Breakout', 'Reversal', 'Price Action'), 'difficulty', 'Advanced')),

-- Funding Rate Extreme
('funding_rate_extreme_contrarian', 'Funding Rate Extreme Reversal', 'On-chain - Quantified', '1H, 4H', '60-70%',
'ENTRY: BUY when funding < -0.05% for 8+ hours, OI declining 10%+, price holds support. STOP LOSS: 3% OR below weekly support. TAKE PROFIT: TP1 when funding reaches -0.01% (40%), TP2 when funding neutral 0.00% (40%), TP3 when funding positive +0.02% (20%). TIME BASED: Monitor every 8 hours. REVERSAL EXIT: If funding continues extreme for 48+ hours, reconsider position.',
'Max 3% risk, can scale into 2 entries',
'Perpetual futures during high volatility',
JSON_OBJECT('tags', JSON_ARRAY('Funding Rate', 'On-chain', 'Contrarian'), 'difficulty', 'Advanced')),

-- Ichimoku Cloud
('ichimoku_cloud_breakout', 'Ichimoku Cloud Breakout (Complete)', 'Technical - Holistic', '4H, Daily', '64-71%',
'ENTRY: BUY above cloud, Tenkan > Kijun, Chikou clear, future cloud green, volume > 1.5x. STOP LOSS: Below Kijun line OR cloud bottom, max 3%. TAKE PROFIT: TP1 at 1x cloud thickness (40%), TP2 at 2x cloud thickness (40%), TP3 at 3x cloud or major resistance (20% runner). TRAILING: Use Kijun line as dynamic trailing stop. EXIT: If Tenkan crosses below Kijun, exit all positions.',
'2% risk, cloud provides natural stop levels',
'BTC, ETH, strong trend markets',
JSON_OBJECT('tags', JSON_ARRAY('Ichimoku', 'Cloud', 'Trend'), 'difficulty', 'Intermediate')),

-- Volume Profile POC
('volume_profile_poc_bounce', 'Volume Profile POC Bounce', 'Volume - Advanced', '1H, 4H, Daily', '68-75%',
'ENTRY: BUY at POC retest with bullish rejection, volume > 1.3x, RSI 45-60. STOP LOSS: 1.5% beyond POC OR below Value Area Low. TAKE PROFIT: TP1 at Value Area High / 50% distance (50%), TP2 at Value Area High (30%), TP3 at previous range high (20%). POC RECLAIM: If POC breaks, flip to opposite side. CONSOLIDATION: Best in 48-72h ranges.',
'2% risk, tight stops at statistical levels',
'BTC/ETH consolidation phases',
JSON_OBJECT('tags', JSON_ARRAY('Volume Profile', 'POC', 'Statistical'), 'difficulty', 'Advanced')),

-- RSI Divergence
('rsi_divergence_strict', 'RSI Divergence (Strict Criteria)', 'Technical - Refined', '1H, 4H', '56-64%',
'ENTRY: Bullish divergence with 3+ touches, RSI second low > 35, volume confirms. Enter on break above minor high. STOP LOSS: 2% below recent swing low. TAKE PROFIT: TP1 at RSI 60 level (50%), TP2 at 1:2 RR or RSI 70 (30%), TP3 at 1:3 RR (20%). FILTER: Avoid if ADX > 40 (too strong trend). BEARISH DIVERGENCE: Inverse setup, TP when RSI reaches 30-40.',
'2% risk, divergence can take time to play out',
'Ranging to mild trending markets',
JSON_OBJECT('tags', JSON_ARRAY('RSI', 'Divergence', 'Momentum'), 'difficulty', 'Intermediate')),

-- London Session Breakout
('session_breakout_london', 'London Session Breakout (Time-Based)', 'Price Action - Session', '15m, 1H', '62-69%',
'ENTRY: Break Asian range high/low in first 2h of London (08:00-10:00 UTC), volume > 2x. STOP LOSS: 1.5% OR middle of Asian range. TAKE PROFIT: TP1 at 1x Asian range height (60%), TP2 at 1.5x range height (30%), TP3 at 2x range height (10%). TIME LIMIT: Exit all before NY close (21:00 UTC) if target not hit. LOW VOLATILITY: Skip if ATR < 70% of 20-day average.',
'1.5% risk, time-based strategy needs discipline',
'BTC, ETH during major sessions',
JSON_OBJECT('tags', JSON_ARRAY('Session Breakout', 'London', 'Time-Based'), 'difficulty', 'Intermediate')),

-- Smart Money Liquidity Grab
('liquidity_grab_smc', 'Smart Money Concept - Liquidity Grab', 'Smart Money - Precise', '15m, 1H, 4H', '58-66%',
'ENTRY: After liquidity sweep + engulfing reversal, volume > 2x. Enter on break of engulfing high. STOP LOSS: 1-2% below sweep low. TAKE PROFIT: TP1 at previous range high or 1:2 RR (50%), TP2 at 1:3 RR (30%), TP3 at next major high or 1:5 RR (20%). MARKET STRUCTURE: Confirm higher high formation. TRAILING: Use 15m/1H structure breaks as trailing stops.',
'2% risk, tight stop after sweep completes',
'Liquid markets, major trading sessions',
JSON_OBJECT('tags', JSON_ARRAY('SMC', 'Liquidity', 'Smart Money'), 'difficulty', 'Advanced')),

-- Bollinger Band Squeeze
('bollinger_band_squeeze_expansion', 'Bollinger Band Squeeze + Expansion', 'Volatility - Statistical', '1H, 4H, Daily', '65-72%',
'ENTRY: First close above upper BB after squeeze (bands < 70% avg for 5+ candles), volume > 2x. STOP LOSS: Below lower BB OR 2%, whichever tighter. TAKE PROFIT: TP1 at 1x BB width (40%), TP2 at 2x BB width (40%), TP3 at 3x BB width or major resistance (20%). MIDDLE BB EXIT: If closes below middle BB, exit remaining. DIRECTION: Confirm with EMA20 slope.',
'2% risk, squeeze provides natural volatility metrics',
'News events, major announcements',
JSON_OBJECT('tags', JSON_ARRAY('Bollinger Bands', 'Squeeze', 'Volatility'), 'difficulty', 'Intermediate')),

-- Three Bar Reversal
('three_bar_reversal', 'Three-Bar Reversal Pattern (Proven)', 'Price Action - Pattern', '4H, Daily', '60-67%',
'ENTRY: Bar 3 engulfs Bar 1&2 with volume > 1.8x at key support/resistance. STOP LOSS: 1.5-2% below Bar 3 low. TAKE PROFIT: TP1 at 50% to previous swing (40%), TP2 at previous swing high (40%), TP3 at 1:3 RR (20%). RSI FILTER: RSI 30-50 on bullish reversal. INVALIDATION: If Bar 4 closes below Bar 3 low within 50% of range.',
'2.5% risk, reversal patterns need room',
'Major S/R reversals',
JSON_OBJECT('tags', JSON_ARRAY('Three Bar', 'Reversal', 'Pattern'), 'difficulty', 'Intermediate')),

-- Composite High Probability
('composite_high_probability', 'Composite High-Probability Setup', 'Multi-Factor - Elite', '4H, Daily', '72-80%',
'ENTRY: ALL 7 CONDITIONS: (1) EMA alignment, (2) RSI 50-65, (3) MACD positive & rising, (4) Volume > 1.5x, (5) Demand zone, (6) HTF aligned, (7) Clear path to 1:2. STOP LOSS: 2% OR below structure. TAKE PROFIT: TP1 at 1:2 RR (40%), TP2 at 1:3 RR (40%), TP3 at 1:5 RR (20% runner). TRAILING: After TP1, trail with structure. MAX TRADES: Only 2-3 per week with full criteria.',
'Max 2% risk, highest quality = highest position size allowed',
'Patient traders, best RR setups',
JSON_OBJECT('tags', JSON_ARRAY('Composite', 'High Probability', 'Multi-Factor'), 'difficulty', 'Advanced')),

-- Market Structure Break
('market_structure_break', 'Market Structure Break (BOS/CHoCH)', 'Smart Money - Structure', '15m, 1H, 4H', '61-68%',
'ENTRY: BOS confirmed, wait for 50-61.8% Fib pullback to demand zone. Enter on rejection with volume > 1.4x. STOP LOSS: 1.5% below demand zone. TAKE PROFIT: TP1 at previous structure high / 50% (40%), TP2 at next resistance (40%), TP3 at 1:4 RR (20%). FIB LEVELS: Best entries at 0.618 or 0.5. STRUCTURE: Update stops with each new higher low.',
'2% risk, structure provides clear levels',
'All trending markets',
JSON_OBJECT('tags', JSON_ARRAY('BOS', 'CHoCH', 'Structure Break'), 'difficulty', 'Advanced')),

-- Advanced Scalping
('advanced_scalping', 'Advanced Scalping System', 'Scalping - Elite', '1m, 5m, 15m', '68-75%',
'ENTRY: 5m inside bar breakout + 15m trend + orderbook confirmation (bid/ask > 1.3). Volume must exceed 2x on breakout bar. STOP LOSS: 0.8-1% (tight for scalping). TAKE PROFIT: TP1 at 1:1 RR (70% out), TP2 at 1:1.5 RR (30% out). TIME LIMIT: Exit ALL within 30 minutes max. SESSIONS: Only trade London (08:00-12:00 UTC) and NY open (13:00-17:00 UTC). AVOID: News events, low volume periods.',
'Max 1% risk, 5-10 trades per day max',
'Active traders with Level 2 data',
JSON_OBJECT('tags', JSON_ARRAY('Scalping', 'Intraday', 'Fast'), 'difficulty', 'Expert')),

-- Swing Trading Pro
('swing_trading_pro', 'Swing Trading Pro System', 'Swing - Position', 'Daily, Weekly', '60-70%',
'ENTRY: Weekly higher high + Daily pullback to 0.618 Fib + demand zone + RSI 40-55. Volume on pullback should decrease, then spike on reversal > 1.5x. STOP LOSS: 3-4% below weekly structure OR major support. TAKE PROFIT: TP1 at 1:2 RR (30%), TP2 at 1:3 RR (30%), TP3 at 1:5+ RR (40% runner for trend). WEEKLY REVIEW: Reassess every Sunday. TRAILING: Trail with weekly swing lows after TP1.',
'Max 2% risk per trade, hold 1-4 weeks typical',
'Patient traders, BTC/ETH/top 20 coins',
JSON_OBJECT('tags', JSON_ARRAY('Swing', 'Position', 'Multi-Timeframe'), 'difficulty', 'Intermediate')),

-- 1. EMA RIBBON ENHANCED (Crypto Optimized)
('ema_ribbon_crypto_v2', 'EMA Ribbon Crypto Enhanced', 'Technical - Elite', '4H, Daily', '68-75%',
'ENTRY: Price > EMA8 > EMA21 > EMA55 + EMA8 crosses EMA21 in last 2 candles + RSI 48-68 + Volume > 1.8x MA(20) + BTC dominance stable (±2%). CRYPTO FILTER: Avoid if BTC drops >3% in 24h. STOP LOSS: 2.5% below EMA55 (crypto volatility buffer). TAKE PROFIT: TP1 at 1:2 RR (35%), TP2 at 1:3.5 RR (40%), TP3 at 1:6 RR (25% runner). TRAILING: After TP1→breakeven, After TP2→EMA21 trail. EXIT: Close below EMA21 OR ADX drops <22.',
'1.5-2% risk per trade, reduce during BTC uncertainty',
'BTC, ETH, SOL, XRP - trending markets only',
JSON_OBJECT('tags', JSON_ARRAY('EMA', 'Crypto Optimized', 'Trend'), 'win_rate', '68-75%', 'difficulty', 'Intermediate')),

-- 2. LIQUIDITY SWEEP + FAIR VALUE GAP (SMC Premium)
('liquidity_fvg_combo', 'Liquidity Sweep + FVG Combo (Premium SMC)', 'Smart Money - Premium', '15m, 1H, 4H', '64-72%',
'ENTRY: (1) Sweep of equal lows/highs with wick rejection >60%, (2) FVG formation immediately after, (3) Price returns to fill 50-75% of FVG, (4) Volume spike >2.5x, (5) Order Flow Delta positive on 1H. Enter on first bullish close in FVG. STOP LOSS: 1.8% below sweep low (tight). TAKE PROFIT: TP1 at opposite liquidity level (45%), TP2 at 1:3 RR (35%), TP3 at major resistance/1:5 RR (20%). TIMEFRAME SYNC: 15m entry, 1H/4H confirmation.',
'Max 2% risk, works best during high volume sessions (UTC 08:00-20:00)',
'BTC/USDT, ETH/USDT perpetuals - high liquidity required',
JSON_OBJECT('tags', JSON_ARRAY('SMC', 'FVG', 'Liquidity Sweep'), 'win_rate', '64-72%', 'difficulty', 'Advanced')),

-- 3. VWAP + ORDERFLOW HYBRID (Institutional Grade)
('vwap_orderflow_pro', 'VWAP + Orderflow Pro System', 'Quantitative - Institutional', '5m, 15m, 1H', '72-80%',
'ENTRY: Price -2 std from VWAP + RSI <28 + CVD 3+ green bars + Delta >70% bullish + Volume explosion >3x. Enter on first 5m close back inside -1.5 std. STOP LOSS: 1.2% OR recent swing low (tighter stop for high WR). TAKE PROFIT: TP1 at VWAP (65%), TP2 at VWAP +0.8 std (25%), TP3 at VWAP +1.5 std (10%). TIME LIMIT: Exit within 8 candles if no movement. REVERSE: Same logic inverted for +2 std shorts.',
'3% risk allowed due to 72-80% win rate, but use tight stops',
'Intraday BTC/ETH during consolidation or range-bound phases',
JSON_OBJECT('tags', JSON_ARRAY('VWAP', 'Order Flow', 'Statistical'), 'win_rate', '72-80%', 'difficulty', 'Advanced')),

-- 4. MULTI-TIMEFRAME STRUCTURE BREAK (HTF Aligned)
('mtf_structure_break', 'Multi-Timeframe Structure Break', 'Structure - Professional', '1H, 4H, Daily', '66-74%',
'ENTRY: ALL ALIGN: Daily BOS bullish + 4H pullback to 0.5-0.618 Fib + 1H demand zone hold + Volume decrease on pullback + Volume spike >2x on reversal + RSI 4H: 45-60. STOP LOSS: 2.5% below 1H demand zone. TAKE PROFIT: TP1 at 4H structure high (35%), TP2 at Daily resistance/1:3 RR (40%), TP3 at 1:5+ RR (25% runner). UPDATE: Move stop to breakeven after TP1, trail with 4H swing lows after TP2.',
'Max 2% risk, high-quality setups only (2-4 per week)',
'All top 20 crypto, best during established trends',
JSON_OBJECT('tags', JSON_ARRAY('MTF', 'Structure', 'BOS'), 'win_rate', '66-74%', 'difficulty', 'Advanced')),

-- 5. FUNDING RATE + OPEN INTEREST DIVERGENCE
('funding_oi_divergence', 'Funding + OI Divergence (Quantified)', 'On-chain - Quantified', '1H, 4H', '63-71%',
'ENTRY: Funding rate extreme (<-0.08% or >+0.08% for 12+ hours) + OI declining 15%+ while price stable + Long/Short ratio extreme (>2.5 or <0.4) + Price at key support/resistance. STOP LOSS: 3.5% OR weekly structure. TAKE PROFIT: TP1 at funding normalization to -0.02/+0.02 (40%), TP2 at funding neutral 0.00% (35%), TP3 at funding reversal extreme (25%). MONITOR: Check funding every 8 hours. Exit if extreme persists >72h.',
'Max 2.5% risk, can scale in with 2 entries (60% + 40%)',
'BTC, ETH perpetuals during extreme sentiment periods',
JSON_OBJECT('tags', JSON_ARRAY('Funding', 'OI', 'Contrarian'), 'win_rate', '63-71%', 'difficulty', 'Advanced')),

-- 6. SESSION BREAKOUT + LIQUIDITY (Time-Based Edge)
('session_liquidity_breakout', 'Session Breakout + Liquidity Zones', 'Price Action - Session', '15m, 1H', '65-73%',
'ENTRY: Asian range established (min 4 hours) + London open (08:00 UTC) breaks high/low + Sweep of obvious liquidity first + Volume >2.5x + No major news in 2 hours. Enter on retest of breakout level. STOP LOSS: 1.5% OR middle of Asian range. TAKE PROFIT: TP1 at 1x range height (50%), TP2 at 1.5x range (30%), TP3 at 2x range (20%). TIME LIMIT: Exit before 21:00 UTC if targets not hit. SKIP: If ATR <75% of 20-period average.',
'1.5% risk, best for active traders in major sessions',
'BTC, ETH - high liquidity during London/NY sessions',
JSON_OBJECT('tags', JSON_ARRAY('Session', 'Liquidity', 'Breakout'), 'win_rate', '65-73%', 'difficulty', 'Intermediate')),

-- 7. BOLLINGER SQUEEZE + MACD ACCELERATION
('bb_squeeze_macd_v2', 'BB Squeeze + MACD Momentum', 'Volatility - Momentum', '1H, 4H', '68-76%',
'ENTRY: BB squeeze <65% avg width for 6+ candles + MACD histogram rising for 3 bars + First close above upper BB + Volume explosion >2.8x + Clear directional bias (EMA20 slope). STOP LOSS: Below middle BB OR 2.2% max. TAKE PROFIT: TP1 at 1.5x BB width (40%), TP2 at 2.5x BB width (35%), TP3 at 3.5x BB width or major resistance (25%). EXIT: If closes back inside middle BB.',
'2% risk, squeeze patterns offer excellent RR',
'All major crypto, best around news events or after consolidation',
JSON_OBJECT('tags', JSON_ARRAY('Bollinger', 'MACD', 'Squeeze'), 'win_rate', '68-76%', 'difficulty', 'Intermediate')),

-- 8. VOLUME PROFILE + GAMMA LEVELS (Options Flow)
('vp_gamma_squeeze', 'Volume Profile + Gamma Squeeze', 'Institutional - Quant', '1H, 4H, Daily', '70-78%',
'ENTRY: Price at POC + high gamma strike nearby + Imbalanced volume profile (HVN cluster) + Bullish rejection with volume >1.8x + RSI 47-62. STOP LOSS: 2% below VAL (Value Area Low) OR POC. TAKE PROFIT: TP1 at VAH (Value Area High) or 50% to target (45%), TP2 at next gamma level (35%), TP3 at upper HVN (20%). GAMMA SQUEEZE: If volume accelerates near strikes, trail aggressively.',
'Max 2% risk, institutional-grade edge during options expiry weeks',
'BTC, ETH with active options markets (monthly/quarterly expiry)',
JSON_OBJECT('tags', JSON_ARRAY('Volume Profile', 'Gamma', 'Options'), 'win_rate', '70-78%', 'difficulty', 'Advanced')),

-- 9. ELLIOTT WAVE + FIBONACCI CONFLUENCE
('elliott_fib_confluence', 'Elliott Wave + Fib Confluence', 'Technical - Advanced', '4H, Daily, Weekly', '58-67%',
'ENTRY: Wave 4 correction complete at 0.382-0.618 Fib + RSI reset to 40-55 + Volume declining on correction, spiking on Wave 5 start + Structure holds (no Wave 4 into Wave 1 territory). STOP LOSS: 3% below Wave 4 low OR 0.786 Fib. TAKE PROFIT: TP1 at 1.618 extension (30%), TP2 at 2.0 extension (40%), TP3 at 2.618 extension (30%). INVALIDATION: Wave 4 enters Wave 1 territory.',
'Max 2.5% risk, requires pattern recognition skill',
'BTC, ETH on higher timeframes for swing/position trades',
JSON_OBJECT('tags', JSON_ARRAY('Elliott Wave', 'Fibonacci', 'Wave Theory'), 'win_rate', '58-67%', 'difficulty', 'Expert')),

-- 10. ADAPTIVE MOMENTUM SYSTEM (AI-Enhanced)
('adaptive_momentum_ai', 'Adaptive Momentum System', 'Quantitative - AI', '15m, 1H, 4H', '71-79%',
'ENTRY: RSI(14) slope positive for 3+ bars + Stochastic crosses in 20-40 zone + MACD histogram acceleration + Volume ROC >150% + ATR expanding >20% + Price above VWAP + Higher timeframe aligned (4H trend = 1H entry direction). STOP LOSS: ATR-based: 1.5x ATR(14) below entry. TAKE PROFIT: Dynamic: TP1 at 2x ATR (40%), TP2 at 3.5x ATR (35%), TP3 at 5x ATR with trailing (25%). ADAPTIVE: Tighten stops in low volatility, widen in high volatility.',
'Max 2% risk, adapts to market conditions automatically',
'All top 30 crypto, works in trending and ranging markets',
JSON_OBJECT('tags', JSON_ARRAY('AI', 'Adaptive', 'Momentum'), 'win_rate', '71-79%', 'difficulty', 'Expert')),

-- 11. COMPOSITE ULTRA-HIGH PROBABILITY (The 10-Factor System)
('composite_ultra_elite', 'Composite Ultra (10-Factor System)', 'Multi-Factor - Elite', '4H, Daily', '76-85%',
'ENTRY: ALL 10 CONDITIONS MUST ALIGN:
(1) Daily + 4H trend aligned (EMA8>21>55)
(2) RSI 52-68 on 4H, >50 on Daily  
(3) MACD positive + rising on both TFs
(4) Volume spike >2x on entry candle
(5) At institutional demand zone (touched <3 times)
(6) Fair Value Gap filled 50-70%
(7) Fibonacci 0.5-0.618 pullback zone
(8) BTC correlation positive (for altcoins)
(9) Clear 1:3 RR minimum path
(10) No major resistance within 5%

STOP LOSS: 2.5% OR below structure (whichever tighter). 
TAKE PROFIT: TP1 at 1:3 RR (30%), TP2 at 1:5 RR (40%), TP3 at 1:8+ RR (30% runner).
TRAILING: Breakeven after TP1, 4H structure after TP2.
MAX FREQUENCY: Only 1-2 setups per week - QUALITY OVER QUANTITY.',
'Max 3% risk due to exceptional win rate (76-85%)',
'Patient traders, BTC/ETH/top 10 coins only',
JSON_OBJECT('tags', JSON_ARRAY('Composite', 'Ultra Elite', '10-Factor'), 'win_rate', '76-85%', 'difficulty', 'Expert')),

-- 12. SWING POSITION SYSTEM (Crypto Bull/Bear Cycles)
('swing_position_crypto', 'Crypto Swing Position System', 'Position - Macro', 'Daily, Weekly', '62-73%',
'ENTRY: Weekly BOS + Daily pullback to 0.618-0.786 Fib + Weekly demand zone + RSI Daily: 38-52 + Volume contraction on pullback, expansion on reversal + Bitcoin fear/greed <35 (for longs) or >75 (for shorts). STOP LOSS: 4-5% below weekly structure. TAKE PROFIT: TP1 at 1:2.5 RR (25%), TP2 at 1:4 RR (30%), TP3 at 1:6+ RR (45% long-term runner). WEEKLY REVIEW: Reassess position every Sunday. TRAILING: Trail with weekly swing lows after TP1.',
'Max 2% per trade, 4-8 week typical hold, max 3 positions',
'Patient traders - BTC, ETH, top 15 coins during confirmed trends',
JSON_OBJECT('tags', JSON_ARRAY('Swing', 'Position', 'Macro'), 'win_rate', '62-73%', 'difficulty', 'Intermediate')),
-- ═══════════════════════════════════════════════════════════════
-- CRYPTO SHORT/SELL STRATEGIES - ENHANCED EDITION
-- Optimized for BTC, ETH, XRP, and Top 50 Cryptocurrencies
-- Focus: Bearish setups with high win rates & proper risk management
-- ═══════════════════════════════════════════════════════════════

-- 1. EMA RIBBON SHORT (Crypto Optimized)
('ema_ribbon_short_v2', 'EMA Ribbon Short - Crypto Enhanced', 'Technical - Elite', '4H, Daily', '68-75%',
'ENTRY: Price < EMA8 < EMA21 < EMA55 + EMA8 crosses BELOW EMA21 in last 2 candles + RSI 32-52 + Volume > 1.8x MA(20) + BTC showing weakness (falling >2% in 24h). CRYPTO FILTER: Confirm BTC downtrend on Daily TF. STOP LOSS: 2.5% ABOVE EMA55 (crypto volatility buffer). TAKE PROFIT: TP1 at 1:2 RR (35%), TP2 at 1:3.5 RR (40%), TP3 at 1:6 RR (25% runner). TRAILING: After TP1→breakeven, After TP2→EMA21 trail (move down with EMA21). EXIT: Close ABOVE EMA21 OR ADX drops <22.',
'1.5-2% risk per trade, increase during clear bearish momentum',
'BTC, ETH, SOL, XRP - downtrending markets only',
JSON_OBJECT('tags', JSON_ARRAY('EMA', 'Short', 'Trend'), 'win_rate', '68-75%', 'difficulty', 'Intermediate')),

-- 2. LIQUIDITY GRAB SHORT + FAIR VALUE GAP
('liquidity_fvg_short', 'Liquidity Grab Short + FVG (Premium SMC)', 'Smart Money - Premium', '15m, 1H, 4H', '64-72%',
'ENTRY: (1) Sweep of equal HIGHS with wick rejection >60% to downside, (2) Bearish FVG formation immediately after, (3) Price rallies to fill 50-75% of FVG, (4) Volume spike >2.5x on rejection, (5) Order Flow Delta negative on 1H. Enter on first bearish close inside FVG zone. STOP LOSS: 1.8% ABOVE sweep high (tight). TAKE PROFIT: TP1 at opposite liquidity level / support (45%), TP2 at 1:3 RR (35%), TP3 at major support / 1:5 RR (20%). TIMEFRAME SYNC: 15m entry, 1H/4H bearish confirmation.',
'Max 2% risk, best during high volume bearish sessions (UTC 08:00-20:00)',
'BTC/USDT, ETH/USDT perpetuals - high liquidity required',
JSON_OBJECT('tags', JSON_ARRAY('SMC', 'FVG', 'Short'), 'win_rate', '64-72%', 'difficulty', 'Advanced')),

-- 3. VWAP + ORDERFLOW SHORT (Institutional Grade)
('vwap_orderflow_short', 'VWAP + Orderflow Short System', 'Quantitative - Institutional', '5m, 15m, 1H', '72-80%',
'ENTRY: Price +2 std ABOVE VWAP + RSI >72 + CVD 3+ consecutive red bars + Delta >70% bearish + Volume explosion >3x. Enter on first 5m close back BELOW +1.5 std. STOP LOSS: 1.2% ABOVE recent swing high (tight stop for high WR). TAKE PROFIT: TP1 at VWAP (65%), TP2 at VWAP -0.8 std (25%), TP3 at VWAP -1.5 std (10%). TIME LIMIT: Exit within 8 candles if no movement. REVERSAL: Close position if CVD turns bullish.',
'3% risk allowed due to 72-80% win rate, but use tight stops',
'Intraday BTC/ETH during range-bound or distribution phases',
JSON_OBJECT('tags', JSON_ARRAY('VWAP', 'Short', 'Statistical'), 'win_rate', '72-80%', 'difficulty', 'Advanced')),

-- 4. MULTI-TIMEFRAME STRUCTURE BREAK SHORT
('mtf_structure_break_short', 'Multi-Timeframe Structure Break Short', 'Structure - Professional', '1H, 4H, Daily', '66-74%',
'ENTRY: ALL ALIGN: Daily BOS bearish (break of structure to downside) + 4H rally/pullback to 0.5-0.618 Fib + 1H supply zone rejection + Volume decrease on rally + Volume spike >2x on rejection + RSI 4H: 40-55. STOP LOSS: 2.5% ABOVE 1H supply zone. TAKE PROFIT: TP1 at 4H structure low (35%), TP2 at Daily support / 1:3 RR (40%), TP3 at 1:5+ RR (25% runner). UPDATE: Move stop to breakeven after TP1, trail with 4H swing highs after TP2.',
'Max 2% risk, high-quality SHORT setups only (2-4 per week)',
'All top 20 crypto, best during established downtrends',
JSON_OBJECT('tags', JSON_ARRAY('MTF', 'Structure', 'Short'), 'win_rate', '66-74%', 'difficulty', 'Advanced')),

-- 5. FUNDING RATE EXTREME SHORT (Contrarian)
('funding_oi_divergence_short', 'Funding + OI Extreme Short', 'On-chain - Quantified', '1H, 4H', '63-71%',
'ENTRY: Funding rate EXTREMELY positive (>+0.08% for 12+ hours) + OI increasing 15%+ while price stalling/diverging + Long/Short ratio extreme (>3.0 = too many longs) + Price at key resistance rejection. STOP LOSS: 3.5% ABOVE weekly resistance. TAKE PROFIT: TP1 at funding normalization to +0.02 (40%), TP2 at funding neutral 0.00% (35%), TP3 at funding negative -0.05% (25%). MONITOR: Check funding every 8 hours. Exit if extreme persists >72h without price drop.',
'Max 2.5% risk, can scale in with 2 entries (60% + 40%)',
'BTC, ETH perpetuals during extreme greed/euphoria periods',
JSON_OBJECT('tags', JSON_ARRAY('Funding', 'Short', 'Contrarian'), 'win_rate', '63-71%', 'difficulty', 'Advanced')),

-- 6. SESSION BREAKDOWN + LIQUIDITY SHORT
('session_liquidity_short', 'Session Breakdown + Liquidity Zones', 'Price Action - Session', '15m, 1H', '65-73%',
'ENTRY: Asian range established (min 4 hours) + London open (08:00 UTC) breaks BELOW low + Sweep of obvious buy-side liquidity + Volume >2.5x + No major news in 2 hours. Enter on retest of breakdown level from below. STOP LOSS: 1.5% ABOVE middle of Asian range. TAKE PROFIT: TP1 at 1x range height down (50%), TP2 at 1.5x range (30%), TP3 at 2x range (20%). TIME LIMIT: Exit before 21:00 UTC if targets not hit. SKIP: If ATR <75% of 20-period average.',
'1.5% risk, best for active traders in major sessions',
'BTC, ETH - high liquidity during London/NY sessions',
JSON_OBJECT('tags', JSON_ARRAY('Session', 'Short', 'Breakdown'), 'win_rate', '65-73%', 'difficulty', 'Intermediate')),

-- 7. BOLLINGER SQUEEZE BREAKDOWN + MACD
('bb_squeeze_short_v2', 'BB Squeeze Breakdown + MACD', 'Volatility - Momentum', '1H, 4H', '68-76%',
'ENTRY: BB squeeze <65% avg width for 6+ candles + MACD histogram declining for 3 bars + First close BELOW lower BB + Volume explosion >2.8x + Clear bearish bias (EMA20 sloping down). STOP LOSS: ABOVE middle BB OR 2.2% max. TAKE PROFIT: TP1 at -1.5x BB width (40%), TP2 at -2.5x BB width (35%), TP3 at -3.5x BB width or major support (25%). EXIT: If closes back ABOVE middle BB.',
'2% risk, squeeze breakdowns offer excellent RR',
'All major crypto, best after distribution or during bearish news',
JSON_OBJECT('tags', JSON_ARRAY('Bollinger', 'Short', 'Squeeze'), 'win_rate', '68-76%', 'difficulty', 'Intermediate')),

-- 8. VOLUME PROFILE POC REJECTION SHORT
('vp_poc_rejection_short', 'Volume Profile POC Rejection Short', 'Institutional - Quant', '1H, 4H, Daily', '70-78%',
'ENTRY: Price rallies to POC + Bearish rejection with wick >50% + High gamma strike above acting as resistance + Volume >1.8x on rejection + RSI 38-53. STOP LOSS: 2% ABOVE VAH (Value Area High) OR POC. TAKE PROFIT: TP1 at VAL (Value Area Low) or 50% to target (45%), TP2 at next gamma level below (35%), TP3 at lower HVN (20%). DISTRIBUTION SIGN: If volume profile shows selling distribution at POC.',
'Max 2% risk, institutional-grade SHORT edge near options expiry',
'BTC, ETH with active options markets (monthly/quarterly expiry)',
JSON_OBJECT('tags', JSON_ARRAY('Volume Profile', 'Short', 'POC'), 'win_rate', '70-78%', 'difficulty', 'Advanced')),

-- 9. ELLIOTT WAVE SHORT (Wave 3 or Wave C)
('elliott_wave_short', 'Elliott Wave Short - Wave 3/C', 'Technical - Advanced', '4H, Daily, Weekly', '58-67%',
'ENTRY: Wave 2 correction complete at 0.5-0.618 Fib retracement + RSI reset to 45-60 on pullback + Volume declining on Wave 2, spiking on Wave 3 start down + Structure: Wave 2 does NOT exceed Wave B high. STOP LOSS: 3% ABOVE Wave 2 high OR 0.786 Fib. TAKE PROFIT: TP1 at -1.618 extension (30%), TP2 at -2.0 extension (40%), TP3 at -2.618 extension (30%). INVALIDATION: Wave 2 goes above Wave B high (not a valid impulse).',
'Max 2.5% risk, requires Elliott Wave pattern recognition',
'BTC, ETH on higher timeframes for swing/position shorts',
JSON_OBJECT('tags', JSON_ARRAY('Elliott Wave', 'Short', 'Wave Theory'), 'win_rate', '58-67%', 'difficulty', 'Expert')),

-- 10. ADAPTIVE MOMENTUM SHORT SYSTEM
('adaptive_momentum_short', 'Adaptive Momentum Short System', 'Quantitative - AI', '15m, 1H, 4H', '71-79%',
'ENTRY: RSI(14) slope negative for 3+ bars + Stochastic crosses DOWN in 60-80 zone + MACD histogram declining + Volume ROC >150% + ATR expanding >20% + Price below VWAP + Higher timeframe bearish (4H trend = 1H short direction). STOP LOSS: ATR-based: 1.5x ATR(14) ABOVE entry. TAKE PROFIT: Dynamic: TP1 at -2x ATR (40%), TP2 at -3.5x ATR (35%), TP3 at -5x ATR with trailing (25%). ADAPTIVE: Tighten stops in low volatility, widen in high volatility.',
'Max 2% risk, adapts to bearish market conditions automatically',
'All top 30 crypto, works in downtrends and distribution phases',
JSON_OBJECT('tags', JSON_ARRAY('AI', 'Short', 'Adaptive'), 'win_rate', '71-79%', 'difficulty', 'Expert')),

-- 11. RISING WEDGE BREAKDOWN (Classic Pattern)
('rising_wedge_breakdown', 'Rising Wedge Breakdown Short', 'Pattern - Classic', '1H, 4H, Daily', '62-70%',
'ENTRY: Rising wedge formed (converging trend lines, 5+ touches) + Volume declining into apex + Breakdown below support line with volume >2.5x + Retest of broken support from below fails. STOP LOSS: 2.5% ABOVE wedge support line (now resistance). TAKE PROFIT: TP1 at wedge height measured down (40%), TP2 at 1.5x wedge height (35%), TP3 at 2x wedge height or major support (25%). CONFIRMATION: Wait for 4H close below wedge for higher probability.',
'Max 2% risk, classic pattern with measurable targets',
'All crypto during distribution phases or weak rallies',
JSON_OBJECT('tags', JSON_ARRAY('Wedge', 'Short', 'Pattern'), 'win_rate', '62-70%', 'difficulty', 'Intermediate')),

-- 12. BEARISH DIVERGENCE SHORT (RSI/MACD)
('bearish_divergence_short', 'Bearish Divergence Short System', 'Technical - Refined', '1H, 4H', '60-68%',
'ENTRY: Bearish divergence confirmed: Price makes higher high BUT RSI/MACD makes lower high (2-3 touches minimum) + RSI second peak <65 + Volume declining on second high + Break below minor support confirms reversal. STOP LOSS: 2.5% ABOVE recent swing high. TAKE PROFIT: TP1 at RSI 40 level (50%), TP2 at 1:2 RR or RSI 30 (30%), TP3 at 1:3 RR (20%). FILTER: Avoid if ADX <25 (need some trend strength for divergence to play out). EARLY EXIT: If RSI turns bullish before targets.',
'2% risk, divergence can take time - patience required',
'Ranging to mild downtrending markets, overbought conditions',
JSON_OBJECT('tags', JSON_ARRAY('RSI', 'Divergence', 'Short'), 'win_rate', '60-68%', 'difficulty', 'Intermediate')),

-- 13. DOUBLE TOP BREAKDOWN
('double_top_breakdown', 'Double Top Breakdown Short', 'Pattern - Classic', '4H, Daily', '64-72%',
'ENTRY: Double top formed (two peaks at similar level, <3% variance) + Neckline established + Break below neckline with volume >2x + Retest of neckline from below fails. STOP LOSS: 2% ABOVE second peak OR recent swing high. TAKE PROFIT: TP1 at 1x height of pattern measured from neckline (40%), TP2 at 1.5x height (35%), TP3 at 2x height or major support (25%). CONFIRMATION: Both peaks should have decreasing volume (distribution sign).',
'Max 2.5% risk, reliable pattern with clear targets',
'BTC, ETH, major crypto - best at market tops or resistance zones',
JSON_OBJECT('tags', JSON_ARRAY('Double Top', 'Short', 'Pattern'), 'win_rate', '64-72%', 'difficulty', 'Intermediate')),

-- 14. DEATH CROSS SHORT (Moving Average)
('death_cross_short', 'Death Cross Short System', 'Technical - Trend', 'Daily, Weekly', '58-66%',
'ENTRY: EMA50 crosses BELOW EMA200 (Death Cross confirmed) + Price trading below both EMAs + Volume increasing on down moves + RSI <55 and declining. STOP LOSS: 4% ABOVE EMA50 OR recent swing high. TAKE PROFIT: TP1 at next major support / 1:2 RR (30%), TP2 at 1:3 RR (35%), TP3 at 1:5+ RR (35% runner for extended bear trend). TRAILING: Trail stop with EMA50 (when price falls further). EXIT: If EMA50 crosses back above EMA200 (Golden Cross).',
'Max 2% risk per trade, longer-term position short',
'BTC, ETH - major trend reversal signal, hold weeks to months',
JSON_OBJECT('tags', JSON_ARRAY('Death Cross', 'Short', 'Long-term'), 'win_rate', '58-66%', 'difficulty', 'Beginner')),

-- 15. HEAD AND SHOULDERS BREAKDOWN
('head_shoulders_short', 'Head and Shoulders Breakdown', 'Pattern - Elite', '4H, Daily', '66-74%',
'ENTRY: H&S pattern complete (left shoulder, head, right shoulder) + Right shoulder lower volume than left + Neckline break with volume >2.5x + Retest fails. STOP LOSS: 2.5% ABOVE right shoulder high. TAKE PROFIT: TP1 at 1x head height from neckline (35%), TP2 at 1.5x height (40%), TP3 at 2x height or major support (25%). ADVANCED: Inverse H&S at bottom for long, regular H&S at top for short. INVALIDATION: Price closes above right shoulder.',
'Max 2% risk, one of the most reliable reversal patterns',
'All major crypto at market structure tops, high-timeframe',
JSON_OBJECT('tags', JSON_ARRAY('H&S', 'Short', 'Reversal'), 'win_rate', '66-74%', 'difficulty', 'Intermediate')),

-- 16. COMPOSITE ULTRA-HIGH PROBABILITY SHORT (10-Factor)
('composite_ultra_short', 'Composite Ultra Short (10-Factor)', 'Multi-Factor - Elite', '4H, Daily', '76-85%',
'ENTRY: ALL 10 CONDITIONS MUST ALIGN:
(1) Daily + 4H downtrend (EMA8<21<55)
(2) RSI 32-48 on 4H, <50 on Daily  
(3) MACD negative + declining on both TFs
(4) Volume spike >2x on entry candle (down move)
(5) At institutional supply zone (touched <3 times)
(6) Bearish Fair Value Gap filled 50-70%
(7) Fibonacci 0.5-0.618 retracement zone from recent down move
(8) BTC showing weakness (for altcoin shorts)
(9) Clear 1:3 RR minimum path to downside
(10) No major support within 5% below

STOP LOSS: 2.5% ABOVE structure (supply zone). 
TAKE PROFIT: TP1 at 1:3 RR (30%), TP2 at 1:5 RR (40%), TP3 at 1:8+ RR (30% runner).
TRAILING: Breakeven after TP1, 4H structure after TP2.
MAX FREQUENCY: Only 1-2 perfect SHORT setups per week - ULTRA SELECTIVE.',
'Max 3% risk due to exceptional 76-85% win rate',
'Patient traders, BTC/ETH/top 10 coins only, bear markets',
JSON_OBJECT('tags', JSON_ARRAY('Composite', 'Short', 'Ultra Elite'), 'win_rate', '76-85%', 'difficulty', 'Expert')),

-- 17. SWING POSITION SHORT SYSTEM (Bear Cycle)
('swing_position_short', 'Crypto Swing Position Short', 'Position - Macro', 'Daily, Weekly', '62-73%',
'ENTRY: Weekly BOS to downside + Daily rally to 0.618-0.786 Fib retracement + Weekly supply zone rejection + RSI Daily: 48-62 (overbought on pullback) + Volume contraction on rally, expansion on rejection + Bitcoin fear/greed >65 (greed, good for shorts). STOP LOSS: 4-5% ABOVE weekly supply zone. TAKE PROFIT: TP1 at 1:2.5 RR (25%), TP2 at 1:4 RR (30%), TP3 at 1:6+ RR (45% long-term runner). WEEKLY REVIEW: Reassess position every Sunday. TRAILING: Trail with weekly swing highs after TP1.',
'Max 2% per trade, 4-8 week typical hold, max 3 short positions',
'Patient traders - BTC, ETH, top 15 coins during confirmed bear trends',
JSON_OBJECT('tags', JSON_ARRAY('Swing', 'Short', 'Position'), 'win_rate', '62-73%', 'difficulty', 'Intermediate')),

-- 18. SUPPLY ZONE REJECTION SHORT
('supply_zone_rejection_short', 'Supply Zone Rejection Short', 'Smart Money - Refined', '1H, 4H', '62-68%',
'ENTRY: Price reaches SUPPLY zone (previous resistance, strong selling area) + Bearish rejection candle (wick >50% of candle to upside) + Volume 1.5x on rejection + RSI reaching 55-70 zone (overbought). STOP LOSS: 10 pips ABOVE supply zone OR 2% max. TAKE PROFIT: TP1 at 50% to previous swing low (40% out), TP2 at swing low (40% out), TP3 at 1:4 RR if zone was fresh (20% runner). ZONE VALIDITY: Only use zones touched < 3 times. Fresh zones preferred. INVALIDATION: If price closes ABOVE zone.',
'2% risk, prefer 1:3 minimum RR on shorts',
'All major pairs, downtrending or ranging conditions',
JSON_OBJECT('tags', JSON_ARRAY('Supply', 'Short', 'Zones'), 'win_rate', '62-68%', 'difficulty', 'Intermediate')),

-- 19. ICHIMOKU CLOUD BREAKDOWN SHORT
('ichimoku_cloud_short', 'Ichimoku Cloud Breakdown Short', 'Technical - Holistic', '4H, Daily', '64-71%',
'ENTRY: Price breaks BELOW cloud + Tenkan < Kijun + Chikou Span below price (bearish) + Future cloud red + Volume > 1.5x. STOP LOSS: ABOVE Kijun line OR cloud top, max 3%. TAKE PROFIT: TP1 at -1x cloud thickness (40%), TP2 at -2x cloud thickness (40%), TP3 at -3x cloud or major support (20% runner). TRAILING: Use Kijun line as dynamic trailing stop (move down with it). EXIT: If Tenkan crosses ABOVE Kijun, exit all positions immediately.',
'2% risk, cloud provides natural stop levels',
'BTC, ETH, strong downtrend markets',
JSON_OBJECT('tags', JSON_ARRAY('Ichimoku', 'Short', 'Cloud'), 'win_rate', '64-71%', 'difficulty', 'Intermediate')),

-- 20. TURTLE SOUP SHORT (False Breakout)
('turtle_soup_short', 'Turtle Soup Short - False Breakout', 'Price Action - Classic', '4H, Daily', '55-63%',
'ENTRY: Bullish breakout FAILS within 2 candles (price can not sustain above resistance) + Enter SHORT when breakout fails. STOP LOSS: 1% ABOVE false breakout high. TAKE PROFIT: TP1 at range midpoint (50%), TP2 at opposite range boundary / support (30%), TP3 at 1:3 RR if momentum continues (20%). TRAILING: After TP1, move SL to breakeven. After TP2, trail with 4H swing highs. TIME LIMIT: Exit within 48 hours if consolidating.',
'2.5% risk, wider stop due to volatility of false moves',
'Volatile altcoins, news-driven false breakouts (bull traps)',
JSON_OBJECT('tags', JSON_ARRAY('False Breakout', 'Short', 'Turtle Soup'), 'win_rate', '55-63%', 'difficulty', 'Advanced'));

-- ═══════════════════════════════════════════════════════════════
-- SHORT-SPECIFIC RISK MANAGEMENT (CRITICAL!)
-- ═══════════════════════════════════════════════════════════════
-- • SHORTS are more risky than longs in crypto (unlimited upside risk)
-- • Max 1.5-2% risk per SHORT trade (slightly lower than longs)
-- • NEVER hold shorts during major bullish news (FOMC dovish, BTC ETF approvals, etc.)
-- • Set STOP LOSS tighter on shorts - use 2-2.5% instead of 3%
-- • ALWAYS use stop losses on shorts (never "hope" it goes down)
-- • Exit shorts faster if momentum stalls - don't wait for all TPs
-- • Monitor funding rates - negative funding helps shorts, positive hurts
-- • Best SHORT environments: Bear markets, distribution phases, high RSI
-- • Avoid shorting during strong bull trends (low probability)
-- • Scale out aggressively - take profits faster on shorts than longs
-- • Max 2 short positions open at once (vs 3-4 longs allowed)
-- ═══════════════════════════════════════════════════════════════

-- CRYPTO SHORT FILTERS (Apply to ALL short strategies):
-- • NEVER short when BTC pumps >5% in 1 hour (wait for stabilization)
-- • Check if funding rate is NEGATIVE (helps shorts) - ideal <-0.01%
-- • Avoid shorting during "short squeeze" conditions (high funding + OI spike)
-- • Best shorting conditions: Fear & Greed Index >75 (extreme greed)
-- • Reduce SHORT size 24-48 hours before potential bullish news
-- • Be aware: Crypto has violent short squeezes - use TIGHT stops always
-- • Best shorting hours: Asian session dumps (00:00-04:00 UTC) or post-news
-- • Exit ALL shorts if BTC breaks major resistance (e.g., ATH, key psychological levels)

-- ═══════════════════════════════════════════════════════════════
-- RISK MANAGEMENT PRINCIPLES (APPLY TO ALL STRATEGIES)
-- ═══════════════════════════════════════════════════════════════
-- • Max 2-3% risk per trade (3% only for 70%+ win rate strategies)
-- • Max 6% total portfolio risk across all open positions
-- • Scale out in 3+ tranches - never exit all at once
-- • Move to breakeven after first TP hit
-- • Trail stops with structure on higher timeframes
-- • Reduce position size during high BTC volatility (>5% daily moves)
-- • Never trade during major news without 30min+ confirmation
-- • Keep win rate journal - if strategy drops 10% below expected, pause and review
-- ═══════════════════════════════════════════════════════════════

-- CRYPTO-SPECIFIC FILTERS (Apply to all strategies):
-- • Avoid trading when BTC drops >4% in 1 hour (wait for stabilization)
-- • Check BTC dominance - if shifting >2% rapidly, reduce altcoin exposure
-- • Monitor funding rates - extreme rates increase reversal probability
-- • Be aware of token unlock schedules (can cause dumps)
-- • Reduce size 24 hours before FOMC, CPI, major Fed announcements
-- • Best trading hours: 08:00-20:00 UTC (London + NY sessions));

-- Create prompt categories table for better organization
CREATE TABLE IF NOT EXISTS prompt_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_category VARCHAR(100),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category_name (category_name),
    INDEX idx_parent (parent_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed categories
INSERT INTO prompt_categories (category_name, description, parent_category, display_order) VALUES
('Technical - Refined', 'Refined technical analysis strategies with high accuracy', 'Technical', 1),
('Smart Money - Advanced', 'Advanced institutional trading concepts', 'Smart Money', 2),
('Technical - Statistical', 'Statistical and probability-based technical strategies', 'Technical', 3),
('Smart Money - Refined', 'Refined smart money concepts', 'Smart Money', 4),
('Price Action - Classic', 'Classic price action patterns', 'Price Action', 5),
('On-chain - Quantified', 'Quantified on-chain metrics strategies', 'On-chain', 6),
('Technical - Holistic', 'Holistic multi-indicator technical approaches', 'Technical', 7),
('Volume - Advanced', 'Advanced volume analysis strategies', 'Volume', 8),
('Price Action - Session', 'Session-based price action strategies', 'Price Action', 9),
('Smart Money - Precise', 'Precise smart money execution strategies', 'Smart Money', 10),
('Volatility - Statistical', 'Volatility-based statistical strategies', 'Volatility', 11),
('Price Action - Pattern', 'Pattern recognition strategies', 'Price Action', 12),
('Multi-Factor - Elite', 'Elite multi-factor confirmation strategies', 'Multi-Factor', 13),
('Smart Money - Structure', 'Market structure-based strategies', 'Smart Money', 14),
('Scalping - Elite', 'Professional scalping systems', 'Scalping', 15),
('Swing - Position', 'Swing and position trading systems', 'Swing', 16);

-- Create user favorite prompts table
CREATE TABLE IF NOT EXISTS user_favorite_prompts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    template_id VARCHAR(100) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES prompt_templates(template_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_template (user_id, template_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create prompt usage statistics table
CREATE TABLE IF NOT EXISTS prompt_usage_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id VARCHAR(100) NOT NULL,
    user_id INT,
    bot_id INT,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    performance_rating INT,
    notes TEXT,
    FOREIGN KEY (template_id) REFERENCES prompt_templates(template_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE SET NULL,
    INDEX idx_template_id (template_id),
    INDEX idx_user_id (user_id),
    INDEX idx_used_at (used_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


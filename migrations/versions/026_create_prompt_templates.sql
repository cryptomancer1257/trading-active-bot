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
JSON_OBJECT('tags', JSON_ARRAY('Swing', 'Position', 'Multi-Timeframe'), 'difficulty', 'Intermediate'));

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


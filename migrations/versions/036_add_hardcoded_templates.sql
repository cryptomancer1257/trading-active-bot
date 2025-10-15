-- Migration: 036_add_hardcoded_templates.sql
-- Date: 2025-10-15
-- Description: Add hardcoded frontend templates to database for API consistency

-- Insert Universal Futures Bot template
INSERT INTO bots (
    name,
    description,
    developer_id,
    category_id,
    status,
    bot_type,
    bot_mode,
    timeframe,
    timeframes,
    exchange_type,
    trading_pair,
    trading_pairs,
    strategy_config,
    price_per_month,
    is_free,
    total_subscribers,
    average_rating,
    total_reviews,
    config_schema,
    default_config,
    leverage,
    risk_percentage,
    stop_loss_percentage,
    take_profit_percentage,
    risk_config,
    risk_management_mode,
    metadata,
    llm_provider,
    enable_image_analysis,
    enable_sentiment_analysis,
    code_path,
    created_at,
    updated_at
) VALUES (
    '🌐 Universal Futures Entity',
    'Multi-exchange futures trading across 6 major platforms (Binance, Bybit, OKX, Bitget, Huobi, Kraken) with unified LLM AI analysis',
    1, -- developer_id
    1, -- category_id
    'APPROVED',
    'FUTURES',
    'ACTIVE',
    '1h',
    '["1h", "4h", "1d"]',
    'BINANCE', -- Default exchange
    'BTC/USDT',
    '["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"]',
    JSON_OBJECT(
        'llm_analysis_enabled', TRUE,
        'multi_exchange_support', TRUE,
        'unified_interface', TRUE
    ),
    0.0, -- price_per_month (free template)
    TRUE, -- is_free
    0, -- total_subscribers
    0.0, -- average_rating
    0, -- total_reviews
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'exchange', JSON_OBJECT('type', 'string', 'enum', JSON_ARRAY('BINANCE', 'BYBIT', 'OKX', 'BITGET', 'HUOBI', 'KRAKEN'), 'default', 'BINANCE'),
            'trading_pair', JSON_OBJECT('type', 'string', 'default', 'BTCUSDT'),
            'leverage', JSON_OBJECT('type', 'number', 'minimum', 1, 'maximum', 125, 'default', 10),
            'use_llm_analysis', JSON_OBJECT('type', 'boolean', 'default', TRUE),
            'llm_model', JSON_OBJECT('type', 'string', 'default', 'openai')
        )
    ),
    JSON_OBJECT(
        'exchange', 'BINANCE',
        'trading_pair', 'BTCUSDT',
        'leverage', 10,
        'use_llm_analysis', TRUE,
        'llm_model', 'openai'
    ),
    10, -- leverage
    2.0, -- risk_percentage
    5.0, -- stop_loss_percentage
    10.0, -- take_profit_percentage
    JSON_OBJECT(
        'max_leverage', 10,
        'max_position_size', 2.0,
        'stop_loss_percent', 5.0,
        'take_profit_percent', 10.0,
        'risk_per_trade_percent', 2.0
    ),
    'DEFAULT',
    JSON_OBJECT(
        'template_id', 'universal_futures_bot',
        'features', JSON_ARRAY('6 Exchanges Support', 'Multi-Exchange Portfolio', 'LLM Integration', 'Unified Interface', 'Capital Management', 'Stop Loss/Take Profit'),
        'complexity', 'Advanced',
        'gradient', 'from-blue-500 via-purple-500 to-pink-500',
        'highlighted', TRUE,
        'new', TRUE
    ),
    'openai',
    FALSE, -- enable_image_analysis
    FALSE, -- enable_sentiment_analysis
    'bot_files/universal_futures_bot.py',
    NOW(),
    NOW()
);

-- Insert Universal Spot Bot template
INSERT INTO bots (
    name,
    description,
    developer_id,
    category_id,
    status,
    bot_type,
    bot_mode,
    timeframe,
    timeframes,
    exchange_type,
    trading_pair,
    trading_pairs,
    strategy_config,
    price_per_month,
    is_free,
    total_subscribers,
    average_rating,
    total_reviews,
    config_schema,
    default_config,
    leverage,
    risk_percentage,
    stop_loss_percentage,
    take_profit_percentage,
    risk_config,
    risk_management_mode,
    metadata,
    llm_provider,
    enable_image_analysis,
    enable_sentiment_analysis,
    code_path,
    created_at,
    updated_at
) VALUES (
    '🌟 Universal Spot Entity',
    'Multi-exchange spot trading across 6 major platforms (Binance, Bybit, OKX, Bitget, Huobi, Kraken) with OCO orders and no leverage',
    1, -- developer_id
    1, -- category_id
    'APPROVED',
    'SPOT',
    'ACTIVE',
    '1h',
    '["1h", "4h", "1d"]',
    'BINANCE', -- Default exchange
    'BTC/USDT',
    '["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"]',
    JSON_OBJECT(
        'llm_analysis_enabled', TRUE,
        'oco_orders_enabled', TRUE,
        'no_leverage', TRUE
    ),
    0.0, -- price_per_month (free template)
    TRUE, -- is_free
    0, -- total_subscribers
    0.0, -- average_rating
    0, -- total_reviews
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'exchange', JSON_OBJECT('type', 'string', 'enum', JSON_ARRAY('BINANCE', 'BYBIT', 'OKX', 'BITGET', 'HUOBI', 'KRAKEN'), 'default', 'BINANCE'),
            'trading_pair', JSON_OBJECT('type', 'string', 'default', 'BTCUSDT'),
            'use_llm_analysis', JSON_OBJECT('type', 'boolean', 'default', TRUE),
            'llm_model', JSON_OBJECT('type', 'string', 'default', 'openai')
        )
    ),
    JSON_OBJECT(
        'exchange', 'BINANCE',
        'trading_pair', 'BTCUSDT',
        'use_llm_analysis', TRUE,
        'llm_model', 'openai'
    ),
    1, -- leverage (no leverage for spot)
    1.0, -- risk_percentage
    2.0, -- stop_loss_percentage
    5.0, -- take_profit_percentage
    JSON_OBJECT(
        'max_leverage', 1,
        'max_position_size', 1.0,
        'stop_loss_percent', 2.0,
        'take_profit_percent', 5.0,
        'risk_per_trade_percent', 1.0
    ),
    'DEFAULT',
    JSON_OBJECT(
        'template_id', 'universal_spot_bot',
        'features', JSON_ARRAY('6 Exchanges Support', 'No Leverage (1x)', 'OCO Orders (SL/TP)', 'LLM Integration', 'Safer than Futures', 'Multi-Timeframe Analysis'),
        'complexity', 'Intermediate',
        'gradient', 'from-emerald-500 via-teal-500 to-cyan-500',
        'highlighted', TRUE,
        'new', TRUE
    ),
    'openai',
    FALSE, -- enable_image_analysis
    FALSE, -- enable_sentiment_analysis
    'bot_files/universal_spot_bot.py',
    NOW(),
    NOW()
);

-- Insert Binance Futures Bot template
INSERT INTO bots (
    name,
    description,
    developer_id,
    category_id,
    status,
    bot_type,
    bot_mode,
    timeframe,
    timeframes,
    exchange_type,
    trading_pair,
    trading_pairs,
    strategy_config,
    price_per_month,
    is_free,
    total_subscribers,
    average_rating,
    total_reviews,
    config_schema,
    default_config,
    leverage,
    risk_percentage,
    stop_loss_percentage,
    take_profit_percentage,
    risk_config,
    risk_management_mode,
    metadata,
    llm_provider,
    enable_image_analysis,
    enable_sentiment_analysis,
    code_path,
    created_at,
    updated_at
) VALUES (
    '🚀 Futures Quantum Entity',
    'Advanced futures trading with LLM AI analysis, leverage, and quantum risk management',
    1, -- developer_id
    1, -- category_id
    'APPROVED',
    'FUTURES',
    'ACTIVE',
    '1h',
    '["15m", "1h", "4h"]',
    'BINANCE',
    'BTC/USDT',
    '["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "DOT/USDT"]',
    JSON_OBJECT(
        'llm_analysis_enabled', TRUE,
        'quantum_risk_management', TRUE,
        'advanced_futures', TRUE
    ),
    0.0, -- price_per_month (free template)
    TRUE, -- is_free
    0, -- total_subscribers
    0.0, -- average_rating
    0, -- total_reviews
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'trading_pair', JSON_OBJECT('type', 'string', 'default', 'BTCUSDT'),
            'leverage', JSON_OBJECT('type', 'number', 'minimum', 1, 'maximum', 125, 'default', 20),
            'use_llm_analysis', JSON_OBJECT('type', 'boolean', 'default', TRUE),
            'llm_model', JSON_OBJECT('type', 'string', 'default', 'openai')
        )
    ),
    JSON_OBJECT(
        'trading_pair', 'BTCUSDT',
        'leverage', 20,
        'use_llm_analysis', TRUE,
        'llm_model', 'openai'
    ),
    20, -- leverage
    3.0, -- risk_percentage
    4.0, -- stop_loss_percentage
    8.0, -- take_profit_percentage
    JSON_OBJECT(
        'max_leverage', 20,
        'max_position_size', 3.0,
        'stop_loss_percent', 4.0,
        'take_profit_percent', 8.0,
        'risk_per_trade_percent', 3.0
    ),
    'DEFAULT',
    JSON_OBJECT(
        'template_id', 'binance_futures_bot',
        'features', JSON_ARRAY('High Leverage', 'Quantum Risk Management', 'LLM AI Analysis', 'Advanced Futures', 'Binance Native', 'Real-time Signals'),
        'complexity', 'Expert',
        'gradient', 'from-orange-500 via-red-500 to-pink-500',
        'highlighted', FALSE,
        'new', FALSE
    ),
    'openai',
    FALSE, -- enable_image_analysis
    FALSE, -- enable_sentiment_analysis
    'bot_files/binance_futures_bot.py',
    NOW(),
    NOW()
);

-- Insert Binance Futures RPA Bot template
INSERT INTO bots (
    name,
    description,
    developer_id,
    category_id,
    status,
    bot_type,
    bot_mode,
    timeframe,
    timeframes,
    exchange_type,
    trading_pair,
    trading_pairs,
    strategy_config,
    price_per_month,
    is_free,
    total_subscribers,
    average_rating,
    total_reviews,
    config_schema,
    default_config,
    leverage,
    risk_percentage,
    stop_loss_percentage,
    take_profit_percentage,
    risk_config,
    risk_management_mode,
    metadata,
    llm_provider,
    enable_image_analysis,
    enable_sentiment_analysis,
    code_path,
    created_at,
    updated_at
) VALUES (
    '🤖 RPA Automation Entity',
    'Browser automation for futures trading with RPA (Robotic Process Automation) and LLM intelligence',
    1, -- developer_id
    1, -- category_id
    'APPROVED',
    'FUTURES_RPA',
    'ACTIVE',
    '1h',
    '["1h", "4h"]',
    'BINANCE',
    'BTC/USDT',
    '["BTC/USDT", "ETH/USDT", "BNB/USDT"]',
    JSON_OBJECT(
        'rpa_enabled', TRUE,
        'browser_automation', TRUE,
        'llm_analysis_enabled', TRUE
    ),
    0.0, -- price_per_month (free template)
    TRUE, -- is_free
    0, -- total_subscribers
    0.0, -- average_rating
    0, -- total_reviews
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'trading_pair', JSON_OBJECT('type', 'string', 'default', 'BTCUSDT'),
            'leverage', JSON_OBJECT('type', 'number', 'minimum', 1, 'maximum', 125, 'default', 10),
            'use_llm_analysis', JSON_OBJECT('type', 'boolean', 'default', TRUE),
            'llm_model', JSON_OBJECT('type', 'string', 'default', 'openai')
        )
    ),
    JSON_OBJECT(
        'trading_pair', 'BTCUSDT',
        'leverage', 10,
        'use_llm_analysis', TRUE,
        'llm_model', 'openai'
    ),
    10, -- leverage
    2.0, -- risk_percentage
    5.0, -- stop_loss_percentage
    10.0, -- take_profit_percentage
    JSON_OBJECT(
        'max_leverage', 10,
        'max_position_size', 2.0,
        'stop_loss_percent', 5.0,
        'take_profit_percent', 10.0,
        'risk_per_trade_percent', 2.0
    ),
    'DEFAULT',
    JSON_OBJECT(
        'template_id', 'binance_futures_rpa_bot',
        'features', JSON_ARRAY('RPA Automation', 'Browser Control', 'LLM Intelligence', 'Futures Trading', 'Visual Recognition', 'Human-like Trading'),
        'complexity', 'Expert',
        'gradient', 'from-purple-500 via-indigo-500 to-blue-500',
        'highlighted', FALSE,
        'new', FALSE
    ),
    'openai',
    TRUE, -- enable_image_analysis (for RPA)
    FALSE, -- enable_sentiment_analysis
    'bot_files/binance_futures_rpa_bot.py',
    NOW(),
    NOW()
);

-- Insert Binance Signals Bot template
INSERT INTO bots (
    name,
    description,
    developer_id,
    category_id,
    status,
    bot_type,
    bot_mode,
    timeframe,
    timeframes,
    exchange_type,
    trading_pair,
    trading_pairs,
    strategy_config,
    price_per_month,
    is_free,
    total_subscribers,
    average_rating,
    total_reviews,
    config_schema,
    default_config,
    leverage,
    risk_percentage,
    stop_loss_percentage,
    take_profit_percentage,
    risk_config,
    risk_management_mode,
    metadata,
    llm_provider,
    enable_image_analysis,
    enable_sentiment_analysis,
    code_path,
    created_at,
    updated_at
) VALUES (
    '📡 Trading Signals Entity',
    'AI-powered trading signals with Telegram notifications and LLM market analysis',
    1, -- developer_id
    1, -- category_id
    'APPROVED',
    'BACKTEST', -- Signals bot type
    'PASSIVE',
    '1h',
    '["15m", "1h", "4h"]',
    'BINANCE',
    'BTC/USDT',
    '["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"]',
    JSON_OBJECT(
        'signals_only', TRUE,
        'telegram_notifications', TRUE,
        'llm_analysis_enabled', TRUE
    ),
    0.0, -- price_per_month (free template)
    TRUE, -- is_free
    0, -- total_subscribers
    0.0, -- average_rating
    0, -- total_reviews
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'trading_pair', JSON_OBJECT('type', 'string', 'default', 'BTCUSDT'),
            'use_llm_analysis', JSON_OBJECT('type', 'boolean', 'default', TRUE),
            'llm_model', JSON_OBJECT('type', 'string', 'default', 'openai'),
            'telegram_chat_id', JSON_OBJECT('type', 'string', 'description', 'Your Telegram Chat ID for signals')
        )
    ),
    JSON_OBJECT(
        'trading_pair', 'BTCUSDT',
        'use_llm_analysis', TRUE,
        'llm_model', 'openai',
        'telegram_chat_id', ''
    ),
    1, -- leverage (not applicable for signals)
    0.0, -- risk_percentage (not applicable)
    0.0, -- stop_loss_percentage (not applicable)
    0.0, -- take_profit_percentage (not applicable)
    JSON_OBJECT(),
    'NONE',
    JSON_OBJECT(
        'template_id', 'binance_signals_bot',
        'features', JSON_ARRAY('Trading Signals', 'Telegram Alerts', 'LLM Analysis', 'No Trading', 'Market Insights', 'Real-time Notifications'),
        'complexity', 'Beginner',
        'gradient', 'from-green-500 via-teal-500 to-blue-500',
        'highlighted', FALSE,
        'new', FALSE
    ),
    'openai',
    FALSE, -- enable_image_analysis
    TRUE, -- enable_sentiment_analysis
    'bot_files/binance_signals_bot.py',
    NOW(),
    NOW()
);

-- Get the inserted bot IDs for reference
SELECT 
    id,
    name,
    JSON_EXTRACT(metadata, '$.template_id') as template_id,
    bot_type,
    status
FROM bots 
WHERE JSON_EXTRACT(metadata, '$.template_id') IN (
    'universal_futures_bot',
    'universal_spot_bot', 
    'binance_futures_bot',
    'binance_futures_rpa_bot',
    'binance_signals_bot'
)
ORDER BY created_at DESC;

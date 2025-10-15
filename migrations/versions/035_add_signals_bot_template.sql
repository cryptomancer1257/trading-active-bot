-- Add Universal Futures Signals Bot Template
-- Migration: 035_add_signals_bot_template.sql
-- Date: 2025-10-15

-- Insert bot template for signals bot
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
    price_per_month,
    is_free,
    leverage,
    risk_percentage,
    stop_loss_percentage,
    take_profit_percentage,
    risk_config,
    metadata,
    llm_provider,
    enable_image_analysis,
    enable_sentiment_analysis,
    created_at,
    updated_at
) VALUES (
    'Universal Futures Signals Bot',
    'AI-powered trading signals bot with multi-timeframe analysis. Sends BUY/SELL signals via Telegram and Discord. Supports Binance, Bybit, OKX, Bitget, Huobi, and Kraken exchanges. Uses LLM (OpenAI/Claude/Gemini) for intelligent market analysis. NO ACTUAL TRADING - Signals only for manual trading.',
    1, -- developer_id (replace with actual developer ID)
    1, -- category_id (replace with actual category ID, e.g., "Signals/Alerts")
    'APPROVED', -- status must be PENDING/APPROVED/REJECTED/ARCHIVED
    'BACKTEST', -- bot_type (signals bot, not for live trading)
    'multi_timeframe',
    '1h',
    '["30m", "1h", "4h"]',
    'BINANCE', -- Default exchange (user can change)
    'BTC/USDT',
    '["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]',
    0.00, -- Free bot (or set price)
    TRUE,
    1, -- No leverage (signals only)
    0, -- No risk percentage (signals only)
    0, -- No stop loss (signals only)
    0, -- No take profit (signals only)
    JSON_OBJECT(
        'max_leverage', 1,
        'max_position_size', 0,
        'stop_loss_percent', 0,
        'take_profit_percent', 0,
        'max_daily_trades', 0,
        'max_open_positions', 0,
        'trailing_stop_enabled', false,
        'risk_per_trade_percent', 0
    ),
    JSON_OBJECT(
        'bot_file', 'universal_futures_signals_bot.py',
        'bot_class', 'UniversalFuturesSignalsBot',
        'supported_exchanges', JSON_ARRAY('BINANCE', 'BYBIT', 'OKX', 'BITGET', 'HUOBI', 'KRAKEN'),
        'notification_channels', JSON_ARRAY('telegram', 'discord'),
        'features', JSON_ARRAY(
            'LLM AI Analysis',
            'Multi-timeframe Analysis',
            'Telegram Notifications',
            'Discord Notifications',
            'Technical Analysis Fallback',
            'No Trading Execution',
            'Public API Only (No Credentials Needed)',
            'Redis Caching',
            'Multi-exchange Support'
        ),
        'requirements', JSON_OBJECT(
            'telegram_bot_token', 'Required (from @BotFather)',
            'discord_webhook_url', 'Optional (from Discord Server Settings)',
            'telegram_chat_id', 'Required (User chat ID)',
            'exchange_api_keys', 'Not Required (Public API only)',
            'llm_api_keys', 'Optional (Uses developer BYOK if configured)'
        ),
        'signal_types', JSON_ARRAY('BUY', 'SELL', 'HOLD'),
        'analysis_methods', JSON_ARRAY('LLM (OpenAI/Claude/Gemini)', 'RSI', 'MACD', 'SMA', 'ATR'),
        'example_config', JSON_OBJECT(
            'exchange', 'BINANCE',
            'trading_pair', 'BTCUSDT',
            'timeframes', JSON_ARRAY('30m', '1h', '4h'),
            'primary_timeframe', '1h',
            'use_llm_analysis', true,
            'llm_provider', 'openai',
            'notification_config', JSON_OBJECT(
                'telegram', JSON_OBJECT('enabled', true),
                'discord', JSON_OBJECT('enabled', true)
            )
        )
    ),
    'openai', -- Default LLM provider
    FALSE, -- No image analysis
    FALSE, -- No sentiment analysis
    NOW(),
    NOW()
);

-- Get the bot_id for reference and display success message
SET @signals_bot_id = LAST_INSERT_ID();

SELECT 
    @signals_bot_id AS bot_id,
    'Universal Futures Signals Bot' AS bot_name,
    '✅ Signals Bot Template Created Successfully!' AS status;


from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum

# Enums for API responses
class UserRole(str, Enum):
    USER = "USER"
    DEVELOPER = "DEVELOPER"
    ADMIN = "ADMIN"

class BotStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

class BotType(str, Enum):
    TECHNICAL = "TECHNICAL"  # Traditional technical analysis
    ML = "ML"               # Machine Learning
    DL = "DL"               # Deep Learning
    LLM = "LLM"             # Large Language Model
    SPOT = "SPOT"           # Spot Trading
    FUTURES = "FUTURES"     # Futures Trading
    FUTURES_RPA = "FUTURES_RPA"  # Futures Trading with RPA
    FUTURES_API = "FUTURES_API"  # temp

class BotMode(str, Enum):
    PASSIVE = "PASSIVE"
    ACTIVE = "ACTIVE"

class FileType(str, Enum):
    CODE = "CODE"
    MODEL = "MODEL"
    WEIGHTS = "WEIGHTS"
    CONFIG = "CONFIG"
    DATA = "DATA"

class ExchangeType(str, Enum):
    MULTI = "MULTI"  # Multi-exchange support (Universal Bot)
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
    OKX = "OKX"
    BITGET = "BITGET"
    HUOBI = "HUOBI"
    KRAKEN = "KRAKEN"

class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    ERROR = "ERROR"

class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class NetworkType(str, Enum):
    TESTNET = "TESTNET"
    MAINNET = "MAINNET"

class TradeMode(str, Enum):
    SPOT = "Spot"
    MARGIN = "Margin"
    FUTURES = "Futures"

class CredentialType(str, Enum):
    SPOT = "SPOT"
    FUTURES = "FUTURES"
    MARGIN = "MARGIN"

class UserPrincipalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.USER
    is_active: bool = True
    developer_name: Optional[str] = None
    developer_bio: Optional[str] = None
    developer_website: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER
    developer_name: Optional[str] = None
    developer_bio: Optional[str] = None
    developer_website: Optional[str] = None

class UserUpdate(BaseModel):
    developer_name: Optional[str] = None
    developer_bio: Optional[str] = None
    developer_website: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True  # Serialize enums as their values

class UserProfile(UserInDB):
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    total_developed_bots: int = 0
    approved_bots: int = 0

# --- User Principal Schemas ---
class UserPrincipalBase(BaseModel):
    principal_id: str = Field(..., description="ICP Principal ID")
    status: UserPrincipalStatus = UserPrincipalStatus.ACTIVE

class UserPrincipalCreate(BaseModel):
    principal_id: str = Field(..., description="ICP Principal ID")
    
    @validator('principal_id')
    def validate_principal_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Principal ID cannot be empty')
        # Add more validation if needed (e.g., format check)
        return v.strip()

class UserPrincipalUpdate(BaseModel):
    status: Optional[UserPrincipalStatus] = None

class UserPrincipalInDB(UserPrincipalBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserPrincipalResponse(UserPrincipalInDB):
    pass

# --- Exchange Credentials Schemas (End Users) ---
class ExchangeCredentialsBase(BaseModel):
    exchange: ExchangeType
    api_key: str
    api_secret: str
    api_passphrase: Optional[str] = None  # For Coinbase
    is_testnet: bool = True  # Default to testnet for safety

class ExchangeCredentialsCreate(ExchangeCredentialsBase):
    pass

class ExchangeCredentialsUpdate(BaseModel):
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    api_passphrase: Optional[str] = None
    is_testnet: Optional[bool] = None
    is_active: Optional[bool] = None

class ExchangeCredentialsInDB(ExchangeCredentialsBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_validated: Optional[datetime] = None
    validation_status: str
    
    class Config:
        from_attributes = True

class ExchangeCredentialsPublic(BaseModel):
    """Public view without sensitive data"""
    id: int
    exchange: ExchangeType
    is_testnet: bool
    is_active: bool
    validation_status: str
    last_validated: Optional[datetime] = None
    api_key_preview: str  # Only show first 8 characters
    
    class Config:
        from_attributes = True

class ExchangeCredentialsValidation(BaseModel):
    """Response for credential validation"""
    valid: bool
    message: str
    exchange: ExchangeType
    is_testnet: bool

# === Marketplace user settings (for marketplace Settings page) ===
class MarketplaceUserSettings(BaseModel):
    principal_id: str = Field(..., description="ICP Principal ID (unique)")
    email: Optional[str] = None
    social_telegram: Optional[str] = None
    social_discord: Optional[str] = None
    social_twitter: Optional[str] = None
    social_whatsapp: Optional[str] = None
    default_channel: Optional[str] = "email"
    display_dark_mode: Optional[bool] = False
    display_currency: Optional[str] = "ICP"
    display_language: Optional[str] = "en"
    display_timezone: Optional[str] = "UTC"

    @validator('principal_id')
    def validate_settings_principal_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Principal ID cannot be empty')
        return v.strip()

    @validator('social_telegram', 'social_discord', 'social_twitter', 'social_whatsapp', pre=True)
    def remove_at_prefix(cls, v):
        if v and isinstance(v, str) and v.startswith('@'):
            return v[1:]
        return v

class MarketplaceUserSettingsInDB(MarketplaceUserSettings):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Payload version (without principal_id) for nested usage in bulk endpoint
class MarketplaceUserSettingsPayload(BaseModel):
    email: Optional[str] = None
    social_telegram: Optional[str] = None
    social_discord: Optional[str] = None
    social_twitter: Optional[str] = None
    social_whatsapp: Optional[str] = None
    default_channel: Optional[str] = "email"
    display_dark_mode: Optional[bool] = False
    display_currency: Optional[str] = "ICP"
    display_language: Optional[str] = "en"
    display_timezone: Optional[str] = "UTC"

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Bot Category Schemas ---
class BotCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class BotCategoryCreate(BotCategoryBase):
    pass

class BotCategoryInDB(BotCategoryBase):
    id: int
    
    class Config:
        from_attributes = True

# --- Bot Schemas ---
class BotBase(BaseModel):
    name: str
    description: str
    category_id: Optional[int] = None
    version: str = "1.0.0"
    bot_type: BotType = BotType.TECHNICAL
    price_per_month: Decimal = Decimal('0.00')
    is_free: bool = True
    config_schema: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    model_metadata: Optional[Dict[str, Any]] = None
    timeframes: Optional[List[str]] = None
    timeframe: Optional[str] = None
    bot_mode: Optional[BotMode] = None
    trading_pair: Optional[str] = None
    exchange_type: Optional[ExchangeType] = None
    strategy_config: Optional[Any] = None
    image_url: Optional[str] = None
    code_path_rpa: Optional[str] = None
    version_rpa: Optional[str] = None
    
    # Template-related fields (legacy - kept for backward compatibility)
    template: Optional[str] = None
    templateFile: Optional[str] = None
    leverage: Optional[int] = None
    risk_percentage: Optional[float] = None
    stop_loss_percentage: Optional[float] = None
    take_profit_percentage: Optional[float] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None  # Specific model to use (e.g., "claude-3-5-sonnet-20241022")
    enable_image_analysis: Optional[bool] = False
    enable_sentiment_analysis: Optional[bool] = False
    
    # Risk Management (new system)
    risk_config: Optional[Dict[str, Any]] = None
    risk_management_mode: Optional[str] = None

class PayLoadAnalysis(BaseModel):
    bot_name: str = ""
    trading_pair: str
    primary_timeframe: str
    timeframes: List[str]
    strategies: List[str]

    @validator('timeframes', pre=True, always=True)
    def remove_primary_from_timeframes(cls, v, values):
        primary = values.get('primary_timeframe')
        if primary and v:
            return [tf for tf in v if tf != primary]
        return v

class BotCreate(BotBase):
    pass

class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    version: Optional[str] = None
    bot_type: Optional[BotType] = None
    price_per_month: Optional[Decimal] = None
    is_free: Optional[bool] = None
    config_schema: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    model_metadata: Optional[Dict[str, Any]] = None
    timeframes: Optional[List[str]] = None
    timeframe: Optional[str] = None
    bot_mode: Optional[BotMode] = None
    trading_pair: Optional[str] = None
    exchange_type: Optional[ExchangeType] = None
    strategy_config: Optional[Any] = None
    image_url: Optional[str] = None
    
    # Advanced configuration fields
    leverage: Optional[int] = None
    risk_percentage: Optional[float] = None
    stop_loss_percentage: Optional[float] = None
    take_profit_percentage: Optional[float] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None  # Specific model to use (e.g., "claude-3-5-sonnet-20241022")
    enable_image_analysis: Optional[bool] = None
    enable_sentiment_analysis: Optional[bool] = None
    prompt_template_id: Optional[int] = None

class BotInDB(BotBase):
    id: int
    developer_id: int
    status: BotStatus
    code_path: Optional[str] = None
    model_path: Optional[str] = None
    total_subscribers: int = 0
    subscribers_count: int = 0  # Real-time count from subscriptions
    transactions_count: int = 0  # Total transactions count
    average_rating: float = 0.0
    total_reviews: int = 0
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    
    class Config:
        from_attributes = True

class BotPublic(BaseModel):
    id: int
    name: str
    description: str
    developer_id: int
    category_id: Optional[int] = None
    version: str
    bot_type: Optional[str] = None
    code_path: Optional[str] = None
    price_per_month: Decimal
    is_free: bool
    total_subscribers: int
    average_rating: float
    total_reviews: int
    default_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class BotWithDeveloper(BotPublic):
    developer: UserInDB

# --- Bot File Schemas ---
class BotFileBase(BaseModel):
    file_type: FileType
    file_name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    model_framework: Optional[str] = None
    model_type: Optional[str] = None
    input_shape: Optional[Dict[str, Any]] = None
    output_shape: Optional[Dict[str, Any]] = None

class BotFileCreate(BotFileBase):
    bot_id: int

class BotFileInDB(BotFileBase):
    id: int
    bot_id: int
    file_path: str
    file_size: int
    file_hash: str
    upload_date: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class BotFileUpload(BaseModel):
    file_type: FileType
    description: Optional[str] = None
    model_framework: Optional[str] = None
    model_type: Optional[str] = None

class MLModelInfo(BaseModel):
    framework: str  # tensorflow, pytorch, sklearn, etc.
    model_type: str  # classification, regression, etc.
    input_features: List[str]
    output_format: Dict[str, Any]
    requirements: List[str]  # Python packages needed
    preprocessing_steps: Optional[List[str]] = None

# --- Binance Account Schemas ---
class BinanceAccount(BaseModel):
    account_type: str
    can_trade: bool
    can_withdraw: bool
    can_deposit: bool
    update_time: datetime
    balances: List[Dict[str, str]]
    permissions: List[str]

class BinanceBalance(BaseModel):
    asset: str
    free: str
    locked: str

class BinanceOrder(BaseModel):
    symbol: str
    order_id: int
    client_order_id: str
    price: str
    orig_qty: str
    executed_qty: str
    status: str
    side: str
    type: str
    time_in_force: str

class CreateOrderRequest(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    type: str  # MARKET, LIMIT, etc.
    quantity: Optional[str] = None
    price: Optional[str] = None
    time_in_force: Optional[str] = "GTC"

# --- Bot Review Schemas ---
class BotReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None

class BotReviewCreate(BotReviewBase):
    bot_id: int

class BotReviewInDB(BotReviewBase):
    id: int
    user_id: int
    bot_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        
class BotReviewWithUser(BotReviewInDB):
    user: UserInDB

# --- Subscription Schemas ---
class ExecutionConfig(BaseModel):
    buy_order_type: str = Field(..., pattern="^(PERCENTAGE|USDT_AMOUNT)$")
    buy_order_value: float = Field(..., gt=0)
    sell_order_type: str = Field(..., pattern="^(PERCENTAGE|ALL)$")
    sell_order_value: float = Field(..., gt=0)

class RiskManagementMode(str, Enum):
    """Risk management mode"""
    DEFAULT = "DEFAULT"  # Human-configured rules
    AI_PROMPT = "AI_PROMPT"  # LLM-based dynamic risk management

class TrailingStopConfig(BaseModel):
    """Trailing stop loss configuration"""
    enabled: bool = False
    activation_percent: Optional[float] = Field(None, gt=0, description="Profit % to activate trailing")
    trailing_percent: Optional[float] = Field(None, gt=0, description="Distance from peak to trail")

class TradingWindowConfig(BaseModel):
    """Trading time window configuration"""
    enabled: bool = False
    start_hour: Optional[int] = Field(None, ge=0, le=23, description="Trading start hour (UTC)")
    end_hour: Optional[int] = Field(None, ge=0, le=23, description="Trading end hour (UTC)")
    days_of_week: Optional[List[int]] = Field(None, description="Days allowed (0=Monday, 6=Sunday)")

class CooldownConfig(BaseModel):
    """Cooldown after loss configuration"""
    enabled: bool = False
    cooldown_minutes: Optional[int] = Field(None, gt=0, description="Minutes to wait after loss")
    trigger_loss_count: Optional[int] = Field(None, gt=0, description="Number of consecutive losses to trigger")

class RiskConfig(BaseModel):
    """Enhanced risk configuration supporting DEFAULT and AI modes"""
    
    # Mode selection
    mode: RiskManagementMode = Field(default=RiskManagementMode.DEFAULT, description="Risk management mode")
    
    # === DEFAULT MODE: Manual Configuration ===
    
    # Basic Risk Parameters (Legacy support)
    stop_loss_percent: Optional[float] = Field(None, gt=0, le=100, description="Stop loss %")
    take_profit_percent: Optional[float] = Field(None, gt=0, description="Take profit %")
    max_position_size: Optional[float] = Field(None, gt=0, description="Max position size %")
    
    # Advanced Risk Parameters
    min_risk_reward_ratio: Optional[float] = Field(None, gt=0, description="Minimum RR ratio (e.g., 2 means 2:1)")
    risk_per_trade_percent: Optional[float] = Field(None, gt=0, le=100, description="Risk % per trade")
    max_leverage: Optional[int] = Field(None, gt=1, le=125, description="Maximum leverage allowed")
    max_portfolio_exposure: Optional[float] = Field(None, gt=0, le=100, description="Max total exposure %")
    daily_loss_limit_percent: Optional[float] = Field(None, gt=0, le=100, description="Daily loss limit %")
    
    # Trailing Stop Configuration
    trailing_stop: Optional[TrailingStopConfig] = Field(default=None, description="Trailing stop settings")
    
    # Trading Window
    trading_window: Optional[TradingWindowConfig] = Field(default=None, description="Trading time restrictions")
    
    # Cooldown Rules
    cooldown: Optional[CooldownConfig] = Field(default=None, description="Cooldown after losses")
    
    # === AI MODE: Prompt-based Dynamic Risk Management ===
    
    ai_prompt_id: Optional[int] = Field(None, description="ID of AI risk management prompt template")
    ai_prompt_custom: Optional[str] = Field(None, description="Custom AI prompt for risk analysis")
    ai_update_frequency_minutes: Optional[int] = Field(default=15, gt=0, description="How often to consult AI")
    
    # Hybrid: AI can override defaults within these bounds
    ai_allow_override: bool = Field(default=False, description="Allow AI to override default rules")
    ai_min_stop_loss: Optional[float] = Field(None, gt=0, description="AI cannot set SL below this")
    ai_max_stop_loss: Optional[float] = Field(None, gt=0, description="AI cannot set SL above this")
    ai_min_take_profit: Optional[float] = Field(None, gt=0, description="AI cannot set TP below this")
    ai_max_take_profit: Optional[float] = Field(None, gt=0, description="AI cannot set TP above this")
    
    class Config:
        use_enum_values = True

class SubscriptionBase(BaseModel):
    instance_name: str
    bot_id: int
    exchange_type: ExchangeType = ExchangeType.BINANCE
    trading_pair: str
    timeframe: str = Field(..., pattern="^(1m|5m|15m|1h|2h|4h|6h|8h|12h|1d|1w)$")
    strategy_config: Dict[str, Any] = {}
    execution_config: ExecutionConfig
    risk_config: RiskConfig
    is_testnet: bool = False  # Whether to run on testnet
    is_trial: bool = False    # Whether this is a trial subscription

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionTrialCreate(BaseModel):
    """Schema for creating a trial subscription with simplified setup"""
    instance_name: str
    bot_id: int
    exchange_type: ExchangeType = ExchangeType.BINANCE
    trading_pair: str = "BTC/USDT"
    timeframe: str = "1h"
    trial_duration_hours: float = Field(default=24.0, ge=0.1, le=168.0)  # 0.1 hours (6 minutes) to 1 week

class MarketplaceSubscriptionCreate(BaseModel):
    """Schema for creating subscription from marketplace with user principal ID"""
    user_principal_id: str = Field(..., description="ICP Principal ID of user from marketplace")
    bot_api_key: str = Field(..., description="API key of the registered bot")
    instance_name: str
    bot_id: int
    exchange_type: ExchangeType = ExchangeType.BINANCE
    trading_pair: str = "BTCUSDT"
    timeframe: str = "1h"
    is_testnet: bool = True  # Default to testnet for safety
    
    # Marketplace controls subscription timing
    start_time: Optional[datetime] = Field(None, description="When subscription should start (UTC). If None, starts immediately")
    end_time: Optional[datetime] = Field(None, description="When subscription should end (UTC). If None, no expiration")
    
    strategy_config: Dict[str, Any] = {}
    execution_config: ExecutionConfig = Field(default_factory=lambda: ExecutionConfig(
        buy_order_type="PERCENTAGE",
        buy_order_value=100.0,
        sell_order_type="ALL", 
        sell_order_value=100.0
    ))
    risk_config: RiskConfig = Field(default_factory=lambda: RiskConfig(
        stop_loss_percent=2.0,
        take_profit_percent=4.0,
        max_position_size=100.0
    ))

class MarketplaceSubscriptionCreateV2(BaseModel):
    """Schema for creating subscription from marketplace (v2 - with contact info)"""
    # Required fields
    user_principal_id: str = Field(..., description="ICP Principal ID of marketplace user")
    bot_id: int = Field(..., description="ID of bot to subscribe to")
    user_id: Optional[int] = Field(None, description="Studio user ID for trial subscriptions")
    # instance_name: Optional[str] = Field(None, description="User's custom name for this bot instance")
    # Subscription timing - REQUIRED
    subscription_start: datetime = Field(..., description="When subscription starts (UTC) - REQUIRED")
    subscription_end: datetime = Field(..., description="When subscription ends (UTC) - REQUIRED")
    
    # Trading configuration
    is_testnet: bool = True
    trading_pair: Optional[str] = Field(None, description="Trading pair like BTC/USDT")
    trading_network: Optional[str] = Field(None, description="Trading network like MAINNET, TESTNET")
    payment_method:  Optional[str] = None
    paypal_payment_id: Optional[str] = None

    # Optional configurations with defaults
    execution_config: Optional[ExecutionConfig] = None
    risk_config: Optional[RiskConfig] = None
    notify_default_method: Optional[str] = "email"  # Default notification method (email, telegram, etc.)
    
    @validator('user_principal_id')
    def validate_principal_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Principal ID cannot be empty')
        return v.strip()

class MarketplaceSubscriptionResponse(BaseModel):
    """Response for marketplace subscription creation"""
    subscription_id: int
    user_principal_id: str
    bot_id: int
    instance_name: str
    status: SubscriptionStatus
    is_marketplace_subscription: bool
    started_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class SubscriptionUpdate(BaseModel):
    subscription_id: Optional[int] = None
    instance_name: Optional[str] = None
    exchange_type: Optional[ExchangeType] = None
    trading_pair: Optional[str] = None
    timeframe: Optional[str] = None
    strategy_config: Optional[Dict[str, Any]] = None
    execution_config: Optional[ExecutionConfig] = None
    risk_config: Optional[RiskConfig] = None
    is_testnet: Optional[bool] = None
    principal_id: Optional[str] = None
    api_key: Optional[str] = None

class SubscriptionInDB(SubscriptionBase):
    id: int
    user_id: Optional[int]  # Can be None for marketplace subscriptions
    status: SubscriptionStatus
    started_at: datetime
    expires_at: Optional[datetime] = None
    trial_expires_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    total_trades: int = 0
    winning_trades: int = 0
    total_pnl: Decimal = Decimal('0.0')
    
    class Config:
        from_attributes = True

class SubscriptionWithBot(SubscriptionInDB):
    bot: BotInDB

class SubscriptionResponse(BaseModel):
    subscription_id: int
    status: str
    message: str

# --- Trade Schemas ---
class TradeBase(BaseModel):
    side: str = Field(..., pattern="^(BUY|SELL)$")
    entry_price: Decimal
    quantity: Decimal
    stop_loss_price: Optional[Decimal] = None
    take_profit_price: Optional[Decimal] = None

class TradeCreate(TradeBase):
    subscription_id: int

class TradeInDB(TradeBase):
    id: int
    subscription_id: int
    status: TradeStatus
    exit_price: Optional[Decimal] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    pnl: Optional[Decimal] = None
    pnl_percentage: Optional[float] = None
    exchange_order_id: Optional[str] = None
    exchange_trade_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class TradeWithSubscription(TradeInDB):
    subscription: SubscriptionInDB

# --- Performance Schemas ---
class PerformanceMetrics(BaseModel):
    total_trades: int = 0
    winning_trades: int = 0
    win_rate: float = 0.0
    average_pnl: Decimal = Decimal('0.0')
    total_pnl: Decimal = Decimal('0.0')
    max_drawdown: float = 0.0
    sharpe_ratio: Optional[float] = None

class BotPerformanceInDB(PerformanceMetrics):
    id: int
    bot_id: int
    period_start: datetime
    period_end: datetime
    total_subscribers: int = 0
    active_subscribers: int = 0
    
    class Config:
        from_attributes = True

class PerformanceLogBase(BaseModel):
    action: str = Field(..., pattern="^(BUY|SELL|HOLD|STOP_LOSS|TAKE_PROFIT)$")
    price: Decimal
    quantity: Decimal
    balance: Decimal
    signal_data: Optional[Dict[str, Any]] = None

class PerformanceLogCreate(PerformanceLogBase):
    subscription_id: int

class PerformanceLogInDB(PerformanceLogBase):
    id: int
    subscription_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

# --- Exchange Schemas ---
class ExchangeCredentials(BaseModel):
    exchange_name: str = Field(..., description="Exchange name (BINANCE, COINBASE, etc.)")
    api_key: str = Field(..., description="Exchange API key")
    api_secret: str = Field(..., description="Exchange API secret")
    testnet: bool = Field(default=True, description="Use testnet/sandbox environment")

class ExchangeValidationResponse(BaseModel):
    valid: bool
    message: str
    exchange: str
    testnet: bool
    account_info: Optional[Dict[str, Any]] = None

# --- Payment Schemas ---
class PaymentBase(BaseModel):
    amount: Decimal
    currency: str = "USD"
    payment_method: str
    payment_provider: str = "STRIPE"

class PaymentCreate(PaymentBase):
    subscription_id: int

class PaymentInDB(PaymentBase):
    id: int
    user_id: int
    subscription_id: int
    payment_status: str
    external_payment_id: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# --- Response Schemas ---
class BotListResponse(BaseModel):
    bots: List[BotPublic]
    total: int
    page: int
    per_page: int

class SubscriptionListResponse(BaseModel):
    subscriptions: List[SubscriptionWithBot]
    total: int
    page: int
    per_page: int

class TradeListResponse(BaseModel):
    trades: List[TradeInDB]
    total: int
    page: int
    per_page: int

class PerformanceResponse(BaseModel):
    performance: PerformanceMetrics
    recent_trades: List[TradeInDB]
    logs: List[PerformanceLogInDB]

# --- Error Schemas ---
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

# --- Admin Schemas ---
class AdminBotApproval(BaseModel):
    bot_id: int
    status: BotStatus
    approval_notes: Optional[str] = None

class AdminUserUpdate(BaseModel):
    user_id: int
    is_active: bool
    role: Optional[UserRole] = None

class AdminStats(BaseModel):
    total_users: int
    total_developers: int
    total_bots: int
    approved_bots: int
    pending_bots: int
    total_subscriptions: int
    active_subscriptions: int
    total_trades: int
    total_revenue: Decimal

# --- Pricing Plan Schemas ---
class PricingPlanBase(BaseModel):
    plan_name: str
    plan_description: str
    price_per_month: Decimal
    price_per_year: Optional[Decimal] = None
    price_per_quarter: Optional[Decimal] = None
    max_trading_pairs: int = 1
    max_daily_trades: int = 10
    max_position_size: Decimal = Decimal('0.10')
    advanced_features: Optional[Dict[str, Any]] = None
    trial_days: int = 0
    trial_trades_limit: int = 5
    is_popular: bool = False

class PricingPlanCreate(PricingPlanBase):
    pass

class PricingPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    plan_description: Optional[str] = None
    price_per_month: Optional[Decimal] = None
    price_per_year: Optional[Decimal] = None
    price_per_quarter: Optional[Decimal] = None
    max_trading_pairs: Optional[int] = None
    max_daily_trades: Optional[int] = None
    max_position_size: Optional[Decimal] = None
    advanced_features: Optional[Dict[str, Any]] = None
    trial_days: Optional[int] = None
    trial_trades_limit: Optional[int] = None
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None

class PricingPlanInDB(PricingPlanBase):
    id: int
    bot_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# --- Promotion Schemas ---
class PromotionBase(BaseModel):
    promotion_code: str
    promotion_name: str
    promotion_description: str
    discount_type: str  # "PERCENTAGE", "FIXED_AMOUNT", "FREE_TRIAL"
    discount_value: Decimal
    max_uses: int = 100
    valid_from: datetime
    valid_until: datetime
    min_subscription_months: int = 1
    applicable_plans: Optional[List[int]] = None

class PromotionCreate(PromotionBase):
    pass

class PromotionUpdate(BaseModel):
    promotion_name: Optional[str] = None
    promotion_description: Optional[str] = None
    discount_value: Optional[Decimal] = None
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    min_subscription_months: Optional[int] = None
    applicable_plans: Optional[List[int]] = None
    is_active: Optional[bool] = None

class PromotionInDB(PromotionBase):
    id: int
    bot_id: int
    used_count: int
    is_active: bool
    created_at: datetime
    created_by: int
    
    class Config:
        from_attributes = True

# --- Invoice Schemas ---
class InvoiceBase(BaseModel):
    amount: Decimal
    currency: str = "USD"
    base_price: Decimal
    discount_amount: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    final_amount: Decimal
    billing_period_start: datetime
    billing_period_end: datetime
    payment_method: Optional[str] = None
    promotion_code: Optional[str] = None
    promotion_discount: Decimal = Decimal('0.00')

class InvoiceCreate(InvoiceBase):
    subscription_id: int
    user_id: int

class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    payment_date: Optional[datetime] = None
    payment_method: Optional[str] = None

class InvoiceInDB(InvoiceBase):
    id: int
    subscription_id: int
    user_id: int
    invoice_number: str
    status: str
    payment_date: Optional[datetime] = None
    created_at: datetime
    due_date: datetime
    
    class Config:
        from_attributes = True

# --- Enhanced Bot Schemas ---
class BotWithPricing(BotPublic):
    pricing_plans: List[PricingPlanInDB] = []
    active_promotions: List[PromotionInDB] = []
    
    class Config:
        from_attributes = True

# --- Bot Registration Schemas for Marketplace ---
class BotRegistrationRequest(BaseModel):
    """Schema for marketplace bot registration request"""
    user_principal_id: str = Field(..., description="Principal ID của ICP user")
    bot_id: int = Field(..., description="ID của bot đã được approve")
    symbol: str = Field(..., description="Trading pair như ETH/USDT, BTC/USDT")
    timeframes: List[str] = Field(..., description="Danh sách timeframes như ['1h', '2h', '4h']")
    trade_evaluation_period: int = Field(..., gt=0, description="Thời gian quan sát và phân tích (phút)")
    starttime: datetime = Field(..., description="Thời gian bắt đầu cho thuê")
    endtime: datetime = Field(..., description="Thời gian kết thúc cho thuê")
    exchange_name: ExchangeType = Field(..., description="Sàn giao dịch")
    network_type: NetworkType = Field(..., description="Testnet hoặc mainnet")
    trade_mode: TradeMode = Field(..., description="Chế độ giao dịch")

    @validator('timeframes')
    def validate_timeframes(cls, v):
        valid_timeframes = ['1m', '5m', '15m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '1w']
        for tf in v:
            if tf not in valid_timeframes:
                raise ValueError(f'Invalid timeframe: {tf}. Must be one of {valid_timeframes}')
        return v

    @validator('symbol')
    def validate_symbol(cls, v):
        if '/' not in v or len(v.split('/')) != 2:
            raise ValueError('Symbol must be in format BASE/QUOTE (e.g., BTC/USDT)')
        return v.upper()

class BotMarketplaceRegistrationRequest(BaseModel):
    """Request schema for registering bot on marketplace"""
    user_principal_id: str = Field(..., description="ICP Principal ID của developer")
    bot_id: int = Field(..., description="ID của bot cần đăng ký")
    marketplace_name: Optional[str] = Field(None, description="Tên hiển thị trên marketplace")
    marketplace_description: Optional[str] = Field(None, description="Mô tả trên marketplace") 
    price_on_marketplace: Optional[Decimal] = Field(None, description="Giá bán trên marketplace")
    
    @validator('user_principal_id')
    def validate_principal_id(cls, v):
        # Validate ICP Principal ID format
        if not v or len(v) < 20:
            raise ValueError('Invalid ICP Principal ID format')
        return v

class BotMarketplaceRegistrationResponse(BaseModel):
    """Response for bot marketplace registration"""
    registration_id: int
    user_principal_id: str
    bot_id: int
    api_key: str
    status: str
    message: str
    registration_details: Dict[str, Any]

class BotMarketplaceRegistrationInDB(BaseModel):
    """Bot registration in database"""
    id: int
    user_principal_id: str
    bot_id: int
    api_key: str
    status: str  # Will be BotRegistrationStatus enum value
    marketplace_name: Optional[str]
    marketplace_description: Optional[str]
    price_on_marketplace: Optional[Decimal]
    commission_rate: float
    registered_at: datetime
    is_featured: bool
    is_active: bool
    
    class Config:
        from_attributes = True

# Legacy schema - keeping for backward compatibility
class BotRegistrationResponse(BaseModel):
    """Response for bot registration"""
    subscription_id: int
    user_principal_id: str
    bot_id: int
    status: str
    message: str
    registration_details: Dict[str, Any]

class BotRegistrationUpdate(BaseModel):
    """Schema for updating bot registration"""
    timeframes: Optional[List[str]] = Field(None, description="Cập nhật timeframes")
    trade_evaluation_period: Optional[int] = Field(None, gt=0, description="Cập nhật thời gian quan sát")
    starttime: Optional[datetime] = Field(None, description="Cập nhật thời gian bắt đầu")
    endtime: Optional[datetime] = Field(None, description="Cập nhật thời gian kết thúc")
    exchange_name: Optional[ExchangeType] = Field(None, description="Cập nhật sàn giao dịch")
    network_type: Optional[NetworkType] = Field(None, description="Cập nhật network type")
    trade_mode: Optional[TradeMode] = Field(None, description="Cập nhật chế độ giao dịch")

    @validator('timeframes')
    def validate_timeframes(cls, v):
        if v is not None:
            valid_timeframes = ['1m', '5m', '15m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '1w']
            for tf in v:
                if tf not in valid_timeframes:
                    raise ValueError(f'Invalid timeframe: {tf}. Must be one of {valid_timeframes}')
        return v

class BotRegistrationUpdateResponse(BaseModel):
    """Response for bot registration update"""
    subscription_id: int
    user_principal_id: str
    status: str
    message: str
    updated_fields: List[str]

# --- Subscription with Pricing ---
class SubscriptionWithPricing(SubscriptionResponse):
    pricing_plan: Optional[PricingPlanInDB] = None
    next_billing_date: Optional[datetime] = None
    billing_cycle: str = "MONTHLY"
    auto_renew: bool = True
    
    class Config:
        from_attributes = True

# Exchange Credentials by Principal ID (for marketplace)
class ExchangeCredentialsByPrincipalRequest(BaseModel):
    """Request model for storing exchange credentials by principal ID"""
    principal_id: str = Field(..., description="ICP Principal ID")
    exchange: ExchangeType = Field(..., description="Exchange name")
    api_key: str = Field(..., description="Exchange API key")
    api_secret: str = Field(..., description="Exchange API secret")
    api_passphrase: Optional[str] = Field(None, description="Exchange API passphrase (for some exchanges)")
    is_testnet: bool = Field(True, description="Whether these are testnet credentials")
    
    @validator('principal_id')
    def validate_principal_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Principal ID cannot be empty')
        return v.strip()

# === Bulk credentials + optional user settings ===
class ExchangeCredentialItemByPrincipal(BaseModel):
    exchange: ExchangeType
    api_key: str
    api_secret: str
    api_passphrase: Optional[str] = None
    is_testnet: bool = True

    @validator('api_key', 'api_secret')
    def _not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

class ExchangeCredentialsBulkByPrincipalRequest(BaseModel):
    principal_id: str = Field(..., description="ICP Principal ID")
    credentials: List[ExchangeCredentialItemByPrincipal]
    user_settings: Optional[MarketplaceUserSettingsPayload] = None

    @validator('principal_id')
    def validate_bulk_principal(cls, v):
        if not v or not v.strip():
            raise ValueError('Principal ID cannot be empty')
        return v.strip()

class MarketplaceSubscriptionControlRequest(BaseModel):
    """Request model for controlling marketplace subscriptions"""
    subscription_id: int = Field(..., description="Subscription ID")
    principal_id: str = Field(..., description="User Principal ID")
    api_key: str = Field(..., description="Bot API key for authentication")
    
    @validator('principal_id')
    def validate_principal_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Principal ID cannot be empty')
        return v.strip()
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('API key cannot be empty')
        return v.strip()


class MarketplaceSubscriptionTradingPairRequest(BaseModel):
    """Request model for controlling marketplace subscriptions"""
    subscription_id: int = Field(..., description="Subscription ID")
    principal_id: str = Field(..., description="User Principal ID")
    api_key: str = Field(..., description="Bot API key for authentication")
    trading_pair: str = Field(..., description="Trading pair like BTC/USDT")

    @validator('principal_id')
    def validate_principal_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Principal ID cannot be empty')
        return v.strip()

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('API key cannot be empty')
        return v.strip()

class MarketplaceSubscriptionControlResponse(BaseModel):
    """Response model for marketplace subscription control actions"""
    subscription_id: int
    principal_id: str
    action: str  # "paused", "cancelled", "resumed"
    status: SubscriptionStatus
    message: str
    timestamp: datetime

# PayPal Payment Schemas
class PayPalOrderRequest(BaseModel):
    """Request to create PayPal order"""
    user_principal_id: str
    bot_id: int
    duration_days: int
    pricing_tier: str  # "daily", "quarterly", "yearly"

class PayPalOrderResponse(BaseModel):
    """Response from PayPal order creation"""
    success: bool
    payment_id: str
    paypal_order_id: str
    approval_url: str
    amount_usd: Decimal
    amount_icp_equivalent: Decimal
    expires_in_minutes: int

class PayPalExecutionRequest(BaseModel):
    """Request to execute PayPal payment"""
    payment_id: str
    payer_id: str

class PayPalExecutionResponse(BaseModel):
    """Response from PayPal payment execution"""
    success: bool
    payment_id: str
    paypal_payment_id: Optional[str] = None
    rental_id: Optional[str] = None
    message: str
    rental_status: str  # "processing", "completed", "failed"

class PayPalPaymentBase(BaseModel):
    """Base PayPal payment schema"""
    user_principal_id: str
    bot_id: int
    duration_days: int
    pricing_tier: str
    amount_usd: Decimal
    amount_icp_equivalent: Decimal
    exchange_rate_usd_to_icp: Decimal

class PayPalPaymentCreate(PayPalPaymentBase):
    """Schema for creating PayPal payment"""
    pass

class PayPalPaymentInDB(PayPalPaymentBase):
    """PayPal payment from database"""
    id: str
    order_id: str
    status: str
    paypal_order_id: Optional[str] = None
    paypal_payment_id: Optional[str] = None
    paypal_payer_id: Optional[str] = None
    payer_email: Optional[str] = None
    payer_name: Optional[str] = None
    payer_country_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rental_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    
    class Config:
        from_attributes = True

class PayPalPaymentSummary(BaseModel):
    """Summary view of PayPal payment"""
    id: str
    user_principal_id: str
    bot_name: str
    amount_usd: Decimal
    status: str
    overall_status: str  # SUCCESS, NEEDS_MANUAL_REVIEW, FAILED, PENDING
    created_at: datetime
    completed_at: Optional[datetime] = None
    rental_id: Optional[str] = None

class PayPalConfigBase(BaseModel):
    """Base PayPal configuration schema"""
    environment: str
    client_id: str
    webhook_id: Optional[str] = None
    is_active: bool

class PayPalConfigCreate(PayPalConfigBase):
    """Schema for creating PayPal config"""
    client_secret: str
    webhook_secret: Optional[str] = None

class PayPalConfigInDB(PayPalConfigBase):
    """PayPal config from database"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PayPalWebhookEvent(BaseModel):
    """PayPal webhook event schema"""
    id: str
    event_type: str
    event_data: Dict[str, Any]
    payment_id: Optional[str] = None
    processed: bool
    created_at: datetime

# --- Developer Exchange Credentials Schemas ---
class DeveloperExchangeCredentialsBase(BaseModel):
    """Base schema for developer exchange credentials"""
    exchange_type: ExchangeType
    credential_type: CredentialType
    network_type: NetworkType
    name: str = Field(..., min_length=1, max_length=100)
    is_default: bool = False
    is_active: bool = True

class DeveloperExchangeCredentialsCreate(DeveloperExchangeCredentialsBase):
    """Schema for creating exchange credentials"""
    api_key: str = Field(..., min_length=10)
    api_secret: str = Field(..., min_length=10)
    passphrase: Optional[str] = None

class DeveloperExchangeCredentialsUpdate(BaseModel):
    """Schema for updating developer exchange credentials"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    api_key: Optional[str] = Field(None, min_length=10)
    api_secret: Optional[str] = Field(None, min_length=10)
    passphrase: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class DeveloperExchangeCredentialsPublic(DeveloperExchangeCredentialsBase):
    """Public view of exchange credentials (without secrets)"""
    id: int
    user_id: int
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DeveloperExchangeCredentialsInDB(DeveloperExchangeCredentialsPublic):
    """Full exchange credentials from database (with secrets)"""
    api_key: str  # This will be encrypted in the database
    api_secret: str  # This will be encrypted in the database
    passphrase: Optional[str] = None

# --- Prompt Template Schemas ---
class PromptTemplateBase(BaseModel):
    """Base schema for prompt templates"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    content: str = Field(..., min_length=1)
    category: str = Field(default="TRADING", pattern="^(TRADING|ANALYSIS|RISK_MANAGEMENT)$")
    is_active: bool = True
    is_default: bool = False

class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating a new prompt template"""
    pass

class PromptTemplateUpdate(BaseModel):
    """Schema for updating a prompt template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, pattern="^(TRADING|ANALYSIS|RISK_MANAGEMENT)$")
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class PromptTemplatePublic(BaseModel):
    """Public schema for prompt templates (without sensitive data)"""
    id: int
    name: str
    description: Optional[str]
    category: str
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PromptTemplateInDB(PromptTemplateBase):
    """Schema for prompt templates in database"""
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# LLM Provider Schemas
class LLMProviderType(str, Enum):
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    GEMINI = "GEMINI"
    GROQ = "GROQ"
    COHERE = "COHERE"

class LLMModelBase(BaseModel):
    """Base schema for LLM models"""
    model_name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    max_tokens: Optional[int] = Field(None, gt=0)
    cost_per_1k_tokens: Optional[Decimal] = Field(None, ge=0)

class LLMModelCreate(LLMModelBase):
    """Schema for creating LLM models"""
    pass

class LLMModelUpdate(BaseModel):
    """Schema for updating LLM models"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    max_tokens: Optional[int] = Field(None, gt=0)
    cost_per_1k_tokens: Optional[Decimal] = Field(None, ge=0)

class LLMModelInDB(LLMModelBase):
    """Schema for LLM models in database"""
    id: int
    provider_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LLMProviderBase(BaseModel):
    """Base schema for LLM providers"""
    provider_type: LLMProviderType
    name: str = Field(..., min_length=1, max_length=255)
    api_key: str = Field(..., min_length=1)
    base_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    is_default: bool = False

class LLMProviderCreate(LLMProviderBase):
    """Schema for creating LLM providers"""
    models: Optional[List[LLMModelCreate]] = []

class LLMProviderUpdate(BaseModel):
    """Schema for updating LLM providers"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    api_key: Optional[str] = Field(None, min_length=1)
    base_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class LLMProviderInDB(LLMProviderBase):
    """Schema for LLM providers in database"""
    id: int
    user_id: int
    models: List[LLMModelInDB] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

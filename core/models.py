from sqlalchemy import Column, Integer, BigInteger, String, Text, JSON, ForeignKey, DateTime, func, Float, Boolean, Enum, DECIMAL, Index
from sqlalchemy.orm import relationship
from core.database import Base
import enum

class UserRole(enum.Enum):
    USER = "USER"
    DEVELOPER = "DEVELOPER"
    ADMIN = "ADMIN"

class BotStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    ERROR = "ERROR"

class TradeStatus(enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class NetworkType(enum.Enum):
    TESTNET = "TESTNET"
    MAINNET = "MAINNET"

class TradeMode(enum.Enum):
    SPOT = "SPOT"
    MARGIN = "MARGIN"
    FUTURES = "FUTURES"

class ExchangeType(enum.Enum):
    MULTI = "MULTI"  # Multi-exchange support (Universal Bot)
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
    OKX = "OKX"
    BITGET = "BITGET"
    HUOBI = "HUOBI"
    KRAKEN = "KRAKEN"

class CredentialType(enum.Enum):
    SPOT = "SPOT"
    FUTURES = "FUTURES"
    MARGIN = "MARGIN"

class BotRegistrationStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class UserPrincipalStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class PayPalPaymentStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    COMPLETED_PENDING_RENTAL = "COMPLETED_PENDING_RENTAL"

class PaymentMethod(enum.Enum):
    STRIPE = "STRIPE"
    PAYPAL = "PAYPAL"
    TRIAL = "TRIAL"

class LLMProviderType(enum.Enum):
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    GEMINI = "GEMINI"
    GROQ = "GROQ"
    COHERE = "COHERE"

class PayPalEnvironment(enum.Enum):
    SANDBOX = "sandbox"
    LIVE = "live"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Developer profile fields
    developer_name = Column(String(255))
    developer_bio = Column(Text)
    developer_website = Column(String(255))
    
    # API credentials for trading
    api_key = Column(String(255))
    api_secret = Column(String(255))
    
    # Relationships
    developed_bots = relationship("Bot", back_populates="developer", foreign_keys="Bot.developer_id")
    approved_bots = relationship("Bot", back_populates="approved_by_user", foreign_keys="Bot.approved_by")
    subscriptions = relationship("Subscription", back_populates="user")
    reviews = relationship("BotReview", back_populates="user")
    exchange_credentials = relationship("ExchangeCredentials", back_populates="user", cascade="all, delete-orphan")
    llm_prompt_templates = relationship("LLMPromptTemplate", back_populates="creator")
    principals = relationship("UserPrincipal", back_populates="user", cascade="all, delete-orphan")
    llm_providers = relationship("LLMProvider", back_populates="user")
    llm_subscriptions = relationship("DeveloperLLMSubscription", back_populates="developer")
    llm_usage_logs = relationship("LLMUsageLog", back_populates="developer")

class UserPrincipal(Base):
    """Mapping between users and their principal IDs"""
    __tablename__ = "user_principals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    principal_id = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(Enum(UserPrincipalStatus), default=UserPrincipalStatus.ACTIVE)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="principals")
    
    # Table args for indexes
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_principal_id', 'principal_id'),
        Index('idx_principal_status', 'principal_id', 'status'),
    )

class ExchangeCredentials(Base):
    """User's API credentials for different exchanges"""
    __tablename__ = "exchange_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for marketplace users
    principal_id = Column(String(255), nullable=True)  # ICP Principal ID for marketplace users
    exchange = Column(Enum(ExchangeType), nullable=False)
    
    # Encrypted API credentials
    api_key = Column(String(255), nullable=False)
    api_secret = Column(String(255), nullable=False)
    api_passphrase = Column(String(255))  # For exchanges like Coinbase that need passphrase
    
    # Configuration
    is_testnet = Column(Boolean, default=True)  # Default to testnet for safety
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_validated = Column(DateTime)  # When credentials were last validated
    validation_status = Column(String(50), default="pending")  # pending, valid, invalid
    
    # Relationships
    user = relationship("User", back_populates="exchange_credentials")
    
    # Unique constraints: one credential set per user OR principal per exchange per testnet/mainnet
    __table_args__ = (
        Index('idx_unique_user_exchange_testnet', 'user_id', 'exchange', 'is_testnet', unique=True),
        Index('idx_unique_principal_exchange_testnet', 'principal_id', 'exchange', 'is_testnet', unique=True),
        Index('idx_principal_id', 'principal_id'),
    )


# NEW: Marketplace user settings keyed by principal_id (unique)
class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    principal_id = Column(String(255), nullable=False, unique=True, index=True)

    # Contact
    email = Column(String(255))

    # Social channels
    social_telegram = Column(String(255))
    social_discord = Column(String(255))
    social_twitter = Column(String(255))
    social_whatsapp = Column(String(255))

    telegram_chat_id = Column(String(255))
    discord_user_id = Column(String(255))

    # Default signal channel
    default_channel = Column(String(50), default="email")

    # Display settings
    display_dark_mode = Column(Boolean, default=False)
    display_currency = Column(String(10), default="ICP")
    display_language = Column(String(10), default="en")
    display_timezone = Column(String(64), default="UTC")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_user_settings_principal', 'principal_id', unique=True),
    )

class BotCategory(Base):
    __tablename__ = "bot_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    description = Column(Text)
    
    # Relationships
    bots = relationship("Bot", back_populates="category")

class Bot(Base):
    __tablename__ = "bots"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    description = Column(Text)
    developer_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("bot_categories.id"))
    status = Column(Enum(BotStatus), default=BotStatus.PENDING)
    image_url = Column(String(500), nullable=True)

    # Bot files and metadata
    code_path = Column(String(500))  # Path to uploaded bot code
    version = Column(String(50), default="1.0.0")

    #Bot rpa code path and version
    code_path_rpa = Column(String(500))  # Path to uploaded bot RPA
    version_rpa = Column(String(50), default="1.0.0")
    
    # Bot type and ML model support
    bot_type = Column(String(50), default="TECHNICAL")  # TECHNICAL, ML, DL, LLM
    model_path = Column(String(500))  # Path to ML model files
    model_metadata = Column(JSON)  # Model info, requirements, etc.
    bot_mode = Column(String(10), default="PASSIVE")

    #timeframe
    timeframe = Column(String(10), default="1h")
    timeframes = Column(JSON, default=list)  # MySQL-compatible JSON array default

    #exchange
    exchange_type = Column(Enum(ExchangeType), default=ExchangeType.BINANCE)
    trading_pair = Column(String(10), default="BTC/USDT")
    strategy_config = Column(JSON, default=dict)  # Strategy configuration overrides

    # Legacy pricing (keep for backward compatibility)
    price_per_month = Column(DECIMAL(10, 2), default=0.00)
    is_free = Column(Boolean, default=True)
    
    # Performance metrics
    total_subscribers = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    # Bot configuration schema (JSON schema for validation)
    config_schema = Column(JSON)
    default_config = Column(JSON)
    
    # Advanced trading configuration
    leverage = Column(Integer, default=10)
    risk_percentage = Column(Float, default=2.0)
    stop_loss_percentage = Column(Float, default=5.0)
    take_profit_percentage = Column(Float, default=10.0)
    
    # AI/LLM configuration
    llm_provider = Column(String(50), nullable=True)  # openai, anthropic, gemini
    enable_image_analysis = Column(Boolean, default=False)
    enable_sentiment_analysis = Column(Boolean, default=False)
    
    # Prompt template
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    approved_at = Column(DateTime)
    approved_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    developer = relationship("User", back_populates="developed_bots", foreign_keys=[developer_id])
    approved_by_user = relationship("User", back_populates="approved_bots", foreign_keys=[approved_by])
    category = relationship("BotCategory", back_populates="bots")
    subscriptions = relationship("Subscription", back_populates="bot")
    reviews = relationship("BotReview", back_populates="bot")
    bot_prompts = relationship("BotPrompt", back_populates="bot", cascade="all, delete-orphan")
    performance_metrics = relationship("BotPerformance", back_populates="bot")
    bot_files = relationship("BotFile", back_populates="bot")
    pricing_plans = relationship("BotPricingPlan", back_populates="bot", cascade="all, delete-orphan")
    promotions = relationship("BotPromotion", back_populates="bot", cascade="all, delete-orphan")
    marketplace_registrations = relationship("BotRegistration", back_populates="bot", cascade="all, delete-orphan")
    llm_usage_logs = relationship("LLMUsageLog", back_populates="bot")

class BotFile(Base):
    """Storage for bot files including ML models, weights, etc."""
    __tablename__ = "bot_files"
    id = Column(Integer, primary_key=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    file_type = Column(String(50))  # CODE, MODEL, WEIGHTS, CONFIG, DATA
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)  # Size in bytes
    file_hash = Column(String(64))  # SHA256 hash for integrity
    version = Column(String(50), default="1.0.0")
    description = Column(Text)
    
    # ML Model specific fields
    model_framework = Column(String(50))  # tensorflow, pytorch, sklearn, etc.
    model_type = Column(String(50))  # classification, regression, transformer, etc.
    input_shape = Column(JSON)  # Model input requirements
    output_shape = Column(JSON)  # Model output format
    
    # File metadata
    upload_date = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="bot_files")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    instance_name = Column(String(255))  # User's custom name for this bot instance
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Can be NULL for marketplace subscriptions
    bot_id = Column(Integer, ForeignKey("bots.id"))
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    
    # Pricing plan reference
    pricing_plan_id = Column(Integer, ForeignKey("bot_pricing_plans.id"))
    
    # Testnet and Trial support
    is_testnet = Column(Boolean, default=False)  # True for testnet subscriptions
    is_trial = Column(Boolean, default=False)    # True for trial subscriptions
    trial_expires_at = Column(DateTime)          # Trial expiration (can be different from expires_at)
    trading_pair = Column(String(20))  # Trading pair like BTC/USDT

    # New fields for marketplace bot registration
    user_principal_id = Column(String(255))  # ICP Principal ID
    trade_evaluation_period = Column(Integer)  # Minutes for bot analysis period
    network_type = Column(Enum(NetworkType), default=NetworkType.TESTNET)

    payment_method = Column(
        Enum(PaymentMethod, name="payment_method_enum", native_enum=False),  # native_enum=False để portable
        default=PaymentMethod.STRIPE,
        server_default="STRIPE",
        nullable=False,
    )
    paypal_payment_id = Column(String(255))  # nullable (chỉ dùng khi PAYPAL)

    # Marketplace subscription fields (for users without studio account)
    is_marketplace_subscription = Column(Boolean, default=False)
    marketplace_subscription_start = Column(DateTime, nullable=True)
    marketplace_subscription_end = Column(DateTime, nullable=True)

    # Execution configuration
    execution_config = Column(JSON)

    # Risk management
    risk_config = Column(JSON)
    
    # Subscription management
    started_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    
    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(15, 8), default=0.0)
    
    # Billing information
    billing_cycle = Column(String(20), default="MONTHLY")  # MONTHLY, QUARTERLY, YEARLY
    next_billing_date = Column(DateTime)
    auto_renew = Column(Boolean, default=True)


    # Relationships
    user = relationship("User", back_populates="subscriptions")
    bot = relationship("Bot", back_populates="subscriptions")
    pricing_plan = relationship("BotPricingPlan", back_populates="subscriptions")
    trades = relationship("Trade", back_populates="subscription")
    performance_logs = relationship("PerformanceLog", back_populates="subscription")
    invoices = relationship("SubscriptionInvoice", back_populates="subscription")

class Trade(Base):
    """Table to track individual trades"""
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    
    # Trade details
    side = Column(String(10))  # "BUY" or "SELL"
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
    entry_price = Column(DECIMAL(15, 8))
    exit_price = Column(DECIMAL(15, 8))
    quantity = Column(DECIMAL(15, 8))
    
    # Risk management
    stop_loss_price = Column(DECIMAL(15, 8))
    take_profit_price = Column(DECIMAL(15, 8))
    
    # Timing
    entry_time = Column(DateTime, server_default=func.now())
    exit_time = Column(DateTime)
    
    # P&L calculation
    pnl = Column(DECIMAL(15, 8))
    pnl_percentage = Column(Float)
    
    # Exchange information
    exchange_order_id = Column(String(100))
    exchange_trade_id = Column(String(100))
    
    # Relationships
    subscription = relationship("Subscription", back_populates="trades")

class BotReview(Base):
    """User reviews for bots"""
    __tablename__ = "bot_reviews"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bot_id = Column(Integer, ForeignKey("bots.id"))
    rating = Column(Integer)  # 1-5 stars
    review_text = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    bot = relationship("Bot", back_populates="reviews")

class BotPerformance(Base):
    """Aggregate performance metrics for bots"""
    __tablename__ = "bot_performance"
    id = Column(Integer, primary_key=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    
    # Time period
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Performance metrics
    total_subscribers = Column(Integer, default=0)
    active_subscribers = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    average_pnl = Column(DECIMAL(15, 8), default=0.0)
    total_pnl = Column(DECIMAL(15, 8), default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float)
    
    # Relationships
    bot = relationship("Bot", back_populates="performance_metrics")

class PerformanceLog(Base):
    """Individual performance logs for subscription tracking"""
    __tablename__ = "performance_logs"
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    
    # Log data
    timestamp = Column(DateTime, server_default=func.now())
    action = Column(String(50))  # "BUY", "SELL", "HOLD", "STOP_LOSS", "TAKE_PROFIT"
    price = Column(DECIMAL(15, 8))
    quantity = Column(DECIMAL(15, 8))
    balance = Column(DECIMAL(15, 8))
    
    # Bot signal details
    signal_data = Column(JSON)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="performance_logs")

class Payment(Base):
    """Payment records for subscriptions"""
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    
    # Payment details
    amount = Column(DECIMAL(10, 2))
    currency = Column(String(10), default="USD")
    payment_method = Column(String(50))
    payment_status = Column(String(50))  # "PENDING", "COMPLETED", "FAILED", "REFUNDED"
    
    # External payment info
    payment_provider = Column(String(50))  # "STRIPE", "PAYPAL", etc.
    external_payment_id = Column(String(255))
    
    # Timing
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    subscription = relationship("Subscription")

class BotPricingPlan(Base):
    """Pricing plans for bots (Free, Basic, Pro, Enterprise)"""
    __tablename__ = "bot_pricing_plans"
    
    id = Column(Integer, primary_key=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    plan_name = Column(String(100))  # "Free", "Basic", "Pro", "Enterprise"
    plan_description = Column(Text)
    
    # Pricing
    price_per_month = Column(DECIMAL(10, 2), default=0.00)
    price_per_year = Column(DECIMAL(10, 2), default=0.00)  # Annual discount
    price_per_quarter = Column(DECIMAL(10, 2), default=0.00)  # Quarterly discount
    
    # Features and limits
    max_trading_pairs = Column(Integer, default=1)  # Number of trading pairs allowed
    max_daily_trades = Column(Integer, default=10)  # Daily trade limit
    max_position_size = Column(DECIMAL(5, 2), default=0.10)  # Max 10% of balance
    advanced_features = Column(JSON)  # Custom features for this plan
    
    # Trial settings
    trial_days = Column(Integer, default=0)  # Free trial period
    trial_trades_limit = Column(Integer, default=5)  # Trial trade limit
    
    # Status
    is_active = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)  # Highlight this plan
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bot = relationship("Bot", back_populates="pricing_plans")
    subscriptions = relationship("Subscription", back_populates="pricing_plan")

class LLMPromptTemplate(Base):
    """LLM Prompt templates for trading analysis"""
    __tablename__ = "llm_prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)  # Rich text prompt content
    category = Column(String(100), default="TRADING")  # TRADING, ANALYSIS, RISK_MANAGEMENT
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="llm_prompt_templates")
    bot_prompts = relationship("BotPrompt", back_populates="llm_prompt_template")

class BotPrompt(Base):
    """Relationship between bots and prompt templates"""
    __tablename__ = "bot_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    prompt_id = Column(Integer, ForeignKey("llm_prompt_templates.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    custom_override = Column(Text)  # Bot-specific prompt customization
    attached_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    bot = relationship("Bot", back_populates="bot_prompts")
    llm_prompt_template = relationship("LLMPromptTemplate", back_populates="bot_prompts")

class BotPromotion(Base):
    """Promotional offers and discounts for bots"""
    __tablename__ = "bot_promotions"
    
    id = Column(Integer, primary_key=True)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    promotion_code = Column(String(50), unique=True)
    promotion_name = Column(String(100))
    promotion_description = Column(Text)
    
    # Discount settings
    discount_type = Column(String(20))  # "PERCENTAGE", "FIXED_AMOUNT", "FREE_TRIAL"
    discount_value = Column(DECIMAL(10, 2))  # 20.00 for 20% or $20
    max_uses = Column(Integer, default=100)  # Maximum uses
    used_count = Column(Integer, default=0)  # Current usage count
    
    # Validity period
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    
    # Eligibility
    min_subscription_months = Column(Integer, default=1)  # Minimum subscription period
    applicable_plans = Column(JSON)  # Which plans this applies to
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    bot = relationship("Bot", back_populates="promotions")
    creator = relationship("User")

class SubscriptionInvoice(Base):
    """Detailed invoice tracking for subscriptions"""
    __tablename__ = "subscription_invoices"
    
    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Invoice details
    invoice_number = Column(String(50), unique=True)
    amount = Column(DECIMAL(10, 2))
    currency = Column(String(10), default="USD")
    
    # Pricing breakdown
    base_price = Column(DECIMAL(10, 2))
    discount_amount = Column(DECIMAL(10, 2), default=0.00)
    tax_amount = Column(DECIMAL(10, 2), default=0.00)
    final_amount = Column(DECIMAL(10, 2))
    
    # Billing period
    billing_period_start = Column(DateTime)
    billing_period_end = Column(DateTime)
    
    # Payment status
    status = Column(String(20), default="PENDING")  # PENDING, PAID, OVERDUE, CANCELLED
    payment_method = Column(String(50))
    payment_date = Column(DateTime)
    
    # Promotional info
    promotion_code = Column(String(50))
    promotion_discount = Column(DECIMAL(10, 2), default=0.00)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    due_date = Column(DateTime)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="invoices")
    user = relationship("User")

class BotRegistration(Base):
    """Table for mapping ICP users to bots on marketplace"""
    __tablename__ = "register_bot"
    
    id = Column(Integer, primary_key=True, index=True)
    user_principal_id = Column(String(255), nullable=False, index=True)  # ICP Principal ID
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    status = Column(Enum(BotRegistrationStatus), default=BotRegistrationStatus.APPROVED)  # Mặc định APPROVED
    
    # Bot API Key - No index, no unique constraint
    api_key = Column(String(255), nullable=False)  # API key cho bot này
    
    # Registration details
    marketplace_name = Column(String(255))
    marketplace_description = Column(Text)
    price_on_marketplace = Column(DECIMAL(10, 2))
    commission_rate = Column(Float, default=0.10)
    
    # Status tracking - Simplified
    registered_at = Column(DateTime, server_default=func.now())
    
    # Marketplace settings
    is_featured = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="marketplace_registrations")

class PayPalPayment(Base):
    """PayPal payment tracking table"""
    __tablename__ = "paypal_payments"
    
    id = Column(String(255), primary_key=True)
    order_id = Column(String(255), unique=True, nullable=False)
    user_principal_id = Column(String(255), nullable=False, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    
    # Rental configuration
    duration_days = Column(Integer, nullable=False)
    pricing_tier = Column(String(50), nullable=False)
    
    # Pricing information
    amount_usd = Column(DECIMAL(10, 2), nullable=False)
    amount_icp_equivalent = Column(DECIMAL(18, 8), nullable=False)
    exchange_rate_usd_to_icp = Column(DECIMAL(18, 8), nullable=False)
    
    # PayPal specific fields
    status = Column(Enum(PayPalPaymentStatus), default=PayPalPaymentStatus.PENDING)
    paypal_order_id = Column(String(255), index=True)
    paypal_payment_id = Column(String(255))
    paypal_payer_id = Column(String(255))
    paypal_approval_url = Column(String(500))
    
    # Payer information (for guest checkout)
    payer_email = Column(String(255))
    payer_name = Column(String(255))
    payer_country_code = Column(String(5))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Rental linking
    rental_id = Column(String(255))
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    bot = relationship("Bot")

class PayPalConfig(Base):
    """PayPal configuration table"""
    __tablename__ = "paypal_config"
    
    id = Column(Integer, primary_key=True, index=True)
    environment = Column(Enum(PayPalEnvironment), default=PayPalEnvironment.SANDBOX)
    client_id = Column(String(255), nullable=False)
    client_secret = Column(String(500), nullable=False)
    webhook_id = Column(String(255))
    webhook_secret = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class PayPalWebhookEvent(Base):
    """PayPal webhook events for audit"""
    __tablename__ = "paypal_webhook_events"
    
    id = Column(String(255), primary_key=True)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=False)
    payment_id = Column(String(255), ForeignKey("paypal_payments.id"))
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    payment = relationship("PayPalPayment")

class DeveloperExchangeCredentials(Base):
    """Exchange API credentials for developers"""
    __tablename__ = "developer_exchange_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exchange_type = Column(Enum(ExchangeType), nullable=False)
    credential_type = Column(Enum(CredentialType), nullable=False)  # SPOT, FUTURES, MARGIN
    network_type = Column(Enum(NetworkType), nullable=False)  # TESTNET, MAINNET
    
    name = Column(String(100), nullable=False)  # User-friendly name like "Binance Futures Testnet"
    api_key = Column(Text, nullable=False)  # Encrypted
    api_secret = Column(Text, nullable=False)  # Encrypted
    passphrase = Column(String(255), nullable=True)  # For exchanges like OKX that need passphrase
    
    is_default = Column(Boolean, default=False)  # Default credential for this exchange+type+network combo
    is_active = Column(Boolean, default=True)
    
    # Metadata
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Indexes for faster queries
    __table_args__ = (
        Index('idx_user_exchange_type_network', 'user_id', 'exchange_type', 'credential_type', 'network_type'),
        Index('idx_user_default_credentials', 'user_id', 'is_default'),
    )

class TradingPromptTemplate(Base):
    """Trading strategy prompt templates"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    timeframe = Column(String(50), nullable=True)
    win_rate_estimate = Column(String(50), nullable=True)
    prompt = Column(Text, nullable=False)
    risk_management = Column(Text, nullable=True)
    best_for = Column(Text, nullable=True)
    template_metadata = Column("metadata", JSON, nullable=True)  # Use template_metadata as attribute name
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PromptCategory(Base):
    """Prompt template categories"""
    __tablename__ = "prompt_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_category = Column(String(100), nullable=True, index=True)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class UserFavoritePrompt(Base):
    """User's favorite prompt templates"""
    __tablename__ = "user_favorite_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(String(100), ForeignKey("prompt_templates.template_id"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User")
    template = relationship("TradingPromptTemplate")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_template', 'user_id', 'template_id', unique=True),
    )


class PromptUsageStats(Base):
    """Prompt template usage statistics"""
    __tablename__ = "prompt_usage_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(100), ForeignKey("prompt_templates.template_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=True)
    used_at = Column(DateTime, server_default=func.now(), index=True)
    performance_rating = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    template = relationship("TradingPromptTemplate")
    user = relationship("User")
    bot = relationship("Bot")


class Transaction(Base):
    """Enhanced transaction records for comprehensive trade performance tracking"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for marketplace users
    user_principal_id = Column(String(255), nullable=True, index=True)  # For marketplace users
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    prompt_id = Column(Integer, ForeignKey("llm_prompt_templates.id"), nullable=True)  # Track prompt used
    
    # Transaction details
    action = Column(String(20), nullable=False)  # BUY, SELL, etc.
    position_side = Column(String(10), nullable=True)  # LONG, SHORT for futures
    symbol = Column(String(20), nullable=False)  # BTC/USDT
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_time = Column(DateTime, nullable=True)  # When position was opened
    leverage = Column(Integer, default=1)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Exit information
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    exit_reason = Column(String(20), nullable=True)  # TP_HIT, SL_HIT, MANUAL, TIMEOUT, LIQUIDATION
    
    # P&L tracking
    pnl_usd = Column(Float, nullable=True)  # Realized P&L in USD
    pnl_percentage = Column(Float, nullable=True)  # P&L as percentage
    is_winning = Column(Boolean, nullable=True)  # Quick flag for win/loss
    realized_pnl = Column(Float, nullable=True)  # Final realized profit
    unrealized_pnl = Column(Float, nullable=True)  # Current unrealized P&L (for open positions)
    
    # Performance metrics
    risk_reward_ratio = Column(Float, nullable=True)  # Planned RR (e.g., 3.0 for 1:3)
    actual_rr_ratio = Column(Float, nullable=True)  # Actual RR achieved
    strategy_used = Column(String(100), nullable=True)  # From LLM recommendation
    
    # Trading costs
    fees_paid = Column(Float, nullable=True, default=0)  # Trading fees in USD
    slippage = Column(Float, nullable=True)  # Price slippage percentage
    
    # Trade duration
    trade_duration_minutes = Column(Integer, nullable=True)  # How long position held
    
    # Monitoring
    last_updated_price = Column(Float, nullable=True)  # Last known market price for open positions
    
    # Order details
    order_id = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)  # LLM confidence score
    reason = Column(Text, nullable=True)  # Trade reason
    status = Column(String(20), default='PENDING')  # PENDING, EXECUTED, OPEN, CLOSED, STOPPED_OUT, FAILED
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    bot = relationship("Bot")
    subscription = relationship("Subscription")
    llm_prompt_template = relationship("LLMPromptTemplate")
    
    # Indexes for faster queries
    __table_args__ = (
        Index('idx_transactions_user_id', 'user_id'),
        Index('idx_transactions_user_principal_id', 'user_principal_id'),
        Index('idx_transactions_bot_id', 'bot_id'),
        Index('idx_transactions_subscription_id', 'subscription_id'),
        Index('idx_transactions_prompt_id', 'prompt_id'),
        Index('idx_transactions_symbol', 'symbol'),
        Index('idx_transactions_status', 'status'),
        Index('idx_transactions_entry_time', 'entry_time'),
        Index('idx_transactions_exit_time', 'exit_time'),
        Index('idx_transactions_is_winning', 'is_winning'),
        Index('idx_transactions_bot_status', 'bot_id', 'status'),
        Index('idx_transactions_created_at', 'created_at'),
    )

class ExecutionLog(Base):
    """Execution logs for bot trading activities"""
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    task_id = Column(String(100), nullable=True)  # Celery task ID
    
    # Log details
    log_type = Column(String(20), nullable=False)  # system, analysis, llm, transaction, error
    message = Column(Text, nullable=False)
    level = Column(String(10), default='info')  # info, warning, error, debug
    data = Column(JSON, nullable=True)  # Additional structured data
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    bot = relationship("Bot")
    subscription = relationship("Subscription")
    
    # Indexes for faster queries
    __table_args__ = (
        Index('idx_execution_logs_bot_id', 'bot_id'),
        Index('idx_execution_logs_subscription_id', 'subscription_id'),
        Index('idx_execution_logs_task_id', 'task_id'),
        Index('idx_execution_logs_log_type', 'log_type'),
        Index('idx_execution_logs_created_at', 'created_at'),
    )

class LLMProvider(Base):
    """LLM Provider configurations for users"""
    __tablename__ = "llm_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_type = Column(Enum(LLMProviderType), nullable=False)
    name = Column(String(255), nullable=False)
    api_key = Column(Text, nullable=False)  # Encrypted
    base_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)  # Priority order (lower = higher priority)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")
    usage_logs = relationship("LLMUsageLog", back_populates="user_provider")
    
    # Indexes for faster queries
    __table_args__ = (
        Index('idx_llm_providers_user_id', 'user_id'),
        Index('idx_llm_providers_provider_type', 'provider_type'),
        Index('idx_llm_providers_is_active', 'is_active'),
        Index('idx_llm_providers_is_default', 'is_default'),
    )

class LLMModel(Base):
    """LLM Models for each provider"""
    __tablename__ = "llm_models"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("llm_providers.id"), nullable=False)
    model_name = Column(String(255), nullable=False)  # e.g., "gpt-4o"
    display_name = Column(String(255), nullable=False)  # e.g., "GPT-4o"
    is_active = Column(Boolean, default=True)
    max_tokens = Column(Integer, nullable=True)
    cost_per_1k_tokens = Column(DECIMAL(10, 6), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    provider = relationship("LLMProvider", back_populates="models")
    
    # Indexes for faster queries
    __table_args__ = (
        Index('idx_llm_models_provider_id', 'provider_id'),
        Index('idx_llm_models_model_name', 'model_name'),
        Index('idx_llm_models_is_active', 'is_active'),
    )


# =====================================================
# LLM Subscription and Billing Models
# =====================================================

class LLMSubscriptionPlan(Base):
    """Platform LLM subscription plans"""
    __tablename__ = "llm_subscription_plans"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Pricing
    price_per_month = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    
    # Limits
    max_requests_per_month = Column(Integer)
    max_tokens_per_month = Column(BigInteger)
    
    # Features (JSON)
    available_providers = Column(JSON)  # ["openai", "claude", "gemini"]
    available_models = Column(JSON)     # {"openai": ["gpt-4o-mini"], ...}
    
    # Status
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subscriptions = relationship("DeveloperLLMSubscription", back_populates="plan")


class DeveloperLLMSubscription(Base):
    """Developer LLM subscription records"""
    __tablename__ = "developer_llm_subscriptions"
    
    id = Column(Integer, primary_key=True)
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("llm_subscription_plans.id"), nullable=False)
    
    # Subscription status
    status = Column(Enum('ACTIVE', 'EXPIRED', 'CANCELLED', name='subscription_status'), default='ACTIVE')
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    auto_renew = Column(Boolean, default=True)
    
    # Usage tracking
    requests_used = Column(Integer, default=0)
    tokens_used = Column(BigInteger, default=0)
    last_reset_at = Column(DateTime)
    
    # Payment
    payment_status = Column(Enum('PENDING', 'PAID', 'FAILED', name='payment_status'), default='PENDING')
    payment_id = Column(String(255))
    payment_method = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    developer = relationship("User", back_populates="llm_subscriptions")
    plan = relationship("LLMSubscriptionPlan", back_populates="subscriptions")
    usage_logs = relationship("LLMUsageLog", back_populates="subscription")


class LLMUsageLog(Base):
    """LLM usage logs for billing and analytics"""
    __tablename__ = "llm_usage_logs"
    
    id = Column(BigInteger, primary_key=True)
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("developer_llm_subscriptions.id"))
    bot_id = Column(Integer, ForeignKey("bots.id"))
    
    # Request details
    provider = Column(String(50))
    model = Column(String(100))
    request_type = Column(String(50))
    
    # Usage metrics
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    cost_usd = Column(DECIMAL(10, 6))
    
    # Source
    source_type = Column(Enum('PLATFORM', 'USER_CONFIGURED', name='llm_source_type'))
    user_provider_id = Column(Integer, ForeignKey("llm_providers.id"))
    
    # Metadata
    request_duration_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Timestamp
    request_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    developer = relationship("User", back_populates="llm_usage_logs")
    subscription = relationship("DeveloperLLMSubscription", back_populates="usage_logs")
    bot = relationship("Bot", back_populates="llm_usage_logs")
    user_provider = relationship("LLMProvider", back_populates="usage_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_llm_usage_developer_date', 'developer_id', 'request_at'),
        Index('idx_llm_usage_subscription', 'subscription_id'),
        Index('idx_llm_usage_bot', 'bot_id'),
        Index('idx_llm_usage_provider', 'provider'),
        Index('idx_llm_usage_source', 'source_type'),
    )
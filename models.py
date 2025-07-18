from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime, func, Float, Boolean, Enum, DECIMAL, Index
from sqlalchemy.orm import relationship
from database import Base
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

class ExchangeType(enum.Enum):
    BINANCE = "BINANCE"
    COINBASE = "COINBASE"
    KRAKEN = "KRAKEN"

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

class ExchangeCredentials(Base):
    """User's API credentials for different exchanges"""
    __tablename__ = "exchange_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
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
    
    # Unique constraint: one credential set per user per exchange per testnet/mainnet
    __table_args__ = (
        Index('idx_unique_user_exchange_testnet', 'user_id', 'exchange', 'is_testnet', unique=True),
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
    
    # Bot files and metadata
    code_path = Column(String(500))  # Path to uploaded bot code
    version = Column(String(50), default="1.0.0")
    
    # Bot type and ML model support
    bot_type = Column(String(50), default="TECHNICAL")  # TECHNICAL, ML, DL, LLM
    model_path = Column(String(500))  # Path to ML model files
    model_metadata = Column(JSON)  # Model info, requirements, etc.
    
    # Pricing
    price_per_month = Column(DECIMAL(10, 2), default=0.00)
    is_free = Column(Boolean, default=True)
    
    # Performance metrics
    total_subscribers = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    # Bot configuration schema (JSON schema for validation)
    config_schema = Column(JSON)
    default_config = Column(JSON)
    
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
    performance_metrics = relationship("BotPerformance", back_populates="bot")
    bot_files = relationship("BotFile", back_populates="bot")

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
    user_id = Column(Integer, ForeignKey("users.id"))
    bot_id = Column(Integer, ForeignKey("bots.id"))
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    
    # Testnet and Trial support
    is_testnet = Column(Boolean, default=False)  # True for testnet subscriptions
    is_trial = Column(Boolean, default=False)    # True for trial subscriptions
    trial_expires_at = Column(DateTime)          # Trial expiration (can be different from expires_at)
    
    # Exchange and trading configuration
    exchange_type = Column(Enum(ExchangeType), default=ExchangeType.BINANCE)  # BINANCE, COINBASE, KRAKEN
    trading_pair = Column(String(20))
    timeframe = Column(String(10))  # "1h", "4h", "1d"
    
    # Strategy configuration (overrides defaults)
    strategy_config = Column(JSON)

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
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    bot = relationship("Bot", back_populates="subscriptions")
    trades = relationship("Trade", back_populates="subscription")
    performance_logs = relationship("PerformanceLog", back_populates="subscription")

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
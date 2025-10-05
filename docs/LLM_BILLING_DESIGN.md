# 🤖 LLM Model Billing & Configuration Design

## 📋 OVERVIEW

Hệ thống hỗ trợ 2 modes sử dụng LLM models:

### 1️⃣ **Platform-Provided Models** (Managed by Platform)
- Platform cung cấp API keys và manage models
- Developer **trả phí theo tháng** (prepaid subscription)
- Không cần config API keys
- Giới hạn usage theo plan (requests/month, tokens/month)
- **Use Cases**: 
  - Developers mới bắt đầu, không có API keys
  - Developers muốn tiết kiệm thời gian setup
  - Testing và prototyping

### 2️⃣ **User-Configured Models** (BYOK - Bring Your Own Keys)
- Developer tự config API keys trong `/creator/llm-providers`
- **Miễn phí** sử dụng (không charge platform fees)
- Developer tự trả phí trực tiếp cho provider (OpenAI, Anthropic, Google)
- Không giới hạn usage
- **Use Cases**:
  - Developers có sẵn API keys
  - High-volume usage
  - Custom models hoặc enterprise plans

---

## 🗄️ DATABASE SCHEMA

### 1. **llm_subscription_plans** Table (NEW)
```sql
CREATE TABLE llm_subscription_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,                    -- "Starter", "Pro", "Enterprise"
    description TEXT,
    
    -- Pricing
    price_per_month DECIMAL(10, 2) NOT NULL,       -- Monthly fee (VND or USD)
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Limits
    max_requests_per_month INT,                     -- Max LLM API calls
    max_tokens_per_month BIGINT,                    -- Max tokens (combined input+output)
    
    -- Features
    available_providers JSON,                       -- ["openai", "claude", "gemini"]
    available_models JSON,                          -- {"openai": ["gpt-4", "gpt-4o-mini"], ...}
    
    -- Priority and availability
    is_active BOOLEAN DEFAULT TRUE,
    display_order INT DEFAULT 0,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_active (is_active)
);

-- Seed data
INSERT INTO llm_subscription_plans (name, description, price_per_month, max_requests_per_month, max_tokens_per_month, available_providers, available_models) VALUES
('Free Trial', 'Try platform LLMs for free', 0, 100, 50000, 
 '["openai"]', 
 '{"openai": ["gpt-4o-mini"]}'),
 
('Starter', 'Basic LLM access for small bots', 10, 5000, 1000000,
 '["openai", "claude"]',
 '{"openai": ["gpt-4o-mini", "gpt-4o"], "claude": ["claude-3-5-sonnet-20241022"]}'),
 
('Pro', 'Advanced LLM access for production bots', 50, 30000, 10000000,
 '["openai", "claude", "gemini"]',
 '{"openai": ["gpt-4o-mini", "gpt-4o", "o1-preview"], "claude": ["claude-3-5-sonnet-20241022"], "gemini": ["gemini-1.5-pro"]}'),
 
('Enterprise', 'Unlimited LLM access', 200, 999999, 999999999,
 '["openai", "claude", "gemini"]',
 '{"openai": ["gpt-4o-mini", "gpt-4o", "o1-preview", "o1"], "claude": ["claude-3-5-sonnet-20241022", "claude-opus-4-20250514"], "gemini": ["gemini-1.5-pro", "gemini-2.0-flash-exp"]}');
```

### 2. **developer_llm_subscriptions** Table (NEW)
```sql
CREATE TABLE developer_llm_subscriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    developer_id INT NOT NULL,
    plan_id INT NOT NULL,
    
    -- Subscription period
    status ENUM('ACTIVE', 'EXPIRED', 'CANCELLED') DEFAULT 'ACTIVE',
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,                    -- Monthly billing
    auto_renew BOOLEAN DEFAULT TRUE,
    
    -- Usage tracking
    requests_used INT DEFAULT 0,
    tokens_used BIGINT DEFAULT 0,
    last_reset_at DATETIME,                        -- When usage was last reset
    
    -- Payment
    payment_status ENUM('PENDING', 'PAID', 'FAILED') DEFAULT 'PENDING',
    payment_id VARCHAR(255),                       -- PayPal/Stripe transaction ID
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (developer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES llm_subscription_plans(id),
    
    INDEX idx_developer_active (developer_id, status),
    INDEX idx_expiry (end_date)
);
```

### 3. **llm_usage_logs** Table (NEW)
```sql
CREATE TABLE llm_usage_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    developer_id INT NOT NULL,
    subscription_id INT,                           -- NULL if using user-configured
    bot_id INT,
    
    -- Request details
    provider VARCHAR(50),                          -- "openai", "claude", "gemini"
    model VARCHAR(100),                            -- "gpt-4o-mini", "claude-3-5-sonnet"
    request_type VARCHAR(50),                      -- "chat", "analysis", "signal_generation"
    
    -- Usage metrics
    input_tokens INT,
    output_tokens INT,
    total_tokens INT,
    
    -- Cost (if using platform models)
    cost_usd DECIMAL(10, 6),
    
    -- Source
    source_type ENUM('PLATFORM', 'USER_CONFIGURED'),
    user_provider_id INT,                          -- FK to developer_llm_providers if BYOK
    
    -- Timestamps
    request_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (developer_id) REFERENCES users(id),
    FOREIGN KEY (subscription_id) REFERENCES developer_llm_subscriptions(id),
    FOREIGN KEY (bot_id) REFERENCES bots(id),
    FOREIGN KEY (user_provider_id) REFERENCES developer_llm_providers(id),
    
    INDEX idx_developer_date (developer_id, request_at),
    INDEX idx_subscription (subscription_id)
);
```

### 4. **Update existing `developer_llm_providers` table**
```sql
-- Add priority fields
ALTER TABLE developer_llm_providers 
ADD COLUMN is_default BOOLEAN DEFAULT FALSE,
ADD COLUMN display_order INT DEFAULT 0,
ADD INDEX idx_developer_default (developer_id, is_default);

-- Ensure only one default per developer
-- This will be enforced in application logic
```

---

## 🎯 PROVIDER SELECTION LOGIC

### Priority System (Cascade):

```
1. User-Configured Provider (BYOK)
   ├─ Check if developer has any active providers
   ├─ Priority 1: Provider with is_default = TRUE
   ├─ Priority 2: First active provider (by display_order)
   └─ If found → Use BYOK (FREE)

2. Platform-Provided Models
   ├─ Check if developer has active subscription
   ├─ Verify subscription not expired
   ├─ Check usage limits (requests/tokens)
   └─ If valid → Use Platform Models (PAID)

3. Fallback
   └─ Error: No LLM provider available
```

### Flowchart:
```
┌─────────────────────────────────────────┐
│  Bot needs LLM analysis                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Check: Developer has BYOK providers?   │
└──────┬────────────────────┬─────────────┘
       │ YES                │ NO
       │                    │
       ▼                    ▼
┌──────────────────┐  ┌────────────────────────┐
│ Get Default      │  │ Check Platform         │
│ Provider         │  │ Subscription           │
└─────┬────────────┘  └────┬───────────────────┘
      │ Not found          │ Active & Valid?
      │                    │
      ▼                    ▼ YES
┌──────────────────┐  ┌────────────────────────┐
│ Get First Active │  │ Check Usage Limits     │
│ Provider         │  │ (requests/tokens)      │
└─────┬────────────┘  └────┬───────────────────┘
      │ Found              │ Within limits?
      │                    │
      ▼                    ▼ YES
┌─────────────────────────────────────────┐
│  ✅ Use BYOK                            │
│  (Free, no platform charges)            │
└─────────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────────────────┐
                    │  ✅ Use Platform Models  │
                    │  (Charge subscription)   │
                    │  + Log usage             │
                    └──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────┐
│  ❌ No Provider Available               │
│  Return error to bot                    │
└─────────────────────────────────────────┘
```

---

## 💻 IMPLEMENTATION

### 1. New Models (core/models.py)

```python
class LLMSubscriptionPlan(Base):
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
    
    # Features
    available_providers = Column(JSON)  # ["openai", "claude", "gemini"]
    available_models = Column(JSON)     # {"openai": ["gpt-4o-mini"], ...}
    
    # Status
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subscriptions = relationship("DeveloperLLMSubscription", back_populates="plan")


class DeveloperLLMSubscription(Base):
    __tablename__ = "developer_llm_subscriptions"
    
    id = Column(Integer, primary_key=True)
    developer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("llm_subscription_plans.id"), nullable=False)
    
    # Subscription period
    status = Column(Enum('ACTIVE', 'EXPIRED', 'CANCELLED'), default='ACTIVE')
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    auto_renew = Column(Boolean, default=True)
    
    # Usage tracking
    requests_used = Column(Integer, default=0)
    tokens_used = Column(BigInteger, default=0)
    last_reset_at = Column(DateTime)
    
    # Payment
    payment_status = Column(Enum('PENDING', 'PAID', 'FAILED'), default='PENDING')
    payment_id = Column(String(255))
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    developer = relationship("User", back_populates="llm_subscriptions")
    plan = relationship("LLMSubscriptionPlan", back_populates="subscriptions")
    usage_logs = relationship("LLMUsageLog", back_populates="subscription")


class LLMUsageLog(Base):
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
    source_type = Column(Enum('PLATFORM', 'USER_CONFIGURED'))
    user_provider_id = Column(Integer, ForeignKey("developer_llm_providers.id"))
    
    request_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    developer = relationship("User", back_populates="llm_usage_logs")
    subscription = relationship("DeveloperLLMSubscription", back_populates="usage_logs")
    bot = relationship("Bot", back_populates="llm_usage_logs")
    user_provider = relationship("DeveloperLLMProvider", back_populates="usage_logs")
```

### 2. Provider Selection Service (services/llm_provider_selector.py)

```python
"""
LLM Provider Selection Service
Determines which LLM provider to use: Platform or User-Configured (BYOK)
"""

from sqlalchemy.orm import Session
from core import models
from typing import Optional, Dict, Any, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMProviderSelector:
    """
    Smart LLM provider selection:
    1. Priority: User-configured providers (BYOK) - FREE
    2. Fallback: Platform subscription - PAID
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_provider_for_developer(
        self, 
        developer_id: int,
        bot_id: Optional[int] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Get best LLM provider for developer
        
        Returns:
            ("USER_CONFIGURED", {provider_config}) or
            ("PLATFORM", {subscription_config})
        
        Raises:
            Exception if no provider available
        """
        logger.info(f"🔍 Selecting LLM provider for developer {developer_id}")
        
        # 1️⃣ Check User-Configured Providers (BYOK) - PRIORITY
        user_provider = self._get_user_configured_provider(developer_id)
        if user_provider:
            logger.info(f"✅ Using BYOK provider: {user_provider['provider']} (FREE)")
            return ("USER_CONFIGURED", user_provider)
        
        # 2️⃣ Check Platform Subscription - FALLBACK
        platform_provider = self._get_platform_provider(developer_id)
        if platform_provider:
            logger.info(f"✅ Using Platform provider: {platform_provider['provider']} (PAID)")
            return ("PLATFORM", platform_provider)
        
        # 3️⃣ No provider available
        logger.error(f"❌ No LLM provider available for developer {developer_id}")
        raise Exception(
            "No LLM provider configured. Please either:\n"
            "1. Add your own API keys in /creator/llm-providers (FREE), or\n"
            "2. Subscribe to a Platform LLM plan"
        )
    
    def _get_user_configured_provider(self, developer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user's own LLM provider (BYOK)
        Priority: Default > First Active
        """
        # Check for default provider
        default_provider = self.db.query(models.DeveloperLLMProvider).filter(
            models.DeveloperLLMProvider.developer_id == developer_id,
            models.DeveloperLLMProvider.is_default == True,
            models.DeveloperLLMProvider.is_active == True
        ).first()
        
        if default_provider:
            logger.info(f"📌 Found default BYOK provider: {default_provider.provider}")
            return self._format_user_provider(default_provider)
        
        # Fallback to first active provider
        first_active = self.db.query(models.DeveloperLLMProvider).filter(
            models.DeveloperLLMProvider.developer_id == developer_id,
            models.DeveloperLLMProvider.is_active == True
        ).order_by(
            models.DeveloperLLMProvider.display_order.asc(),
            models.DeveloperLLMProvider.created_at.asc()
        ).first()
        
        if first_active:
            logger.info(f"📌 Found active BYOK provider: {first_active.provider}")
            return self._format_user_provider(first_active)
        
        logger.info("❌ No BYOK provider found")
        return None
    
    def _format_user_provider(self, provider: models.DeveloperLLMProvider) -> Dict[str, Any]:
        """Format user provider config"""
        # Decrypt API key
        from core.api_key_manager import decrypt_api_key
        
        decrypted_key = decrypt_api_key(provider.encrypted_api_key)
        
        return {
            'source': 'USER_CONFIGURED',
            'provider_id': provider.id,
            'provider': provider.provider,  # "openai", "claude", "gemini"
            'model': provider.model,
            'api_key': decrypted_key,
            'config': provider.config or {},
            'is_free': True  # No platform charges
        }
    
    def _get_platform_provider(self, developer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get platform LLM subscription
        Check: Active subscription + within limits
        """
        # Get active subscription
        subscription = self.db.query(models.DeveloperLLMSubscription).filter(
            models.DeveloperLLMSubscription.developer_id == developer_id,
            models.DeveloperLLMSubscription.status == 'ACTIVE',
            models.DeveloperLLMSubscription.end_date > datetime.now(),
            models.DeveloperLLMSubscription.payment_status == 'PAID'
        ).order_by(
            models.DeveloperLLMSubscription.end_date.desc()
        ).first()
        
        if not subscription:
            logger.info("❌ No active platform subscription")
            return None
        
        # Check usage limits
        plan = subscription.plan
        if subscription.requests_used >= plan.max_requests_per_month:
            logger.warning(f"⚠️ Request limit reached: {subscription.requests_used}/{plan.max_requests_per_month}")
            return None
        
        if subscription.tokens_used >= plan.max_tokens_per_month:
            logger.warning(f"⚠️ Token limit reached: {subscription.tokens_used}/{plan.max_tokens_per_month}")
            return None
        
        # Get default provider/model from plan
        available_providers = plan.available_providers or []
        available_models = plan.available_models or {}
        
        if not available_providers:
            logger.error("❌ Plan has no available providers")
            return None
        
        # Select first available provider
        provider = available_providers[0]
        models_list = available_models.get(provider, [])
        model = models_list[0] if models_list else None
        
        if not model:
            logger.error(f"❌ No model available for provider {provider}")
            return None
        
        # Get platform API key from environment
        import os
        api_key_map = {
            'openai': os.getenv('PLATFORM_OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY'),
            'claude': os.getenv('PLATFORM_CLAUDE_API_KEY') or os.getenv('CLAUDE_API_KEY'),
            'gemini': os.getenv('PLATFORM_GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY')
        }
        
        api_key = api_key_map.get(provider)
        if not api_key:
            logger.error(f"❌ Platform API key not configured for {provider}")
            return None
        
        logger.info(f"✅ Platform subscription valid: {plan.name}")
        return {
            'source': 'PLATFORM',
            'subscription_id': subscription.id,
            'plan_name': plan.name,
            'provider': provider,
            'model': model,
            'api_key': api_key,
            'requests_remaining': plan.max_requests_per_month - subscription.requests_used,
            'tokens_remaining': plan.max_tokens_per_month - subscription.tokens_used,
            'is_free': False  # Will be charged
        }
    
    def log_usage(
        self,
        developer_id: int,
        provider_config: Dict[str, Any],
        bot_id: Optional[int],
        request_type: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float = 0.0
    ):
        """Log LLM usage and update subscription if using platform"""
        total_tokens = input_tokens + output_tokens
        
        # Create usage log
        usage_log = models.LLMUsageLog(
            developer_id=developer_id,
            subscription_id=provider_config.get('subscription_id'),
            bot_id=bot_id,
            provider=provider_config['provider'],
            model=provider_config['model'],
            request_type=request_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            source_type=provider_config['source'],
            user_provider_id=provider_config.get('provider_id')
        )
        self.db.add(usage_log)
        
        # If using platform, update subscription usage
        if provider_config['source'] == 'PLATFORM':
            subscription = self.db.query(models.DeveloperLLMSubscription).get(
                provider_config['subscription_id']
            )
            if subscription:
                subscription.requests_used += 1
                subscription.tokens_used += total_tokens
                logger.info(
                    f"📊 Platform usage updated: "
                    f"requests={subscription.requests_used}, "
                    f"tokens={subscription.tokens_used}"
                )
        
        self.db.commit()
        logger.info(f"✅ Usage logged: {total_tokens} tokens")
```

### 3. Update LLMIntegration class (services/llm_integration.py)

```python
# Add at the top of __init__ method:

def __init__(self, config: Optional[Dict[str, Any]] = None, db: Optional[Session] = None, developer_id: Optional[int] = None):
    """
    Initialize LLM Integration
    
    Args:
        config: Optional configuration override
        db: Database session for provider selection
        developer_id: Developer ID to select appropriate provider
    """
    self.config = config or {}
    self.db = db
    self.developer_id = developer_id
    
    # Smart provider selection if db and developer_id provided
    if db and developer_id:
        try:
            from services.llm_provider_selector import LLMProviderSelector
            selector = LLMProviderSelector(db)
            source_type, provider_config = selector.get_provider_for_developer(developer_id)
            
            logger.info(f"🎯 Selected {source_type} provider for developer {developer_id}")
            
            # Override config with selected provider
            if provider_config['provider'] == 'openai':
                self.config['openai_api_key'] = provider_config['api_key']
                self.config['openai_model'] = provider_config['model']
            elif provider_config['provider'] == 'claude':
                self.config['claude_api_key'] = provider_config['api_key']
                self.config['claude_model'] = provider_config['model']
            elif provider_config['provider'] == 'gemini':
                self.config['gemini_api_key'] = provider_config['api_key']
                self.config['gemini_model'] = provider_config['model']
            
            # Store for usage logging
            self._provider_config = provider_config
            self._provider_selector = selector
            
        except Exception as e:
            logger.error(f"❌ Failed to select LLM provider: {e}")
            # Fall back to environment variables
            self._provider_config = None
            self._provider_selector = None
    else:
        self._provider_config = None
        self._provider_selector = None
    
    # ... rest of existing __init__ code ...
```

---

## 🎨 FRONTEND UI

### 1. LLM Subscription Plans Page
**Path**: `/creator/llm-subscription`

```typescript
// Show available plans
[Free Trial] [Starter] [Pro] [Enterprise]

Each card shows:
- Plan name
- Price/month
- Features (providers, models)
- Limits (requests/month, tokens/month)
- [Subscribe] button

// Show current subscription status
Your Current Plan: Pro
- Expires: 2025-11-05
- Requests used: 1,234 / 30,000
- Tokens used: 456,789 / 10,000,000
- [Upgrade] [Cancel] buttons
```

### 2. LLM Providers Page Enhancement
**Path**: `/creator/llm-providers`

```typescript
// Add banner at top:
┌─────────────────────────────────────────────────────┐
│ 💡 Choose Your LLM Source:                          │
│                                                     │
│ Option 1: Use Your Own API Keys (FREE)             │
│ ✅ No platform charges                             │
│ ✅ Unlimited usage                                 │
│ ➡️ Add your API keys below                         │
│                                                     │
│ Option 2: Use Platform LLMs (PAID)                 │
│ ✅ No setup required                               │
│ ✅ Managed by platform                             │
│ ➡️ Subscribe to a plan →                           │
└─────────────────────────────────────────────────────┘

// Add "Set as Default" toggle to each provider card
// Add "Priority Order" drag-and-drop
```

---

## 📊 USAGE & BILLING

### Monthly Billing Cycle:
```
Day 1: Subscription starts
  ↓
Day 1-30: Track usage
  ├─ Each LLM call: requests_used++, tokens_used++
  ├─ Check limits before each call
  └─ Log usage in llm_usage_logs
  ↓
Day 30: Check auto_renew
  ├─ If TRUE: Charge payment method → Extend end_date
  ├─ If FALSE: Mark as EXPIRED
  └─ Reset requests_used and tokens_used
```

### Cost Estimation:
```python
# Platform markup: 20% over actual cost
PLATFORM_COST_MULTIPLIER = 1.2

# Base costs (per 1M tokens, as of 2025)
MODEL_COSTS = {
    'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
    'gpt-4o': {'input': 2.50, 'output': 10.00},
    'claude-3-5-sonnet': {'input': 3.00, 'output': 15.00},
    'gemini-1.5-pro': {'input': 1.25, 'output': 5.00}
}
```

---

## ✅ SUMMARY

### Developer Experience:

**Scenario 1: Has API Keys**
```
1. Go to /creator/llm-providers
2. Add OpenAI API key
3. Set as default
4. ✅ All bots use BYOK (FREE)
```

**Scenario 2: No API Keys**
```
1. Go to /creator/llm-subscription
2. Choose "Starter" plan ($10/month)
3. Pay via PayPal
4. ✅ All bots use Platform LLMs (PAID)
```

**Scenario 3: Mixed**
```
1. Has some API keys configured
2. Platform uses BYOK first
3. If BYOK fails → fallback to Platform subscription
```

### Priority Logic Summary:
```
BYOK (is_default=True)
  > BYOK (first active)
    > Platform (active subscription)
      > ERROR (no provider)
```

---

## 🚀 NEXT STEPS

1. ✅ Review this design
2. Create database migration for new tables
3. Implement models and services
4. Create API endpoints for subscriptions
5. Build frontend UI
6. Add payment integration (PayPal)
7. Add usage monitoring dashboard
8. Test with real bots

---

**Status**: 📋 Design Complete - Ready for Implementation


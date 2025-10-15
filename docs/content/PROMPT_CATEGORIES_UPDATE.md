# Prompt Templates Category System

## 📋 Overview
Simplified prompt template categorization system with 2 main categories for better user experience.

## 🎯 Categories

### 1. **Trading** (17 Templates)
Strategic trading prompts for market analysis and trade execution:
- EMA Ribbon System
- Bollinger Band Squeeze
- Smart Money Concepts
- Order Flow Imbalance
- London Session Breakout
- Three-Bar Reversal Pattern
- Turtle Soup (False Breakout)
- Wyckoff Distribution Detection
- Funding Rate Extreme Reversal
- Volume Spread Analysis
- RSI Divergence with Volume Confirmation
- MACD + Stochastic Convergence
- Ichimoku Cloud Breakout
- Moving Average Crossover with Volume
- Fibonacci Retracement with Confluence
- Support/Resistance Breakout
- Composite High-Probability Setup

**Best For:**
- Technical analysis strategies
- Entry/exit timing
- Market structure analysis
- Pattern recognition
- Trend following systems

---

### 2. **Risk Management** (14 Templates)
Position sizing and capital management prompts:

#### **Basic** (2 templates)
- Basic Position Size Calculator
- Scale-In Position Sizing

#### **Advanced** (4 templates)
- ATR Volatility-Adjusted Sizing
- Correlation-Adjusted Position Sizing
- Kelly Criterion Calculator
- Drawdown-Adjusted Sizing

#### **Leverage** (2 templates)
- Leverage Safety Calculator
- Multi-Position Margin Manager

#### **Confidence** (2 templates)
- Setup Quality Adjustment
- Market Regime Position Sizing

#### **Comprehensive** (2 templates)
- Complete Position Sizing Analysis
- Position Size Validator

#### **Specialized** (2 templates)
- News/Event Position Sizing
- Recovery Phase Position Sizing

**Best For:**
- Capital allocation
- Risk per trade calculation
- Portfolio diversification
- Leverage management
- Drawdown recovery
- Pre-trade validation

---

## 🖥️ UI Implementation

### Category Tabs
Located in: `frontend/app/creator/prompts/new/page.tsx`

```tsx
// 3 tabs with template counts
🌟 All (31)
📈 Trading Strategies (17)
🛡️ Risk Management (14)
```

### Features
- **Dynamic Filtering**: Click tabs to filter templates by category
- **Live Count**: Shows number of templates in each category
- **Visual Feedback**: Active tab highlighted in purple
- **Responsive Design**: Works on mobile and desktop

---

## 📊 Database Schema

### Table: `prompt_templates`
```sql
category VARCHAR(100) NOT NULL
```

**Allowed Values:**
- `'Trading'` - All trading strategy templates
- `'Risk Management'` - All position sizing & risk templates

### Migration Commands
```sql
-- Update old templates to 'Trading'
UPDATE prompt_templates 
SET category = 'Trading' 
WHERE category NOT LIKE 'Risk Management%';

-- Consolidate Risk Management sub-categories
UPDATE prompt_templates 
SET category = 'Risk Management' 
WHERE category LIKE 'Risk Management%';
```

---

## 🔄 Category Mapping

### Form Categories (Internal)
```typescript
type FormCategory = 'TRADING' | 'ANALYSIS' | 'RISK_MANAGEMENT'
```

### Template Categories (Display)
```typescript
type TemplateCategory = 'Trading' | 'Risk Management'
```

### Mapping Logic
```typescript
const formCategory = strategy.category === 'Risk Management' 
  ? 'RISK_MANAGEMENT' 
  : 'TRADING'
```

---

## 📈 Usage Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| Trading | 17 | 55% |
| Risk Management | 14 | 45% |
| **Total** | **31** | **100%** |

---

## 🚀 API Endpoints

### Get All Templates
```bash
GET /prompts/templates?limit=100
```

### Filter by Category
```bash
# Trading only
GET /prompts/templates?category=Trading

# Risk Management only
GET /prompts/templates?category=Risk+Management
```

### Response Format
```json
[
  {
    "id": 1,
    "template_id": "ema_ribbon_precise",
    "title": "EMA Ribbon System",
    "category": "Trading",
    "timeframe": "4H, Daily",
    "win_rate_estimate": "65-72%",
    "prompt": "...",
    "best_for": "BTC, ETH on trending markets"
  }
]
```

---

## 🎨 Design Decisions

### Why Only 2 Categories?

**Before:** 21+ sub-categories (confusing)
```
- Technical - Refined
- Technical - Statistical
- Technical - Holistic
- Smart Money - Advanced
- Smart Money - Precise
- Price Action - Classic
- Risk Management - Basic
- Risk Management - Advanced
... (too many!)
```

**After:** 2 main categories (clear & simple)
```
- Trading (17)
- Risk Management (14)
```

**Benefits:**
✅ Clearer mental model for users
✅ Faster template discovery
✅ Reduced decision paralysis
✅ Better mobile UX
✅ Easier to maintain

---

## 🛠️ Technical Implementation

### Frontend State Management
```typescript
const [activeCategory, setActiveCategory] = useState<string>('all')

// Filter templates by category
const filteredTemplates = templatePrompts?.filter(template => 
  activeCategory === 'all' || template.category === activeCategory
) || []
```

### Category Tab Component
```tsx
<button
  onClick={() => setActiveCategory('Trading')}
  className={activeCategory === 'Trading' ? 'active' : ''}
>
  📈 Trading Strategies ({tradingCount})
</button>
```

---

## 📝 Adding New Templates

### For Trading Strategies
```python
{
  "template_id": "my_strategy",
  "title": "My Trading Strategy",
  "category": "Trading",  # Always "Trading"
  "prompt": "...",
  # ...
}
```

### For Risk Management
```python
{
  "template_id": "my_risk_template",
  "title": "My Risk Template",
  "category": "Risk Management",  # Always "Risk Management"
  "prompt": "...",
  # ...
}
```

---

## 🔍 Testing

### Verify Categories
```bash
mysql -u botuser -pbotpassword123 -h 127.0.0.1 -P 3307 -D bot_marketplace -e "
SELECT category, COUNT(*) as count 
FROM prompt_templates 
GROUP BY category;
"
```

**Expected Output:**
```
category         | count
-----------------|------
Trading          | 17
Risk Management  | 14
```

### Test API
```bash
curl "http://localhost:8000/prompts/templates?limit=100" | jq '[.[] | .category] | group_by(.) | map({category: .[0], count: length})'
```

---

## 📚 Related Files

- **Frontend Component:** `frontend/app/creator/prompts/new/page.tsx`
- **Seeding Script:** `scripts/seed_risk_management_prompts.py`
- **Database Model:** `core/models.py` → `TradingPromptTemplate`
- **API Endpoint:** `api/endpoints/prompts.py`
- **Hook:** `frontend/hooks/usePrompts.ts`

---

## ✅ Summary

**Changed:**
- Consolidated 21+ sub-categories → 2 main categories
- Updated database: all templates now have clear category
- Updated UI: 3 tabs (All, Trading, Risk Management)
- Auto-mapping: template category → form category

**Result:**
- 📈 **17 Trading Strategy Templates**
- 🛡️ **14 Risk Management Templates**
- 🎯 **Clear & Simple UX**
- ⚡ **Fast Template Discovery**

---

*Last Updated: October 4, 2025*


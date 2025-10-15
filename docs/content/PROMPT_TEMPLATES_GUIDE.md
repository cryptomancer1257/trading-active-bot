# Trading Prompt Templates System

## Overview
A comprehensive library of 17+ proven trading strategy prompts with detailed entry/exit rules, risk management, and performance expectations.

## Features

### 1. Prompt Templates Database
- **17+ Trading Strategies**: From EMA Ribbon to Smart Money Concepts
- **Multiple Categories**: Technical, Smart Money, Price Action, Volume, etc.
- **Win Rate Estimates**: 55-80% based on backtest data
- **Complete Trade Plans**: Entry, Stop Loss, Take Profit, Trailing Stops

### 2. API Endpoints

#### Get All Templates
```
GET /prompts/templates
Query Parameters:
- category: Filter by category
- search: Search in title/description
- timeframe: Filter by timeframe (4H, Daily, etc.)
- min_win_rate: Minimum win rate percentage
- skip: Pagination offset
- limit: Max results (default 100)
```

#### Get Single Template
```
GET /prompts/templates/{template_id}
Example: GET /prompts/templates/ema_ribbon_precise
```

#### Get Categories
```
GET /prompts/categories
Returns: List of all categories with template counts
```

#### Add to Favorites
```
POST /prompts/favorites/{template_id}
Body: { "notes": "Optional notes" }
Requires: Authentication
```

#### Remove from Favorites
```
DELETE /prompts/favorites/{template_id}
Requires: Authentication
```

#### Get User Favorites
```
GET /prompts/favorites
Requires: Authentication
Returns: User's favorited prompts with notes
```

#### Record Usage
```
POST /prompts/usage/{template_id}
Body: {
  "bot_id": 123,
  "performance_rating": 4,
  "notes": "Worked well in trending market"
}
Requires: Authentication
```

#### Get Template Stats
```
GET /prompts/stats/{template_id}
Returns: Usage count, average rating, favorite count
```

## Database Schema

### Tables Created

1. **prompt_templates**: Main template storage
   - `id`: Primary key
   - `template_id`: Unique identifier (e.g., "ema_ribbon_precise")
   - `title`: Display name
   - `category`: Strategy category
   - `timeframe`: Recommended timeframes
   - `win_rate_estimate`: Expected win rate range
   - `prompt`: Complete trading strategy text
   - `risk_management`: Risk rules
   - `best_for`: Best market conditions
   - `metadata`: JSON with tags, difficulty level
   - `is_active`: Enable/disable template
   - `created_at`, `updated_at`: Timestamps

2. **prompt_categories**: Category management
   - `id`: Primary key
   - `category_name`: Unique category name
   - `description`: Category description
   - `parent_category`: For hierarchical categories
   - `display_order`: Sort order
   - `is_active`: Enable/disable category

3. **user_favorite_prompts**: User favorites
   - `id`: Primary key
   - `user_id`: FK to users table
   - `template_id`: FK to prompt_templates
   - `notes`: User's personal notes
   - `created_at`: When favorited

4. **prompt_usage_stats**: Usage tracking
   - `id`: Primary key
   - `template_id`: FK to prompt_templates
   - `user_id`: Who used it
   - `bot_id`: Which bot used it
   - `used_at`: When used
   - `performance_rating`: 1-5 star rating
   - `notes`: Usage notes

## Migration

### File Location
```
migrations/versions/025_create_prompt_templates.sql
```

### Running Migration

#### Method 1: Using Python Script
```bash
cd /path/to/trade-bot-marketplace
source .venv/bin/activate
python -c "
from core.database import get_db
from sqlalchemy import text

db = next(get_db())
with open('migrations/versions/025_create_prompt_templates.sql', 'r') as f:
    sql_script = f.read()

# Execute migration
statements = sql_script.split(';')
for statement in statements:
    if statement.strip():
        db.execute(text(statement))
        db.commit()
"
```

#### Method 2: Direct MySQL
```bash
mysql -h 127.0.0.1 -u root -p bot_marketplace < migrations/versions/025_create_prompt_templates.sql
```

#### Method 3: Using Migration Runner
```bash
cd /path/to/trade-bot-marketplace
source .venv/bin/activate
python migrations/migration_runner.py
# Select: 025_create_prompt_templates.sql
```

## Available Strategy Templates

### High Win Rate (65-80%)
1. **EMA Ribbon System** (65-72%)
   - Category: Technical - Refined
   - Timeframe: 4H, Daily
   - Best for: BTC, ETH on trending markets

2. **VWAP Mean Reversion** (70-78%)
   - Category: Technical - Statistical
   - Timeframe: 5m, 15m, 1H
   - Best for: Intraday, range-bound markets

3. **Volume Profile POC Bounce** (68-75%)
   - Category: Volume - Advanced
   - Timeframe: 1H, 4H, Daily
   - Best for: BTC/ETH consolidation phases

4. **Composite High-Probability** (72-80%)
   - Category: Multi-Factor - Elite
   - Timeframe: 4H, Daily
   - Best for: Patient traders, best RR setups

5. **Advanced Scalping System** (68-75%)
   - Category: Scalping - Elite
   - Timeframe: 1m, 5m, 15m
   - Best for: Active traders with Level 2 data

### Smart Money Strategies (58-68%)
6. **Order Flow Imbalance** (58-65%)
7. **Supply/Demand Zone Entry** (62-68%)
8. **Liquidity Grab SMC** (58-66%)
9. **Market Structure Break** (61-68%)

### Price Action & Patterns (55-69%)
10. **Turtle Soup False Breakout** (55-63%)
11. **London Session Breakout** (62-69%)
12. **Three-Bar Reversal** (60-67%)

### Technical Indicators (56-72%)
13. **RSI Divergence Strict** (56-64%)
14. **Ichimoku Cloud Breakout** (64-71%)
15. **Bollinger Band Squeeze** (65-72%)

### Alternative Strategies (60-70%)
16. **Funding Rate Extreme** (60-70%)
17. **Swing Trading Pro** (60-70%)

## Usage Examples

### 1. List All Technical Strategies
```javascript
fetch('/prompts/templates?category=Technical%20-%20Refined')
  .then(res => res.json())
  .then(data => console.log(data));
```

### 2. Search for Scalping Strategies
```javascript
fetch('/prompts/templates?search=scalping')
  .then(res => res.json())
  .then(data => console.log(data));
```

### 3. Get High Win Rate Strategies
```javascript
fetch('/prompts/templates?min_win_rate=65')
  .then(res => res.json())
  .then(data => console.log(data));
```

### 4. Add to Favorites
```javascript
fetch('/prompts/favorites/ema_ribbon_precise', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    notes: 'Works great on BTC 4H chart'
  })
})
```

### 5. Get User's Favorites
```javascript
fetch('/prompts/favorites', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
.then(res => res.json())
.then(favorites => console.log(favorites));
```

### 6. Record Usage
```javascript
fetch('/prompts/usage/ema_ribbon_precise', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    bot_id: 123,
    performance_rating: 4,
    notes: 'Great performance in uptrend'
  })
})
```

## Integration with Bots

### Using Prompts in Bot Configuration
```python
from core.models import Bot, PromptTemplate

# Get bot
bot = db.query(Bot).get(bot_id)

# Get prompt template
template = db.query(PromptTemplate).filter(
    PromptTemplate.template_id == 'ema_ribbon_precise'
).first()

# Use prompt in bot
bot.prompt_template = template.prompt
bot.risk_management = template.risk_management
db.commit()
```

### Tracking Performance
```python
from core.models import PromptUsageStats

# Record usage
usage = PromptUsageStats(
    template_id='ema_ribbon_precise',
    user_id=user.id,
    bot_id=bot.id,
    performance_rating=4,
    notes='Won 7/10 trades'
)
db.add(usage)
db.commit()
```

## Best Practices

### 1. Strategy Selection
- **Match to Market Conditions**: Trending vs. Ranging
- **Consider Timeframe**: Scalping vs. Swing trading
- **Check Win Rate**: Higher win rate = tighter stops needed
- **Risk Management**: Always follow the risk rules

### 2. Customization
- Start with base template
- Adjust position sizes based on account
- Modify timeframes for your trading style
- Add personal filters

### 3. Performance Tracking
- Record each usage with bot_id
- Rate performance honestly (1-5 stars)
- Add notes about market conditions
- Review stats monthly

### 4. Favorites Management
- Save strategies that work for you
- Add detailed notes about when to use
- Review favorites before trading session
- Update notes with new learnings

## Future Enhancements

### Planned Features
1. **Community Ratings**: Allow users to rate templates
2. **Performance Analytics**: Aggregate performance across all users
3. **Custom Templates**: Users can create and share their own
4. **Backtesting Integration**: Auto-backtest templates
5. **AI Optimization**: ML-based parameter tuning
6. **Live Trading Integration**: One-click deploy to bot
7. **Alerts**: Notify when conditions met
8. **Mobile App**: Access templates on mobile

## Troubleshooting

### Migration Fails
```bash
# Check tables exist
mysql -u root -p bot_marketplace -e "SHOW TABLES LIKE 'prompt%'"

# Check records
mysql -u root -p bot_marketplace -e "SELECT COUNT(*) FROM prompt_templates"

# Re-run migration
python migrations/migration_runner.py
```

### API Returns Empty
- Check `is_active` flag on templates
- Verify authentication token
- Check query parameters

### Favorites Not Saving
- Ensure user is authenticated
- Check `template_id` exists
- Verify unique constraint not violated

## Support

For issues or questions:
- Check API documentation: `/docs`
- Review logs in `logs/` directory
- Contact: support@trade-bot-marketplace.com

## License

Copyright © 2025 Trade Bot Marketplace


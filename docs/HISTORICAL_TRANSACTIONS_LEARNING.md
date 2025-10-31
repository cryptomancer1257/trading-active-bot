# Historical Transactions Learning Feature

## 🎯 Overview

Cho phép LLM học từ historical transactions của bot để cải thiện decision-making dựa trên past performance.

---

## 📊 **1. UI PLACEMENT RECOMMENDATION**

### ✅ **RECOMMENDED: TAB "STRATEGIES" (Best fit)**

**Lý do:**
- ✅ **Contextually relevant** - Strategies tab đã có Bot Prompts, thêm Historical Learning là logical
- ✅ **Bot developer only** - Chỉ developer có quyền config learning parameters
- ✅ **Natural flow** - Prompt → Historical Learning → Risk Management → Indicators
- ✅ **Not cluttered** - Tab này chưa quá đông, có thể thêm section mới

### Structure trong "Strategies" Tab:
```
╔══════════════════════════════════════════════════════════════════╗
║ 📊 STRATEGIES TAB                                                ║
╚══════════════════════════════════════════════════════════════════╝

1. **Bot Prompts Section** (existing)
   - Create/Edit custom prompts
   - Manage prompt templates

2. **Historical Learning Section** (NEW ✨)
   - Enable/Disable historical learning
   - Select number of past transactions to analyze
   - View recent transactions summary

3. **Learning Insights** (Future enhancement)
   - Win rate from historical data
   - Common patterns LLM learned
   - Performance metrics
```

### Alternative Options (Less ideal):

**Option B: New "Learning" Tab**
- ❌ Tạo thêm 1 tab mới → UI cluttered
- ✓ Clear separation of concerns

**Option C: "Settings" Tab**
- ❌ Settings tab quá generic
- ❌ Không liên quan đến trading logic

**Option D: "Risk Management" Tab**
- ❌ Risk Management focus vào SL/TP config
- ❌ Historical learning không phải risk parameter

---

## 💡 **2. SUGGESTED LEVELS FOR HISTORICAL DATA**

### **Recommended 3 Levels:**

```
╔══════════════════════════════════════════════════════════════════╗
║ 📈 HISTORICAL TRANSACTIONS LEARNING LEVELS                       ║
╚══════════════════════════════════════════════════════════════════╝

Level 1: MINIMAL (Last 10 transactions)
   • Use case: Quick context, minimal token usage
   • LLM context: ~2,000 tokens
   • Best for: High-frequency bots (many transactions/day)
   • Focus: Very recent patterns only

Level 2: BALANCED (Last 25 transactions) ⭐ RECOMMENDED
   • Use case: Good balance between context and cost
   • LLM context: ~5,000 tokens
   • Best for: Medium-frequency bots (daily signals)
   • Focus: Recent trends + some history

Level 3: COMPREHENSIVE (Last 50 transactions)
   • Use case: Deep learning from extensive history
   • LLM context: ~10,000 tokens
   • Best for: Low-frequency bots (swing trading)
   • Focus: Long-term patterns + edge cases
```

### **Why These Numbers?**

#### **10 Transactions (MINIMAL)**
```
Pros:
✓ Low token cost (~2K tokens)
✓ Very recent context
✓ Fast LLM processing
✓ Good for scalping/day trading

Cons:
✗ Limited pattern recognition
✗ May miss important trends
✗ Vulnerable to recent anomalies

Use case: Bot trades 5-10x/day
→ 10 transactions = last 1-2 days
```

#### **25 Transactions (BALANCED) ⭐**
```
Pros:
✓ Moderate token cost (~5K tokens)
✓ Captures weekly patterns
✓ Enough data for trend analysis
✓ Balances cost vs insight

Cons:
✗ May not cover all market conditions
✗ Medium token usage

Use case: Bot trades 1-3x/day
→ 25 transactions = last 1-2 weeks
```

#### **50 Transactions (COMPREHENSIVE)**
```
Pros:
✓ Rich historical context
✓ Covers multiple market cycles
✓ Better pattern recognition
✓ More robust decisions

Cons:
✗ Higher token cost (~10K tokens)
✗ May include outdated patterns
✗ Slower LLM processing

Use case: Bot trades 1x/2-3 days
→ 50 transactions = last 3-4 months
```

---

## 🎨 **3. UI DESIGN (Frontend)**

### Component Structure:

```typescript
// frontend/components/HistoricalLearningConfig.tsx

interface HistoricalLearningConfig {
  enabled: boolean
  transaction_limit: 10 | 25 | 50
  include_failed_trades: boolean
  learning_mode: 'recent' | 'best_performance' | 'mixed'
}

interface HistoricalLearningConfigProps {
  botId: number
  value: HistoricalLearningConfig
  onChange: (config: HistoricalLearningConfig) => void
}
```

### UI Mockup:

```
╔══════════════════════════════════════════════════════════════════╗
║ 🧠 HISTORICAL LEARNING CONFIGURATION                             ║
╚══════════════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────────────┐
│ 🔄 Enable Historical Learning                                   │
│                                                                  │
│ [✓] Learn from past transactions                                │
│                                                                  │
│ ℹ️  LLM will analyze recent transactions to improve decisions   │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 📊 Number of Transactions to Analyze                            │
│                                                                  │
│ ○ Minimal (10 transactions)                                     │
│   ~2K tokens · Best for high-frequency trading                  │
│                                                                  │
│ ● Balanced (25 transactions) ⭐ RECOMMENDED                      │
│   ~5K tokens · Good balance for daily signals                   │
│                                                                  │
│ ○ Comprehensive (50 transactions)                               │
│   ~10K tokens · Deep analysis for swing trading                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ ⚙️ Advanced Options                                             │
│                                                                  │
│ [✓] Include failed trades for learning                          │
│ [ ] Focus on best-performing trades only                        │
│                                                                  │
│ Learning Mode:                                                   │
│ ● Recent (time-ordered, most recent first)                      │
│ ○ Best Performance (sorted by profit)                           │
│ ○ Mixed (recent + top performers)                               │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 📈 Recent Transactions Summary                                  │
│                                                                  │
│ Last 25 Transactions:                                            │
│ • Win Rate: 68% (17 wins, 8 losses)                            │
│ • Avg Profit: +2.3%                                             │
│ • Avg Loss: -1.1%                                               │
│ • Total PnL: +$1,245.50                                         │
│                                                                  │
│ [View Full History →]                                           │
└────────────────────────────────────────────────────────────────┘

                    [💾 Save Configuration]
```

---

## 🗄️ **4. DATABASE SCHEMA**

### Option A: Add columns to `bots` table:

```sql
ALTER TABLE bots ADD COLUMN historical_learning_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE bots ADD COLUMN historical_transaction_limit INTEGER DEFAULT 25 
  CHECK (historical_transaction_limit IN (10, 25, 50));
ALTER TABLE bots ADD COLUMN include_failed_trades BOOLEAN DEFAULT TRUE;
ALTER TABLE bots ADD COLUMN learning_mode VARCHAR(20) DEFAULT 'recent'
  CHECK (learning_mode IN ('recent', 'best_performance', 'mixed'));
```

### Option B: Create new table (if more complex config needed):

```sql
CREATE TABLE bot_learning_config (
  id SERIAL PRIMARY KEY,
  bot_id INTEGER NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
  enabled BOOLEAN DEFAULT FALSE,
  transaction_limit INTEGER DEFAULT 25 CHECK (transaction_limit IN (10, 25, 50)),
  include_failed_trades BOOLEAN DEFAULT TRUE,
  learning_mode VARCHAR(20) DEFAULT 'recent',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(bot_id)
);

CREATE INDEX idx_bot_learning_config_bot_id ON bot_learning_config(bot_id);
```

**Recommendation:** Start with **Option A** (simpler), migrate to Option B if needed later.

---

## 🔧 **5. BACKEND IMPLEMENTATION**

### Query Recent Transactions:

```python
# services/transaction_service.py

class TransactionService:
    
    def get_recent_transactions_for_learning(
        self, 
        bot_id: int, 
        limit: int = 25,
        include_failed: bool = True,
        mode: str = 'recent'
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent transactions for LLM learning
        
        Args:
            bot_id: Bot ID
            limit: Number of transactions (10, 25, or 50)
            include_failed: Include losing trades
            mode: 'recent', 'best_performance', or 'mixed'
        
        Returns:
            List of transaction summaries
        """
        try:
            # Base query
            query = """
                SELECT 
                    t.id,
                    t.symbol,
                    t.side,
                    t.entry_price,
                    t.exit_price,
                    t.quantity,
                    t.profit_loss,
                    t.profit_loss_percentage,
                    t.stop_loss,
                    t.take_profit,
                    t.entry_timestamp,
                    t.exit_timestamp,
                    t.strategy,
                    t.timeframe,
                    t.indicators_used,
                    t.market_conditions,
                    s.bot_id
                FROM transactions t
                JOIN subscriptions s ON t.subscription_id = s.id
                WHERE s.bot_id = %s
                  AND t.exit_price IS NOT NULL  -- Only closed trades
            """
            
            # Filter by performance if needed
            if not include_failed:
                query += " AND t.profit_loss > 0"
            
            # Order by mode
            if mode == 'recent':
                query += " ORDER BY t.exit_timestamp DESC"
            elif mode == 'best_performance':
                query += " ORDER BY t.profit_loss_percentage DESC"
            elif mode == 'mixed':
                # 50% recent + 50% best performers
                query += " ORDER BY (CASE WHEN RANK() OVER (ORDER BY t.exit_timestamp DESC) <= %s THEN 1 ELSE 2 END), t.profit_loss_percentage DESC"
                limit_half = limit // 2
            
            query += f" LIMIT {limit}"
            
            with self.db.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    if mode == 'mixed':
                        cursor.execute(query, (bot_id, limit_half))
                    else:
                        cursor.execute(query, (bot_id,))
                    
                    transactions = cursor.fetchall()
                    
                    # Format for LLM
                    return self._format_transactions_for_llm(transactions)
        
        except Exception as e:
            logger.error(f"Error fetching transactions for learning: {e}")
            return []
    
    def _format_transactions_for_llm(self, transactions: List[Dict]) -> List[Dict]:
        """Format transactions into LLM-friendly structure"""
        formatted = []
        
        for t in transactions:
            # Calculate duration
            duration = None
            if t['exit_timestamp'] and t['entry_timestamp']:
                delta = t['exit_timestamp'] - t['entry_timestamp']
                duration = f"{delta.total_seconds() / 3600:.1f}h"
            
            formatted.append({
                'trade_id': t['id'],
                'symbol': t['symbol'],
                'side': t['side'],
                'entry_price': float(t['entry_price']),
                'exit_price': float(t['exit_price']),
                'profit_loss_pct': float(t['profit_loss_percentage']),
                'result': 'WIN' if t['profit_loss'] > 0 else 'LOSS',
                'strategy': t['strategy'],
                'timeframe': t['timeframe'],
                'duration': duration,
                'stop_loss': float(t['stop_loss']) if t['stop_loss'] else None,
                'take_profit': float(t['take_profit']) if t['take_profit'] else None,
                'indicators_used': t['indicators_used'],
                'market_conditions': t['market_conditions']
            })
        
        return formatted
```

---

## 📝 **6. LLM PROMPT INTEGRATION**

### Add Historical Section to Prompt:

```python
# In services/llm_integration.py

def _format_final_prompt(self, strategy_prompt: str, market_data: Dict, 
                         historical_transactions: List[Dict] = None) -> str:
    """
    Format final prompt with historical transactions if enabled
    """
    
    # Base sections (existing)
    base_prompt = f"""{strategy_prompt}

╔══════════════════════════════════════════════════════════════════╗
║ 📈 MARKET DATA TO ANALYZE                                        ║
╚══════════════════════════════════════════════════════════════════╝

{json.dumps(market_data, indent=2)}
"""
    
    # Add historical transactions if available
    if historical_transactions and len(historical_transactions) > 0:
        historical_section = self._format_historical_section(historical_transactions)
        base_prompt = base_prompt + "\n" + historical_section
    
    # Add recap
    base_prompt += """

═══════════════════════════════════════════════════════════════════
⚡ INSTRUCTIONS RECAP:
1. Extract indicators from data["indicators"][timeframe]
2. Analyze OHLCV patterns from data["timeframes"][timeframe]
3. LEARN from historical_transactions (if provided)
4. Apply YOUR STRATEGY rules
5. Return STRICT JSON format only
═══════════════════════════════════════════════════════════════════
"""
    
    return base_prompt

def _format_historical_section(self, transactions: List[Dict]) -> str:
    """Format historical transactions for LLM"""
    
    # Calculate statistics
    total = len(transactions)
    wins = sum(1 for t in transactions if t['result'] == 'WIN')
    losses = total - wins
    win_rate = (wins / total * 100) if total > 0 else 0
    
    avg_win = sum(t['profit_loss_pct'] for t in transactions if t['result'] == 'WIN') / wins if wins > 0 else 0
    avg_loss = sum(t['profit_loss_pct'] for t in transactions if t['result'] == 'LOSS') / losses if losses > 0 else 0
    
    section = f"""
╔══════════════════════════════════════════════════════════════════╗
║ 🧠 HISTORICAL TRANSACTIONS (Learn from Past Performance)        ║
╚══════════════════════════════════════════════════════════════════╝

📊 **Performance Summary** (Last {total} Trades):
   • Win Rate: {win_rate:.1f}% ({wins} wins, {losses} losses)
   • Avg Win: +{avg_win:.2f}%
   • Avg Loss: {avg_loss:.2f}%
   • Risk/Reward: {abs(avg_win/avg_loss):.2f}:1

🎯 **Key Learnings**:
   • Identify patterns from winning trades
   • Avoid conditions that led to losses
   • Consider market conditions when those trades were made
   • Use this history to improve current decision

📋 **Recent Transactions** (Most recent first):

"""
    
    # Add transaction details (limit to top 10 for prompt brevity)
    for i, t in enumerate(transactions[:10], 1):
        result_emoji = "✅" if t['result'] == 'WIN' else "❌"
        section += f"""
   {i}. {result_emoji} {t['side']} {t['symbol']} | {t['timeframe']}
      • Entry: ${t['entry_price']:.2f} → Exit: ${t['exit_price']:.2f}
      • PnL: {t['profit_loss_pct']:+.2f}% | Duration: {t['duration']}
      • Strategy: {t['strategy']}
      • Indicators: {', '.join(t['indicators_used'][:3]) if t['indicators_used'] else 'N/A'}
"""
    
    if total > 10:
        section += f"\n   ... and {total - 10} more transactions\n"
    
    section += """
⚠️ **CRITICAL**: Use this historical context to:
   1. Validate if current market conditions match past winners
   2. Avoid repeating mistakes from losing trades
   3. Adjust confidence based on similar past scenarios
   4. Consider if strategy performed well in similar conditions

"""
    
    return section
```

---

## 🔄 **7. INTEGRATION FLOW**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER CONFIGURES HISTORICAL LEARNING (Frontend)               │
│    • Enable/Disable                                              │
│    • Select limit (10/25/50)                                     │
│    • Choose mode (recent/best/mixed)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. CONFIGURATION SAVED TO DATABASE                               │
│    • Update bot.historical_learning_enabled = TRUE               │
│    • Update bot.historical_transaction_limit = 25                │
│    • Update bot.learning_mode = 'recent'                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. BOT EXECUTES TRADING LOGIC                                    │
│    • Fetch market data (OHLCV + indicators)                      │
│    • Check if historical_learning_enabled                        │
│    • If YES → Query recent transactions                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. QUERY TRANSACTIONS (TransactionService)                       │
│    • Get last N transactions (based on limit)                    │
│    • Filter by mode (recent/best/mixed)                          │
│    • Format for LLM                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. PASS TO LLM (LLMIntegrationService)                           │
│    • Strategy prompt                                             │
│    • Market data                                                 │
│    • Historical transactions ✨ NEW                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. LLM ANALYZES & RETURNS DECISION                               │
│    • Considers historical patterns                               │
│    • Learns from past mistakes                                   │
│    • Adjusts confidence based on similar scenarios               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💰 **8. TOKEN COST ESTIMATION**

| Level | Transactions | Avg Tokens | Cost per Call (GPT-4) | Calls/Month | Monthly Cost |
|-------|--------------|------------|------------------------|-------------|--------------|
| Minimal | 10 | ~2,000 | $0.04 | 1,000 | $40 |
| Balanced | 25 | ~5,000 | $0.10 | 1,000 | $100 |
| Comprehensive | 50 | ~10,000 | $0.20 | 1,000 | $200 |

**Note:** Costs based on GPT-4 Turbo ($0.01/1K input tokens, $0.03/1K output tokens)

---

## 📊 **9. EXPECTED IMPROVEMENTS**

### Before Historical Learning:
```json
{
  "action": "BUY",
  "confidence": "65",
  "reasoning": "RSI neutral, MACD bullish crossover"
}
```

### After Historical Learning (with context):
```json
{
  "action": "HOLD",
  "confidence": "70",
  "reasoning": "Despite bullish MACD, historical data shows 4/5 similar setups 
               with low volume failed. Wait for volume confirmation >150%."
}
```

**Key Benefits:**
- ✅ Learns from mistakes (avoid repeating losing patterns)
- ✅ Confirms winning strategies (more confident when similar to past winners)
- ✅ Adjusts to market conditions (recognizes when strategy works best)
- ✅ Improves over time (more historical data = better learning)

---

## 🚀 **10. IMPLEMENTATION STEPS**

### Phase 1: Database & Backend (Week 1)
1. ✅ Add columns to `bots` table (or create new table)
2. ✅ Implement `TransactionService.get_recent_transactions_for_learning`
3. ✅ Update bot queries to include historical config
4. ✅ Test transaction fetching with various modes

### Phase 2: LLM Integration (Week 1-2)
1. ✅ Update `_format_final_prompt` to include historical section
2. ✅ Implement `_format_historical_section`
3. ✅ Modify bot execution logic to fetch & pass transactions
4. ✅ Test with OpenAI/Claude/Gemini

### Phase 3: Frontend UI (Week 2)
1. ✅ Create `HistoricalLearningConfig` component
2. ✅ Add to "Strategies" tab (after Bot Prompts section)
3. ✅ Implement save/update functionality
4. ✅ Add transaction summary display

### Phase 4: Testing & Optimization (Week 3)
1. ✅ A/B test: bots with vs without historical learning
2. ✅ Monitor token usage & costs
3. ✅ Collect feedback from bot developers
4. ✅ Optimize prompt format based on results

---

## 📝 **11. MIGRATION SCRIPT**

```sql
-- Add columns to existing bots table
ALTER TABLE bots 
  ADD COLUMN IF NOT EXISTS historical_learning_enabled BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS historical_transaction_limit INTEGER DEFAULT 25 
    CHECK (historical_transaction_limit IN (10, 25, 50)),
  ADD COLUMN IF NOT EXISTS include_failed_trades BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS learning_mode VARCHAR(20) DEFAULT 'recent'
    CHECK (learning_mode IN ('recent', 'best_performance', 'mixed'));

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_transactions_subscription_exit 
  ON transactions(subscription_id, exit_timestamp DESC) 
  WHERE exit_price IS NOT NULL;

-- Default config for new bots
UPDATE bots SET 
  historical_learning_enabled = FALSE,
  historical_transaction_limit = 25,
  include_failed_trades = TRUE,
  learning_mode = 'recent'
WHERE historical_learning_enabled IS NULL;
```

---

## ✅ **RECOMMENDATION SUMMARY**

1. **UI Placement**: ✅ **"Strategies" tab** (after Bot Prompts section)

2. **3 Suggested Levels**:
   - ✅ **Level 1: Minimal (10 transactions)** - High-frequency trading
   - ✅ **Level 2: Balanced (25 transactions)** ⭐ **RECOMMENDED** - Daily signals
   - ✅ **Level 3: Comprehensive (50 transactions)** - Swing trading

3. **Implementation Priority**:
   - 🔥 **High**: Basic config (enable/disable, select limit)
   - 🔥 **High**: Query recent transactions
   - 🔥 **High**: Add to LLM prompt
   - 🟡 **Medium**: Advanced options (mode selection)
   - 🟢 **Low**: Learning insights dashboard

4. **Expected Timeline**: 2-3 weeks for full implementation

---

**Ready to implement?** 🚀

This feature will significantly improve bot performance by learning from historical patterns!


# Historical Learning Implementation Status

## ✅ COMPLETED (Phase 1 & 2A)

### 1. Database Schema ✅
**File:** `migrations/add_historical_learning_columns.sql`
- Added columns to `bots` table
- Created indexes for performance
- Set default values

### 2. Transaction Service ✅
**File:** `services/transaction_service.py`
- `get_recent_transactions_for_learning()` - Query transactions
- `_format_transactions_for_llm()` - Format for LLM
- `get_transaction_summary_stats()` - Calculate stats

### 3. LLM Integration (Partial) ✅
**File:** `services/llm_integration.py`
- ✅ `_format_historical_section()` - Format historical data for prompt
- ✅ Updated `_format_final_prompt()` to accept historical_transactions
- ✅ Updated `analyze_market()` signature

---

## 🔄 IN PROGRESS (Phase 2B)

### Update LLM Provider Methods

**Required Changes in `services/llm_integration.py`:**

#### 1. Update `analyze_with_openai()` signature (Line ~1479):
```python
# BEFORE:
async def analyze_with_openai(self, market_data: Dict[str, Any], bot_id: int = None) -> Dict[str, Any]:

# AFTER:
async def analyze_with_openai(self, market_data: Dict[str, Any], bot_id: int = None, 
                              historical_transactions: List[Dict] = None) -> Dict[str, Any]:
```

#### 2. Update `_format_final_prompt` call in `analyze_with_openai()` (Line ~1569):
```python
# BEFORE:
prompt = self._format_final_prompt(strategy_prompt, market_data)

# AFTER:
prompt = self._format_final_prompt(strategy_prompt, market_data, historical_transactions)
```

#### 3. Repeat for `analyze_with_claude()` and `analyze_with_gemini()`
Same pattern for both methods:
- Update signature to accept `historical_transactions: List[Dict] = None`
- Pass `historical_transactions` to `_format_final_prompt()`

#### 4. Update calls in `analyze_market()` (Lines ~1764-1768):
```python
# BEFORE:
analysis = await self._retry_with_backoff(self.analyze_with_openai, market_data, bot_id)

# AFTER:
analysis = await self._retry_with_backoff(self.analyze_with_openai, market_data, bot_id, historical_transactions)
```

---

## ⏳ TODO (Phase 2C & 3)

### Phase 2C: Bot Integration

#### Update Bot Files to Fetch & Pass Historical Transactions

**Files to Update:**
1. `bot_files/universal_futures_bot.py`
2. `bot_files/universal_spot_bot.py`
3. `bot_files/binance_signals_bot.py`
4. `bot_files/binance_trading_bot.py`
5. `bot_files/binance_futures_bot.py`

**Pattern to Add:**
```python
# In execute_algorithm() or equivalent method

# Import at top of file
from services.transaction_service import TransactionService

# Before calling LLM
historical_transactions = None
if hasattr(self, 'id') and self.id:
    # Check if historical learning enabled
    if self.historical_learning_enabled:
        transaction_service = TransactionService()
        historical_transactions = transaction_service.get_recent_transactions_for_learning(
            bot_id=self.id,
            limit=self.historical_transaction_limit or 25,
            include_failed=self.include_failed_trades,
            mode=self.learning_mode or 'recent'
        )
        
        if historical_transactions:
            logger.info(f"📚 Loaded {len(historical_transactions)} historical transactions for learning")

# Pass to LLM service
llm_response = await self.llm_service.analyze_market(
    symbol=symbol,
    timeframes_data=timeframes_data,
    indicators_analysis=indicators_analysis,
    model=self.llm_model,
    bot_id=self.id,
    historical_transactions=historical_transactions  # NEW!
)
```

---

### Phase 3: Frontend (2-3 days)

#### 1. Create Component
**File:** `frontend/components/HistoricalLearningConfig.tsx`

```typescript
'use client'

import { useState } from 'react'
import { CheckCircleIcon, InformationCircleIcon } from '@heroicons/react/24/outline'

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
  stats?: {
    total_trades: number
    win_rate: number
    avg_win: number
    avg_loss: number
    total_pnl: number
  }
}

export default function HistoricalLearningConfig({ 
  botId, 
  value, 
  onChange,
  stats 
}: HistoricalLearningConfigProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <InformationCircleIcon className="h-6 w-6 text-purple-600" />
          </div>
          <div className="ml-3">
            <h3 className="text-lg font-medium text-purple-900">
              🧠 Historical Learning
            </h3>
            <div className="mt-2 text-sm text-purple-700">
              <p>Enable LLM to learn from your bot's past transactions and avoid repeating mistakes.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Enable Toggle */}
      <div className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg">
        <div>
          <label className="text-sm font-medium text-gray-900">
            Enable Historical Learning
          </label>
          <p className="text-sm text-gray-500">
            LLM will analyze past transactions to improve decisions
          </p>
        </div>
        <button
          type="button"
          onClick={() => onChange({ ...value, enabled: !value.enabled })}
          className={`${
            value.enabled ? 'bg-purple-600' : 'bg-gray-200'
          } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2`}
        >
          <span
            className={`${
              value.enabled ? 'translate-x-5' : 'translate-x-0'
            } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out`}
          />
        </button>
      </div>

      {value.enabled && (
        <>
          {/* Transaction Limit Selector */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-900">
              Number of Transactions to Analyze
            </label>
            
            <div className="space-y-2">
              {[
                { value: 10, label: 'Minimal', desc: '~2K tokens · High-frequency trading', emoji: '🟢' },
                { value: 25, label: 'Balanced', desc: '~5K tokens · Daily signals', emoji: '🟡', recommended: true },
                { value: 50, label: 'Comprehensive', desc: '~10K tokens · Swing trading', emoji: '🔴' },
              ].map((option) => (
                <div
                  key={option.value}
                  onClick={() => onChange({ ...value, transaction_limit: option.value as 10 | 25 | 50 })}
                  className={`relative flex cursor-pointer rounded-lg border p-4 focus:outline-none ${
                    value.transaction_limit === option.value
                      ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-500'
                      : 'border-gray-300 bg-white hover:border-purple-300'
                  }`}
                >
                  <div className="flex flex-1">
                    <div className="flex items-center">
                      <input
                        type="radio"
                        checked={value.transaction_limit === option.value}
                        onChange={() => onChange({ ...value, transaction_limit: option.value as 10 | 25 | 50 })}
                        className="h-4 w-4 border-gray-300 text-purple-600 focus:ring-purple-500"
                      />
                    </div>
                    <div className="ml-3 flex flex-col">
                      <span className="text-sm font-medium text-gray-900">
                        {option.emoji} {option.label} ({option.value} transactions)
                        {option.recommended && (
                          <span className="ml-2 inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
                            ⭐ Recommended
                          </span>
                        )}
                      </span>
                      <span className="text-sm text-gray-500">{option.desc}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Performance Summary */}
          {stats && stats.total_trades > 0 && (
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <h4 className="text-sm font-medium text-gray-900 mb-3">
                📊 Recent Performance (Last {stats.total_trades} trades)
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Win Rate</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {stats.win_rate}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total P&L</p>
                  <p className={`text-lg font-semibold ${stats.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {stats.total_pnl >= 0 ? '+' : ''}{stats.total_pnl}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Avg Win</p>
                  <p className="text-lg font-semibold text-green-600">
                    +{stats.avg_win}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Avg Loss</p>
                  <p className="text-lg font-semibold text-red-600">
                    {stats.avg_loss}%
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Advanced Options (Optional) */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-purple-600 hover:text-purple-700 font-medium"
          >
            {showAdvanced ? '▼' : '▶'} Advanced Options
          </button>

          {showAdvanced && (
            <div className="space-y-3 pl-4 border-l-2 border-purple-200">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={value.include_failed_trades}
                  onChange={(e) => onChange({ ...value, include_failed_trades: e.target.checked })}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <label className="ml-2 text-sm text-gray-700">
                  Include failed trades for learning
                </label>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
```

#### 2. Add to Strategies Tab
**File:** `frontend/app/creator/entities/[id]/page.tsx`

In the `strategies` case of `renderContent()`, add after Bot Prompts section:

```typescript
case 'strategies':
  return (
    <>
      <BotPromptsTab botId={bot.id} />
      
      {/* Historical Learning Section */}
      <div className="mt-8">
        <HistoricalLearningConfig
          botId={bot.id}
          value={historicalLearningConfig || {
            enabled: false,
            transaction_limit: 25,
            include_failed_trades: true,
            learning_mode: 'recent'
          }}
          onChange={setHistoricalLearningConfig}
          stats={historicalStats}
        />
      </div>
    </>
  )
```

---

## 🗓️ **TIMELINE**

- ✅ **Phase 1: Database** (Complete)
- ✅ **Phase 2A: Backend Services** (Complete)  
- 🔄 **Phase 2B: LLM Integration** (60% complete - need to update 3 methods)
- ⏳ **Phase 2C: Bot Integration** (Not started - 5 bot files)
- ⏳ **Phase 3: Frontend** (Not started - 1-2 days)
- ⏳ **Phase 4: Testing** (Not started - 1-2 days)

**Estimated Remaining: 1.5 weeks**

---

## 🚀 **NEXT STEPS**

### Immediate (Continue Backend):
1. Update `analyze_with_openai()` signature + call
2. Update `analyze_with_claude()` signature + call
3. Update `analyze_with_gemini()` signature + call
4. Update 3 calls in `analyze_market()`
5. Test backend with mock data

### Then (Bot Integration):
1. Update 5 bot files to fetch/pass historical transactions
2. Test with real bot execution

### Finally (Frontend):
1. Create `HistoricalLearningConfig` component
2. Add to Strategies tab
3. Create save/load APIs
4. End-to-end testing

---

## 📋 **FILES CREATED**

1. ✅ `migrations/add_historical_learning_columns.sql`
2. ✅ `services/transaction_service.py`
3. 🔄 `services/llm_integration.py` (updated, needs 3 more method updates)
4. ⏳ `frontend/components/HistoricalLearningConfig.tsx` (need to create)

---

## 📖 **REFERENCES**

- Full Design: `docs/HISTORICAL_TRANSACTIONS_LEARNING.md`
- Quick Start: `docs/HISTORICAL_LEARNING_QUICK_START.md`
- Visual Guide: `docs/HISTORICAL_LEARNING_VISUAL_GUIDE.txt`

---

**Status:** ~40% Complete | Continue with Phase 2B LLM method updates


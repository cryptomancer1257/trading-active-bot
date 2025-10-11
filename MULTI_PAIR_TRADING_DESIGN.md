# 🔄 Multi-Pair Trading Support - Design Document

## 📋 Executive Summary

**Current State**: Universal Futures Bot supports **1 trading pair** per subscription
**Target State**: Support **multiple trading pairs** (e.g., BTC, ETH, SOL) trong cùng 1 bot subscription

**Complexity Level**: 🟡 Medium (cần thay đổi nhiều component nhưng logic cơ bản giữ nguyên)

---

## 🎯 1. ARCHITECTURE CHANGES

### 1.1 Current Flow (Single Pair)
```
User subscribes → 1 Bot → 1 Trading Pair → 1 Position
```

### 1.2 New Flow (Multi Pair)
```
User subscribes → 1 Bot → Multiple Trading Pairs → Multiple Positions
                              ↓
                    Portfolio Management Layer
                              ↓
                    [BTC] [ETH] [SOL] ...
```

---

## 🔧 2. CODE CHANGES NEEDED

### 2.1 Configuration Changes

#### **File: `bot_files/universal_futures_bot.py`**

**Current:**
```python
self.trading_pair = config.get('trading_pair', 'BTCUSDT')
```

**New:**
```python
# Support both single and multiple pairs
trading_pairs_input = config.get('trading_pairs', config.get('trading_pair', 'BTCUSDT'))

if isinstance(trading_pairs_input, str):
    # Single pair: "BTCUSDT" or "BTC,ETH,SOL"
    self.trading_pairs = [p.strip().replace('/', '') for p in trading_pairs_input.split(',')]
else:
    # List of pairs: ["BTCUSDT", "ETHUSDT"]
    self.trading_pairs = [p.replace('/', '') for p in trading_pairs_input]

# New portfolio settings
self.max_concurrent_positions = config.get('max_concurrent_positions', 3)
self.allocation_strategy = config.get('allocation_strategy', 'equal')  # equal, weighted, dynamic
self.per_pair_allocation = config.get('per_pair_allocation', {})  # Custom allocation per pair

logger.info(f"✅ Multi-pair trading enabled: {self.trading_pairs}")
logger.info(f"   Max Concurrent Positions: {self.max_concurrent_positions}")
```

**Impact**: 🟢 Low - Backward compatible (single pair vẫn hoạt động)

---

### 2.2 Data Crawling Changes

#### **Method: `crawl_data()`**

**Current:** Crawl 1 pair cho multiple timeframes
```python
def crawl_data(self) -> Dict[str, Any]:
    # Returns: {"timeframes": {"1h": [...], "4h": [...]}}
```

**New:** Crawl multiple pairs, mỗi pair có multiple timeframes
```python
def crawl_data(self) -> Dict[str, Any]:
    """
    Crawl data for multiple trading pairs in parallel
    Returns: {
        "pairs": {
            "BTCUSDT": {"timeframes": {"1h": [...], "4h": [...]}},
            "ETHUSDT": {"timeframes": {"1h": [...], "4h": [...]}},
            ...
        },
        "crawl_timestamp": "...",
        "total_pairs": 2
    }
    """
    import concurrent.futures
    
    pairs_data = {}
    
    def crawl_single_pair(pair: str) -> tuple:
        """Crawl data for one pair"""
        try:
            logger.info(f"📊 Crawling {pair}...")
            # Use existing crawl logic but for single pair
            timeframes_data = {}
            
            for timeframe in self.timeframes:
                df = CLIENT.get_klines(
                    symbol=pair,
                    interval=timeframe,
                    start_time=start_time,
                    end_time=end_time,
                    limit=lookback
                )
                timeframes_data[timeframe] = _df_to_records(df)
            
            return (pair, {
                "timeframes": timeframes_data,
                "success": True
            })
        except Exception as e:
            logger.error(f"❌ Failed to crawl {pair}: {e}")
            return (pair, {
                "timeframes": {},
                "success": False,
                "error": str(e)
            })
    
    # Parallel crawling for efficiency
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(crawl_single_pair, pair): pair 
                  for pair in self.trading_pairs}
        
        for future in concurrent.futures.as_completed(futures):
            pair, data = future.result()
            pairs_data[pair] = data
    
    successful_pairs = [p for p, d in pairs_data.items() if d.get('success')]
    logger.info(f"✅ Crawled {len(successful_pairs)}/{len(self.trading_pairs)} pairs successfully")
    
    return {
        "pairs": pairs_data,
        "crawl_timestamp": datetime.now().isoformat(),
        "total_pairs": len(self.trading_pairs),
        "successful_pairs": len(successful_pairs)
    }
```

**Impact**: 🟡 Medium - Cần refactor crawl logic, thêm parallel processing

---

### 2.3 Analysis Changes

#### **Method: `analyze_data()`**

**Current:** Analyze 1 pair
```python
def analyze_data(self, multi_timeframe_data: Dict[str, Any]) -> Dict[str, Any]:
    # Analyze single pair's timeframes
```

**New:** Analyze multiple pairs
```python
def analyze_data(self, multi_pair_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze multiple pairs with multi-timeframe data
    Returns: {
        "pairs": {
            "BTCUSDT": {
                "multi_timeframe": {...},
                "primary_analysis": {...},
                "current_price": 50000
            },
            "ETHUSDT": {...}
        }
    }
    """
    pairs_data = multi_pair_data.get("pairs", {})
    pairs_analysis = {}
    
    for pair, pair_data in pairs_data.items():
        if not pair_data.get('success'):
            pairs_analysis[pair] = {'error': pair_data.get('error')}
            continue
        
        try:
            # Use existing analysis logic per pair
            timeframes_data = pair_data.get("timeframes", {})
            multi_analysis = {}
            
            for timeframe, historical_data in timeframes_data.items():
                df = pd.DataFrame(historical_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.set_index('timestamp')
                
                timeframe_analysis = self._calculate_futures_analysis(df, historical_data)
                multi_analysis[timeframe] = timeframe_analysis
            
            primary_analysis = multi_analysis.get(self.primary_timeframe, {})
            
            pairs_analysis[pair] = {
                'multi_timeframe': multi_analysis,
                'primary_analysis': primary_analysis,
                'current_price': primary_analysis.get('current_price', 0)
            }
            
            logger.info(f"✅ Analyzed {pair}: ${primary_analysis.get('current_price', 0):.2f}")
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze {pair}: {e}")
            pairs_analysis[pair] = {'error': str(e)}
    
    return {
        "pairs": pairs_analysis,
        "analysis_timestamp": datetime.now().isoformat()
    }
```

**Impact**: 🟡 Medium - Cần loop qua từng pair

---

### 2.4 Signal Generation Changes

#### **Method: `generate_signal()`**

**Current:** Generate 1 signal cho 1 pair

**New:** Generate signals cho tất cả pairs
```python
def generate_signals(self, analysis: Dict[str, Any]) -> List[Tuple[str, Action]]:
    """
    Generate trading signals for all pairs
    Returns: List of (pair, signal) tuples sorted by confidence
    """
    pairs_analysis = analysis.get('pairs', {})
    signals = []
    
    for pair, pair_analysis in pairs_analysis.items():
        if 'error' in pair_analysis:
            logger.warning(f"⚠️ Skipping {pair}: {pair_analysis['error']}")
            continue
        
        try:
            # Generate signal for this pair using existing logic
            if self.use_llm_analysis and self.llm_service:
                # LLM analysis for this pair
                signal = asyncio.run(self._generate_llm_signal_for_pair(
                    pair=pair,
                    timeframes_data=pair_analysis.get('timeframes_data', {})
                ))
            else:
                # Technical analysis for this pair
                primary_analysis = pair_analysis.get('primary_analysis', {})
                primary_df = pd.DataFrame({'close': [primary_analysis.get('current_price', 50000)]})
                signal = self._generate_technical_signal(primary_analysis, primary_df)
            
            signals.append((pair, signal))
            logger.info(f"🎯 {pair}: {signal.action} (confidence: {signal.value*100:.1f}%)")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate signal for {pair}: {e}")
    
    # Sort by confidence (highest first)
    signals.sort(key=lambda x: x[1].value, reverse=True)
    
    logger.info(f"✅ Generated {len(signals)} signals")
    return signals
```

**Impact**: 🟡 Medium - Cần refactor để return multiple signals

---

### 2.5 Position Management Changes

#### **New Method: `check_portfolio_status()`**

```python
def check_portfolio_status(self) -> Dict[str, Any]:
    """
    Check portfolio-level status across all pairs
    Returns:
        - total_positions: Number of open positions across all pairs
        - positions_by_pair: Dict of positions per pair
        - total_exposure: Total notional value of all positions
        - available_slots: How many more positions can be opened
        - portfolio_risk: Current portfolio risk level
    """
    try:
        # Get all positions
        all_positions = self.futures_client.get_positions()
        
        # Filter positions for our trading pairs
        our_positions = [p for p in all_positions 
                        if p.symbol.replace('USDT', '') in [pair.replace('USDT', '') for pair in self.trading_pairs]
                        and float(p.size) != 0]
        
        # Group by pair
        positions_by_pair = {}
        total_exposure = 0
        
        for pos in our_positions:
            pair = pos.symbol
            notional = abs(float(pos.size) * float(pos.entry_price))
            total_exposure += notional
            
            positions_by_pair[pair] = {
                'size': float(pos.size),
                'entry_price': float(pos.entry_price),
                'notional': notional,
                'pnl': float(pos.unrealized_pnl) if hasattr(pos, 'unrealized_pnl') else 0
            }
        
        # Check risk config limits
        account_info = self.futures_client.get_account_info()
        total_balance = float(account_info.get('totalWalletBalance', 0))
        
        portfolio_exposure_pct = (total_exposure / total_balance * 100) if total_balance > 0 else 0
        available_slots = max(0, self.max_concurrent_positions - len(our_positions))
        
        logger.info(f"📊 Portfolio Status:")
        logger.info(f"   Open Positions: {len(our_positions)}/{self.max_concurrent_positions}")
        logger.info(f"   Total Exposure: ${total_exposure:,.2f} ({portfolio_exposure_pct:.1f}%)")
        logger.info(f"   Available Slots: {available_slots}")
        
        return {
            'total_positions': len(our_positions),
            'positions_by_pair': positions_by_pair,
            'total_exposure': total_exposure,
            'portfolio_exposure_pct': portfolio_exposure_pct,
            'available_slots': available_slots,
            'total_balance': total_balance
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to check portfolio status: {e}")
        return {
            'total_positions': 0,
            'positions_by_pair': {},
            'total_exposure': 0,
            'available_slots': self.max_concurrent_positions
        }
```

**Impact**: 🔴 High - Hoàn toàn mới, cần test kỹ

---

### 2.6 Execution Flow Changes

#### **New Method: `execute_multi_pair_strategy()`**

```python
async def execute_multi_pair_strategy(self, subscription=None) -> Dict[str, Any]:
    """
    Main execution flow for multi-pair trading
    
    Flow:
    1. Check portfolio status
    2. Crawl data for all pairs
    3. Analyze all pairs
    4. Generate signals for all pairs
    5. Rank signals by confidence
    6. Check risk limits
    7. Execute top N signals (respect max_concurrent_positions)
    """
    try:
        logger.info("=" * 80)
        logger.info("🚀 MULTI-PAIR STRATEGY EXECUTION START")
        logger.info("=" * 80)
        
        # Step 1: Check current portfolio
        portfolio = self.check_portfolio_status()
        available_slots = portfolio['available_slots']
        
        if available_slots == 0:
            logger.info("⏸️ Portfolio full - no available slots")
            return {
                'status': 'info',
                'action': 'HOLD',
                'reason': f'Max positions reached ({self.max_concurrent_positions})',
                'portfolio': portfolio
            }
        
        logger.info(f"✅ Available slots: {available_slots}")
        
        # Step 2: Crawl data for all pairs
        multi_pair_data = self.crawl_data()
        
        # Step 3: Analyze all pairs
        analysis = self.analyze_data(multi_pair_data)
        
        # Step 4: Generate signals for all pairs
        signals = self.generate_signals(analysis)
        
        if not signals:
            logger.info("ℹ️ No trading signals generated")
            return {
                'status': 'info',
                'action': 'HOLD',
                'reason': 'No signals',
                'portfolio': portfolio
            }
        
        # Step 5: Filter signals - skip pairs with existing positions
        existing_pairs = set(portfolio['positions_by_pair'].keys())
        new_signals = [(pair, signal) for pair, signal in signals 
                       if pair not in existing_pairs and signal.action in ['BUY', 'SELL']]
        
        logger.info(f"🎯 New signals: {len(new_signals)}")
        for pair, signal in new_signals[:5]:  # Show top 5
            logger.info(f"   {pair}: {signal.action} ({signal.value*100:.1f}%)")
        
        # Step 6: Check risk limits from risk_config
        if subscription and hasattr(subscription, 'bot') and hasattr(subscription.bot, 'risk_config'):
            risk_config_dict = subscription.bot.risk_config
            if risk_config_dict:
                from core import schemas
                risk_config = schemas.RiskConfig(**risk_config_dict)
                
                # Check max_portfolio_exposure
                if risk_config.max_portfolio_exposure:
                    current_exposure = portfolio['portfolio_exposure_pct']
                    if current_exposure >= risk_config.max_portfolio_exposure:
                        logger.warning(f"⚠️ Portfolio exposure limit reached: {current_exposure:.1f}% >= {risk_config.max_portfolio_exposure}%")
                        return {
                            'status': 'info',
                            'action': 'HOLD',
                            'reason': f'Portfolio exposure limit reached ({current_exposure:.1f}%)',
                            'portfolio': portfolio
                        }
        
        # Step 7: Execute top N signals (limited by available slots)
        signals_to_execute = new_signals[:available_slots]
        
        if not signals_to_execute:
            logger.info("ℹ️ No new signals to execute")
            return {
                'status': 'info',
                'action': 'HOLD',
                'reason': 'All signals filtered out or positions already exist',
                'portfolio': portfolio
            }
        
        logger.info(f"🚀 Executing {len(signals_to_execute)} signal(s)...")
        
        results = []
        for pair, signal in signals_to_execute:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"📈 Executing {signal.action} for {pair}")
                logger.info(f"{'='*60}")
                
                # Temporarily set trading_pair for setup_position
                original_pair = self.trading_pair
                self.trading_pair = pair
                
                # Get analysis for this pair
                pair_analysis = analysis['pairs'][pair]
                
                # Execute position setup
                trade_result = await self.setup_position(signal, pair_analysis, subscription)
                
                # Restore original trading_pair
                self.trading_pair = original_pair
                
                trade_result['pair'] = pair
                results.append(trade_result)
                
                logger.info(f"✅ {pair}: {trade_result.get('status')}")
                
            except Exception as e:
                logger.error(f"❌ Failed to execute {pair}: {e}")
                results.append({
                    'pair': pair,
                    'status': 'error',
                    'message': str(e)
                })
        
        logger.info("=" * 80)
        logger.info("✅ MULTI-PAIR STRATEGY EXECUTION COMPLETE")
        logger.info("=" * 80)
        
        return {
            'status': 'success',
            'action': 'MULTI_PAIR_EXECUTION',
            'pairs_executed': len(results),
            'results': results,
            'portfolio': portfolio
        }
        
    except Exception as e:
        logger.error(f"❌ Multi-pair execution error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'message': str(e)
        }
```

**Impact**: 🔴 High - Core execution logic mới hoàn toàn

---

## 🗄️ 3. DATABASE CHANGES

### 3.1 Schema Changes

**Current `bots` table:**
```sql
CREATE TABLE bots (
    ...
    trading_pair VARCHAR(20),  -- Single pair
    ...
);
```

**New schema - Option 1: JSON field (Recommended)**
```sql
ALTER TABLE bots 
ADD COLUMN trading_pairs JSON DEFAULT NULL 
COMMENT 'List of trading pairs for multi-pair bots';

-- Example data:
-- trading_pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

ALTER TABLE bots
ADD COLUMN max_concurrent_positions INT DEFAULT 1 
COMMENT 'Max number of positions across all pairs';

ALTER TABLE bots
ADD COLUMN allocation_strategy VARCHAR(20) DEFAULT 'equal'
COMMENT 'Capital allocation strategy: equal, weighted, dynamic';
```

**New schema - Option 2: Separate table (More flexible)**
```sql
CREATE TABLE bot_trading_pairs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bot_id INT NOT NULL,
    trading_pair VARCHAR(20) NOT NULL,
    allocation_percent DECIMAL(5,2) DEFAULT NULL COMMENT 'Custom allocation %',
    priority INT DEFAULT 0 COMMENT 'Trading priority',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    UNIQUE KEY unique_bot_pair (bot_id, trading_pair)
);
```

**Recommendation**: 🟢 Use **Option 1 (JSON)** for simplicity, migrate to Option 2 if need advanced features

---

### 3.2 Migration Script

```sql
-- Migration: Add multi-pair support
-- File: migrations/versions/018_multi_pair_support.sql

-- Add new columns to bots table
ALTER TABLE bots 
ADD COLUMN trading_pairs JSON DEFAULT NULL 
COMMENT 'List of trading pairs ["BTCUSDT", "ETHUSDT"]';

ALTER TABLE bots
ADD COLUMN max_concurrent_positions INT DEFAULT 1 
COMMENT 'Max simultaneous positions across all pairs';

ALTER TABLE bots
ADD COLUMN allocation_strategy VARCHAR(20) DEFAULT 'equal'
COMMENT 'equal, weighted, dynamic';

-- Migrate existing data
UPDATE bots 
SET trading_pairs = JSON_ARRAY(trading_pair)
WHERE trading_pair IS NOT NULL AND trading_pairs IS NULL;

-- Add index for performance
CREATE INDEX idx_bots_trading_pairs ON bots(trading_pairs(255));

-- Transactions table already has 'symbol' field, no changes needed
-- SELECT * FROM transactions WHERE symbol IN ('BTCUSDT', 'ETHUSDT');
```

---

## 🛡️ 4. RISK MANAGEMENT CHANGES

### 4.1 Enhanced Risk Config

**File: `core/schemas.py`**

```python
class RiskConfig(BaseModel):
    # ... existing fields ...
    
    # NEW: Multi-pair risk management
    max_portfolio_exposure: Optional[float] = Field(
        None, 
        gt=0, 
        le=100, 
        description="Max total exposure across ALL pairs (%)"
    )
    
    max_concurrent_positions: Optional[int] = Field(
        None,
        gt=0,
        le=10,
        description="Max number of simultaneous positions"
    )
    
    per_pair_max_exposure: Optional[float] = Field(
        None,
        gt=0,
        le=50,
        description="Max exposure per individual pair (%)"
    )
    
    correlation_limit: Optional[float] = Field(
        None,
        gt=-1,
        lt=1,
        description="Avoid opening highly correlated pairs (e.g., 0.8)"
    )
```

### 4.2 Portfolio Risk Checks

```python
def apply_portfolio_risk_management(portfolio_status, new_signal, risk_config):
    """
    Check portfolio-level risk before opening new position
    """
    # 1. Check max concurrent positions
    if portfolio_status['total_positions'] >= risk_config.max_concurrent_positions:
        return False, "Max concurrent positions reached"
    
    # 2. Check portfolio exposure
    account_balance = portfolio_status['total_balance']
    current_exposure = portfolio_status['total_exposure']
    new_position_size = calculate_position_size(new_signal, account_balance)
    
    total_exposure_after = (current_exposure + new_position_size) / account_balance * 100
    
    if total_exposure_after > risk_config.max_portfolio_exposure:
        return False, f"Portfolio exposure limit: {total_exposure_after:.1f}% > {risk_config.max_portfolio_exposure}%"
    
    # 3. Check per-pair exposure (if already have position in this pair)
    if new_signal.pair in portfolio_status['positions_by_pair']:
        return False, "Already have position in this pair"
    
    # 4. Check daily loss limit (portfolio-wide)
    # ... existing logic ...
    
    return True, "Portfolio risk checks passed"
```

---

## 📊 5. CAPITAL MANAGEMENT CHANGES

### 5.1 Capital Allocation

```python
class PortfolioCapitalManager:
    """
    Manages capital allocation across multiple pairs
    """
    
    def calculate_allocations(
        self,
        available_balance: float,
        signals: List[Tuple[str, Action]],
        allocation_strategy: str,
        max_concurrent: int
    ) -> Dict[str, float]:
        """
        Allocate capital to signals based on strategy
        
        Strategies:
        - equal: Divide equally (e.g., 3 pairs → 33.33% each)
        - weighted: Based on confidence scores
        - dynamic: Based on volatility & correlation
        """
        allocations = {}
        
        if allocation_strategy == 'equal':
            # Equal allocation
            per_pair_pct = 1.0 / min(len(signals), max_concurrent)
            for pair, signal in signals[:max_concurrent]:
                allocations[pair] = available_balance * per_pair_pct
        
        elif allocation_strategy == 'weighted':
            # Weight by confidence
            total_confidence = sum(signal.value for _, signal in signals[:max_concurrent])
            for pair, signal in signals[:max_concurrent]:
                weight = signal.value / total_confidence if total_confidence > 0 else 0
                allocations[pair] = available_balance * weight
        
        elif allocation_strategy == 'dynamic':
            # Consider volatility and correlation
            # Lower volatility → higher allocation
            # High correlation → reduce allocation
            pass  # TODO: Implement
        
        return allocations
```

---

## 🧪 6. TESTING STRATEGY

### 6.1 Unit Tests

```python
# tests/bot_trading/test_multi_pair_bot.py

def test_multi_pair_config():
    """Test multi-pair configuration"""
    config = {
        'trading_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
        'max_concurrent_positions': 3,
        'allocation_strategy': 'equal'
    }
    bot = UniversalFuturesBot(config, user_principal_id='test')
    assert len(bot.trading_pairs) == 3
    assert bot.max_concurrent_positions == 3

def test_portfolio_status():
    """Test portfolio status checking"""
    # Mock positions
    # Check that it correctly counts positions per pair

def test_signal_generation_multi_pair():
    """Test signal generation for multiple pairs"""
    # Should return list of (pair, signal) tuples

def test_position_limit_enforcement():
    """Test that bot respects max_concurrent_positions"""
    # Portfolio has 3 positions
    # New signal should be rejected if limit is 3
```

### 6.2 Integration Tests

```python
def test_multi_pair_full_cycle():
    """
    Test complete multi-pair trading cycle:
    1. Crawl 3 pairs
    2. Analyze 3 pairs
    3. Generate signals for all
    4. Execute top 2 (if max_concurrent=2)
    5. Verify positions opened correctly
    """
```

---

## ⚠️ 7. POTENTIAL ISSUES & MITIGATIONS

### 7.1 Performance Issues

**Problem**: Crawling 10 pairs × 3 timeframes = 30 API calls
- **Solution**: Parallel crawling with ThreadPoolExecutor (max_workers=5)
- **Fallback**: Cache data for 1 minute

### 7.2 LLM Cost Explosion

**Problem**: LLM analysis cho 10 pairs = 10x cost
- **Solution 1**: Only use LLM for top 3 highest volatility pairs
- **Solution 2**: Cache LLM results longer (5 minutes instead of 1)
- **Solution 3**: Use technical analysis for pre-filtering, LLM for final decision

### 7.3 Race Conditions

**Problem**: Multiple Celery workers executing same bot simultaneously
- **Solution**: Redis distributed lock per subscription (already exists)
- **Enhancement**: Lock per pair for finer granularity

### 7.4 Capital Fragmentation

**Problem**: Capital spread too thin across many pairs
- **Solution**: Enforce minimum position size from risk_config
- **Solution**: Use `max_concurrent_positions` to limit spread

### 7.5 Correlation Risk

**Problem**: Opening BTC + ETH (highly correlated) = 2x same direction exposure
- **Solution**: Implement correlation matrix check
- **Solution**: Add `correlation_limit` to risk_config

---

## 🚀 8. IMPLEMENTATION PHASES

### Phase 1: Foundation (Week 1)
- ✅ Update bot config to accept `trading_pairs` (JSON)
- ✅ Database migration (add `trading_pairs`, `max_concurrent_positions`)
- ✅ Update `crawl_data()` for multi-pair (parallel)
- ✅ Update `analyze_data()` for multi-pair
- ✅ Basic unit tests

### Phase 2: Core Logic (Week 2)
- ✅ Implement `check_portfolio_status()`
- ✅ Implement `generate_signals()` (multi-pair)
- ✅ Implement `execute_multi_pair_strategy()`
- ✅ Update `core/tasks.py` to call new execution method
- ✅ Integration tests

### Phase 3: Risk & Capital Management (Week 3)
- ✅ Enhance `RiskConfig` with portfolio-level limits
- ✅ Implement `apply_portfolio_risk_management()`
- ✅ Implement `PortfolioCapitalManager`
- ✅ Add portfolio-level daily loss tracking

### Phase 4: Frontend & UX (Week 4)
- ✅ Update "Forge New Bot" form to accept multiple pairs
- ✅ Add UI for `max_concurrent_positions` setting
- ✅ Portfolio dashboard showing all pairs + positions
- ✅ Per-pair performance metrics

### Phase 5: Optimization (Week 5)
- ✅ LLM cost optimization (caching, selective usage)
- ✅ Correlation detection & prevention
- ✅ Dynamic allocation strategies
- ✅ Performance monitoring & alerts

---

## 📝 9. BACKWARD COMPATIBILITY

**Critical**: Ensure existing single-pair bots continue working!

```python
# In __init__:
trading_pairs_input = config.get('trading_pairs', config.get('trading_pair', 'BTCUSDT'))

if isinstance(trading_pairs_input, str):
    if ',' in trading_pairs_input:
        # Multi-pair: "BTC,ETH,SOL"
        self.trading_pairs = [p.strip().replace('/', '') for p in trading_pairs_input.split(',')]
    else:
        # Single pair: "BTCUSDT"
        self.trading_pairs = [trading_pairs_input.replace('/', '')]
else:
    # List: ["BTCUSDT", "ETHUSDT"]
    self.trading_pairs = [p.replace('/', '') for p in trading_pairs_input]

# For single-pair bots, use legacy execution path
if len(self.trading_pairs) == 1:
    self.trading_pair = self.trading_pairs[0]  # Maintain legacy field
    # Use existing execute_algorithm() method
else:
    # Use new multi-pair execution
    self.trading_pair = self.trading_pairs[0]  # Set first as default for compatibility
```

---

## 🎯 10. SUCCESS METRICS

- ✅ Single-pair bots still work (0 regressions)
- ✅ Multi-pair bots can trade 3+ pairs simultaneously
- ✅ Portfolio exposure correctly calculated across all pairs
- ✅ Max concurrent positions enforced
- ✅ API call latency < 30s for 5 pairs × 3 timeframes
- ✅ LLM cost increase < 2x (with caching & optimization)

---

## 📚 11. DOCUMENTATION NEEDS

1. **Developer Guide**: How to implement multi-pair bots
2. **User Guide**: How to configure multi-pair trading
3. **API Reference**: New methods and fields
4. **Migration Guide**: Updating existing bots to multi-pair

---

## ❓ 12. OPEN QUESTIONS FOR REVIEW

1. **Capital Allocation**: Equal vs Weighted vs Dynamic - which default?
2. **LLM Usage**: Analyze all pairs or only top N by volatility?
3. **Position Closing**: Close all positions when daily loss limit hit?
4. **Rebalancing**: Should bot rebalance capital across pairs periodically?
5. **Correlation**: Calculate real-time or use pre-defined matrix?

---

## 🔄 13. ALTERNATIVE APPROACHES

### Approach A: Full Multi-Pair (This Document)
- Pros: Maximum flexibility, portfolio optimization
- Cons: Complex, more API calls, higher LLM cost

### Approach B: "Pair Rotation"
- Trade 1 pair at a time, rotate based on signals
- Pros: Simple, same API usage as single-pair
- Cons: Miss opportunities in other pairs

### Approach C: "Hot Pair Selection"
- Each cycle, select 1 "best" pair to trade
- Use volatility + volume to pick
- Pros: Low cost, focused
- Cons: Less diversification

**Recommendation**: Start with **Approach A** for advanced users, offer **Approach C** as "Simple Mode"

---

## 🎬 CONCLUSION

**Complexity Assessment**: 🟡 Medium-High
- Core logic changes: ~1500 LOC
- Database changes: Minimal
- Frontend changes: Moderate
- Testing effort: High

**Timeline**: 4-5 weeks for full implementation

**Risk Level**: Medium (careful testing needed for portfolio management)

**Business Value**: High (differentiator, institutional-grade feature)

---

## 📋 NEXT STEPS

1. **Review this document** with team
2. **Decide on Phase 1 scope** (foundation only or include core logic?)
3. **Create Jira tickets** for each phase
4. **Prototype** multi-pair data crawling (1-2 days)
5. **User feedback** on allocation strategies

---

**Document Version**: 1.0
**Last Updated**: 2025-10-10
**Author**: AI Assistant
**Status**: 📝 Draft - Awaiting Review


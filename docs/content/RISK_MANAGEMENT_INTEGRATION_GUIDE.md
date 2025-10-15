# 🔧 Risk Management Integration Guide

## Quick Integration vào Bot Execution

Hướng dẫn tích hợp Risk Management System vào bot execution flows hiện có.

## 📝 Bước 1: Import Services

```python
from services.risk_integration import apply_risk_to_signal, record_trade, is_trading_allowed
```

## 🚀 Bước 2: Áp dụng trong `run_bot_logic()` Task

### A. Kiểm tra Trading Allowed (Optional - Quick Check)

```python
# Ở đầu task, kiểm tra nhanh xem có được phép trade không
allowed, reason = is_trading_allowed(db, subscription_id)
if not allowed:
    logger.info(f"⏸️ Trading paused: {reason}")
    crud.log_bot_action(db, subscription_id, "PAUSED", reason)
    return {
        'status': 'paused',
        'reason': reason
    }
```

### B. Áp dụng Risk Management vào Signal

```python
# Sau khi có signal từ bot
signal = await bot.generate_signal(historical_data)

if signal.action in ["BUY", "SELL"]:
    # Prepare data for risk evaluation
    signal_data = {
        'action': signal.action,
        'entry_price': entry_price,
        'stop_loss': stop_loss_target,
        'take_profit': take_profit_target,
        'confidence': signal.value
    }
    
    market_data = {
        'current_price': entry_price,
        'volatility': analysis.get('volatility', 0.05),
        'trend': analysis.get('trend', 'NEUTRAL'),
        'volume': analysis.get('volume', 0)
    }
    
    # Apply risk management
    approved, enhanced_signal, reason = apply_risk_to_signal(
        db=db,
        subscription_id=subscription_id,
        signal=signal_data,
        market_data=market_data,
        account_info=account_info
    )
    
    if not approved:
        logger.warning(f"❌ Trade rejected by risk management: {reason}")
        crud.log_bot_action(
            db, subscription_id, "REJECTED",
            f"Risk management blocked trade: {reason}"
        )
        return {
            'status': 'rejected',
            'reason': reason
        }
    
    # Log warnings if any
    if enhanced_signal.get('risk_warnings'):
        for warning in enhanced_signal['risk_warnings']:
            logger.warning(f"⚠️ Risk warning: {warning}")
    
    # Use enhanced parameters
    stop_loss = enhanced_signal.get('stop_loss', stop_loss_target)
    take_profit = enhanced_signal.get('take_profit', take_profit_target)
    position_size_pct = enhanced_signal.get('position_size_pct', optimal_position_size_pct)
    max_leverage = enhanced_signal.get('max_leverage', leverage)
    
    logger.info(f"✅ Risk management approved trade")
    logger.info(f"   Mode: {subscription.risk_management_mode}")
    logger.info(f"   Position Size: {position_size_pct:.2f}%")
    logger.info(f"   Max Leverage: {max_leverage}x")
    logger.info(f"   SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}")
    if enhanced_signal.get('risk_reward_ratio'):
        logger.info(f"   RR Ratio: {enhanced_signal['risk_reward_ratio']:.2f}:1")
```

### C. Record Trade Outcome

```python
# Sau khi position đóng (trong monitoring hoặc close logic)
# Giả sử bạn có thông tin về trade result

profit_loss = final_pnl  # Tính từ entry/exit prices
is_win = profit_loss > 0

# Record vào risk management system
record_trade(
    db=db,
    subscription_id=subscription_id,
    pnl=profit_loss,
    is_win=is_win
)

logger.info(
    f"📊 Trade recorded: PnL=${profit_loss:.2f}, "
    f"Result={'WIN' if is_win else 'LOSS'}"
)
```

## 📋 Full Example Integration

```python
@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def run_bot_logic(self, subscription_id: int):
    """Enhanced bot logic with risk management"""
    
    from services.risk_integration import (
        apply_risk_to_signal, 
        record_trade, 
        is_trading_allowed
    )
    
    try:
        db = SessionLocal()
        
        # Get subscription
        subscription = crud.get_subscription_by_id(db, subscription_id)
        
        # ⏰ Update next run (race condition fix)
        next_run = _calculate_next_run(subscription.bot.timeframe)
        crud.update_subscription_next_run(db, subscription_id, next_run)
        
        # 🛡️ STEP 1: Quick check if trading is allowed
        allowed, reason = is_trading_allowed(db, subscription_id)
        if not allowed:
            logger.info(f"⏸️ Trading paused for subscription {subscription_id}: {reason}")
            return {'status': 'paused', 'reason': reason}
        
        # Initialize bot and get signal
        bot = initialize_bot(subscription)
        signal = await bot.generate_signal(historical_data)
        
        if signal.action == "HOLD":
            logger.info("No action signal")
            return
        
        # Get account info
        account_info = futures_client.get_account_info()
        entry_price = float(ticker['price'])
        
        # 🛡️ STEP 2: Apply risk management
        signal_data = {
            'action': signal.action,
            'entry_price': entry_price,
            'stop_loss': signal.recommendation.get('stop_loss') if signal.recommendation else None,
            'take_profit': signal.recommendation.get('take_profit') if signal.recommendation else None,
            'confidence': signal.value
        }
        
        market_data = {
            'current_price': entry_price,
            'volatility': analysis.get('volatility', 0.05)
        }
        
        approved, enhanced_signal, rm_reason = apply_risk_to_signal(
            db, subscription_id, signal_data, market_data, account_info
        )
        
        if not approved:
            logger.warning(f"❌ Risk management rejected: {rm_reason}")
            crud.log_bot_action(db, subscription_id, "REJECTED", 
                              f"Risk blocked: {rm_reason}")
            return {'status': 'rejected', 'reason': rm_reason}
        
        # Use risk-managed parameters
        stop_loss = enhanced_signal['stop_loss']
        take_profit = enhanced_signal['take_profit']
        position_size_pct = enhanced_signal.get('position_size_pct', 0.02)
        max_leverage = enhanced_signal.get('max_leverage', 5)
        
        logger.info(f"✅ Risk approved: {rm_reason}")
        for warning in enhanced_signal.get('risk_warnings', []):
            logger.warning(f"⚠️ {warning}")
        
        # Execute trade with risk-managed parameters
        result = await bot.setup_position(signal, analysis)
        
        if result['status'] == 'success':
            logger.info(f"✅ Trade executed successfully")
            crud.log_bot_action(db, subscription_id, signal.action, 
                              f"Position opened with risk management")
            
            # Store trade info for later outcome recording
            # (This would be done when position closes)
            
        return result
        
    finally:
        db.close()
```

## 🔄 Recording Trade Outcomes

### Option 1: In Position Monitor

```python
# In position_monitor.py or similar

async def check_closed_positions(subscription_id: int):
    """Check if any positions closed and record outcomes"""
    
    db = SessionLocal()
    
    # Get closed positions
    closed_positions = get_closed_positions_since_last_check(subscription_id)
    
    for position in closed_positions:
        pnl = calculate_pnl(position)
        is_win = pnl > 0
        
        # Record in risk management
        record_trade(db, subscription_id, pnl, is_win)
        
        logger.info(
            f"Position closed for subscription {subscription_id}: "
            f"PnL=${pnl:.2f}, Result={'WIN' if is_win else 'LOSS'}"
        )
    
    db.close()
```

### Option 2: After Manual Close

```python
# When user manually closes position or SL/TP hits

def handle_position_close(subscription_id: int, position_data: Dict):
    """Handle position close event"""
    
    db = SessionLocal()
    
    entry_price = position_data['entry_price']
    exit_price = position_data['exit_price']
    quantity = position_data['quantity']
    side = position_data['side']
    
    # Calculate PnL
    if side == 'BUY':
        pnl = (exit_price - entry_price) * quantity
    else:
        pnl = (entry_price - exit_price) * quantity
    
    is_win = pnl > 0
    
    # Record
    record_trade(db, subscription_id, pnl, is_win)
    
    # Log
    logger.info(f"Trade outcome recorded: {'WIN' if is_win else 'LOSS'} ${pnl:.2f}")
    
    db.close()
```

## 🎯 Best Practices

### 1. Always Apply Risk Management

```python
# ❌ BAD - Skipping risk management
if signal.action == "BUY":
    execute_trade(signal)

# ✅ GOOD - Always apply
approved, enhanced_signal, reason = apply_risk_to_signal(...)
if approved:
    execute_trade(enhanced_signal)
```

### 2. Use Enhanced Parameters

```python
# ❌ BAD - Ignoring risk-enhanced values
stop_loss = my_default_sl
take_profit = my_default_tp

# ✅ GOOD - Use risk-managed values
stop_loss = enhanced_signal.get('stop_loss', my_default_sl)
take_profit = enhanced_signal.get('take_profit', my_default_tp)
position_size = enhanced_signal.get('position_size_pct', default_size)
```

### 3. Log Risk Warnings

```python
# ✅ GOOD - Always log warnings
if enhanced_signal.get('risk_warnings'):
    for warning in enhanced_signal['risk_warnings']:
        logger.warning(f"⚠️ Risk warning: {warning}")
        # Optionally send to user via notification
```

### 4. Always Record Outcomes

```python
# ✅ GOOD - Record all trade outcomes
# This is critical for cooldown and daily loss tracking
record_trade(db, subscription_id, pnl, is_win)
```

## 📊 Monitoring Integration

### Add Risk Status to Bot Status

```python
def get_bot_status(subscription_id: int) -> Dict:
    """Get comprehensive bot status including risk management"""
    
    from api.endpoints.risk_management import get_risk_status
    
    db = SessionLocal()
    
    # Get regular bot status
    status = {
        'subscription_id': subscription_id,
        'bot_running': True,
        'last_signal': '...',
        # ... other status fields
    }
    
    # Add risk management status
    risk_status = get_risk_status(subscription_id, db)
    status['risk_management'] = risk_status
    
    db.close()
    return status
```

## 🚨 Error Handling

### Graceful Degradation

```python
try:
    approved, enhanced_signal, reason = apply_risk_to_signal(
        db, subscription_id, signal_data, market_data, account_info
    )
except Exception as e:
    logger.error(f"Risk management error: {e}")
    # Decide: reject trade or approve with warning?
    
    # Option 1: Fail-safe (approve)
    approved = True
    enhanced_signal = signal_data
    reason = "Risk check failed, proceeding with caution"
    
    # Option 2: Fail-secure (reject)
    # approved = False
    # return {'status': 'error', 'reason': str(e)}
```

## 🔍 Testing Integration

```python
# Test script
def test_risk_integration():
    """Test risk management integration"""
    
    db = SessionLocal()
    subscription_id = 123
    
    # Test 1: Check if trading allowed
    allowed, reason = is_trading_allowed(db, subscription_id)
    print(f"Trading allowed: {allowed}, reason: {reason}")
    
    # Test 2: Apply risk to dummy signal
    test_signal = {
        'action': 'BUY',
        'entry_price': 50000,
        'stop_loss': 49000,
        'take_profit': 52000,
        'confidence': 0.75
    }
    
    test_market = {'current_price': 50000}
    test_account = {'totalWalletBalance': 10000, 'availableBalance': 8000}
    
    approved, enhanced, reason = apply_risk_to_signal(
        db, subscription_id, test_signal, test_market, test_account
    )
    
    print(f"Approved: {approved}")
    print(f"Reason: {reason}")
    if enhanced:
        print(f"Enhanced signal: {enhanced}")
    
    # Test 3: Record dummy outcome
    record_trade(db, subscription_id, -50.0, False)  # Loss
    print("Trade outcome recorded")
    
    db.close()

if __name__ == '__main__':
    test_risk_integration()
```

## 📚 Additional Resources

- [Risk Management System Overview](./RISK_MANAGEMENT_SYSTEM.md)
- [API Reference](./API_REFERENCE.md)
- [Position Monitoring](./POSITION_MONITORING_SYSTEM.md)

## 🎓 Migration Guide

### For Existing Bots

1. **Add imports**
   ```python
   from services.risk_integration import apply_risk_to_signal, record_trade
   ```

2. **Wrap signal execution**
   ```python
   # Before
   if signal.action == "BUY":
       execute_trade()
   
   # After
   approved, enhanced_signal, reason = apply_risk_to_signal(...)
   if approved:
       execute_trade(enhanced_signal)
   ```

3. **Add outcome recording**
   ```python
   # After position closes
   record_trade(db, subscription_id, pnl, is_win)
   ```

4. **Test thoroughly**
   - Test with DEFAULT mode first
   - Verify cooldowns work
   - Check daily loss tracking
   - Try AI mode when comfortable

Done! 🎉


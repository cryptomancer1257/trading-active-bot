# Race Condition Fix: Moving Next Run Update to Job Start

## Problem

Previously, the `next_run_at` timestamp was updated at the **END** of each job execution. This created a race condition where:

1. Job starts at 10:00:00 and `next_run_at` is still 10:00:00
2. Scheduler checks at 10:00:05 and sees `next_run_at` is past due
3. Scheduler triggers the job AGAIN (duplicate execution)
4. First job completes at 10:00:10 and updates `next_run_at` to 10:01:10
5. Second job completes at 10:00:15 and updates `next_run_at` to 10:01:15

This resulted in multiple jobs running simultaneously for the same subscription.

## Solution

Move the `next_run_at` update to the **BEGINNING** of each job, immediately after validation checks.

### Timeline (After Fix)

1. Job starts at 10:00:00
2. **IMMEDIATELY** update `next_run_at` to 10:01:00 (preventing duplicate scheduling)
3. Job executes for 10 seconds
4. Job completes at 10:00:10
5. Scheduler checks at any time during execution and sees `next_run_at = 10:01:00` (future) → **SKIPS**

## Changes Made

### 1. Helper Function (`_calculate_next_run`)

Created a reusable helper function to calculate next run time based on timeframe:

```python
def _calculate_next_run(timeframe: str) -> 'datetime':
    """Helper function to calculate next run time based on timeframe"""
    from datetime import datetime, timedelta
    
    if timeframe == "1m":
        return datetime.utcnow() + timedelta(minutes=1)
    elif timeframe == "5m":
        return datetime.utcnow() + timedelta(minutes=5)
    # ... etc
```

### 2. Updated Three Task Functions

#### `run_bot_logic` (Lines 1041-1048)
- **ADDED**: Immediate next_run_at update after validation checks
- **REMOVED**: next_run_at update at end of function
- **Location**: After subscription validation, before bot initialization

#### `run_bot_rpa_logic` (Lines 1530-1537)
- **ADDED**: Immediate next_run_at update after validation checks
- **REMOVED**: next_run_at update at end of function
- **Location**: After subscription validation, before bot initialization

#### `run_bot_signal_logic` (Lines 1891-1898)
- **ADDED**: Immediate next_run_at update after validation checks
- **REMOVED**: next_run_at update at end of function
- **Location**: After subscription validation, before RPA execution

### 3. Updated Log Messages

Changed completion messages from:
```
✅ Bot execution completed. Next run scheduled at {next_run}
```

To:
```
✅ Bot execution completed. Next run was already scheduled at start to prevent duplicates.
```

## Benefits

1. **No Duplicate Execution**: Scheduler can't pick up the same subscription twice
2. **Consistent Intervals**: Jobs run at fixed intervals from start time, not completion time
3. **Better Performance**: Reduces unnecessary database queries and lock contention
4. **Clearer Logs**: Makes it obvious that scheduling happens upfront

## Example Log Flow

```
[10:00:00] 🔓 Acquired execution lock for subscription 123
[10:00:00] Running bot logic for subscription 123
[10:00:00] ⏰ Next run scheduled at 10:01:00 (preventing duplicate execution)
[10:00:05] 📊 Analyzing market data...
[10:00:08] 🚀 Opening BUY position...
[10:00:10] ✅ Bot execution completed. Next run was already scheduled at start to prevent duplicates.
[10:00:10] 🔓 Released execution lock for subscription 123
```

## Redis Lock Compatibility

This change **complements** the existing Redis lock mechanism:

- **Redis Lock**: Prevents multiple workers from executing the same job simultaneously
- **Next Run Update**: Prevents scheduler from queuing duplicate jobs

Both mechanisms work together for robust duplicate prevention.

## Testing Recommendations

1. Monitor logs for the new message format
2. Verify no duplicate execution warnings in Redis lock logs
3. Check that job intervals remain consistent
4. Verify error handling still works (next_run_at update failure is logged but doesn't stop execution)

## Rollback Plan

If issues arise, the change can be easily rolled back by:
1. Moving the `next_run_at` update back to the end of each function
2. Removing the `_calculate_next_run` helper if desired
3. Reverting log messages

However, this should **not** be necessary as the change is backward compatible and only improves reliability.


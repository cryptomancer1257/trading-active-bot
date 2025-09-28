#!/usr/bin/env python3
"""
Test script to insert sample execution logs for bot 51
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db
from core import models
from datetime import datetime
import json

def insert_sample_logs():
    """Insert sample execution logs for bot 51"""
    try:
        db = next(get_db())
        
        # Sample execution logs
        sample_logs = [
            {
                "bot_id": 51,
                "subscription_id": 470,
                "task_id": "celery_task_123",
                "log_type": "system",
                "message": "Bot initialized successfully",
                "level": "info",
                "data": json.dumps({"status": "initialized", "version": "1.0.0"})
            },
            {
                "bot_id": 51,
                "subscription_id": 470,
                "task_id": "celery_task_123",
                "log_type": "analysis",
                "message": "Starting market analysis for BTC/USDT",
                "level": "info",
                "data": json.dumps({"symbol": "BTC/USDT", "timeframe": "1h"})
            },
            {
                "bot_id": 51,
                "subscription_id": 470,
                "task_id": "celery_task_123",
                "log_type": "llm",
                "message": "LLM Analysis: Strong bullish momentum detected",
                "level": "info",
                "data": json.dumps({"confidence": 0.85, "signal": "BUY"})
            },
            {
                "bot_id": 51,
                "subscription_id": 470,
                "task_id": "celery_task_123",
                "log_type": "position",
                "message": "Position sizing: 0.001 BTC (10x leverage)",
                "level": "info",
                "data": json.dumps({"quantity": 0.001, "leverage": 10})
            },
            {
                "bot_id": 51,
                "subscription_id": 470,
                "task_id": "celery_task_123",
                "log_type": "order",
                "message": "Entry price: $50,000 | Stop loss: $48,000 | Take profit: $52,000",
                "level": "info",
                "data": json.dumps({"entry": 50000, "stop_loss": 48000, "take_profit": 52000})
            },
            {
                "bot_id": 51,
                "subscription_id": 470,
                "task_id": "celery_task_123",
                "log_type": "transaction",
                "message": "Order executed: BUY 0.001 BTC/USDT at $50,000",
                "level": "info",
                "data": json.dumps({"action": "BUY", "quantity": 0.001, "price": 50000})
            }
        ]
        
        # Insert logs
        for log_data in sample_logs:
            execution_log = models.ExecutionLog(
                bot_id=log_data["bot_id"],
                subscription_id=log_data["subscription_id"],
                task_id=log_data["task_id"],
                log_type=log_data["log_type"],
                message=log_data["message"],
                level=log_data["level"],
                data=log_data["data"],
                created_at=datetime.now()
            )
            db.add(execution_log)
        
        db.commit()
        print(f"✅ Inserted {len(sample_logs)} sample execution logs for bot 51")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to insert sample logs: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Inserting sample execution logs...")
    success = insert_sample_logs()
    if success:
        print("🎉 Sample logs inserted successfully!")
    else:
        print("💥 Failed to insert sample logs!")

"""
FastAPI endpoints for Futures Bot Celery integration
Provides REST API to trigger automated futures trading
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/futures-bot", tags=["Futures Bot"])

class FuturesBotConfig(BaseModel):
    """Configuration for Futures Bot execution"""
    trading_pair: str = "BTCUSDT"
    testnet: bool = True
    leverage: int = 10
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.04
    position_size_pct: float = 0.05
    timeframes: list = ["5m", "30m", "1h", "4h", "1d"]
    primary_timeframe: str = "1h"
    use_llm_analysis: bool = True
    llm_model: str = "openai"
    auto_confirm: bool = True
    require_confirmation: bool = False

class FuturesBotExecuteRequest(BaseModel):
    """Request to execute Futures Bot"""
    user_principal_id: Optional[str] = None
    config: Optional[FuturesBotConfig] = None

class FuturesBotScheduleRequest(BaseModel):
    """Request to schedule Futures Bot"""
    interval_minutes: int = 60
    user_principal_id: Optional[str] = None
    config: Optional[FuturesBotConfig] = None

@router.post("/execute")
async def execute_futures_bot(request: FuturesBotExecuteRequest):
    """
    Execute Futures Bot trading cycle with auto-confirmation
    
    This endpoint triggers the Futures Bot via Celery for automated trading.
    All trades are auto-confirmed (no user interaction required).
    """
    try:
        from core.tasks import run_futures_bot_trading
        
        logger.info(f"🚀 API request to execute Futures Bot")
        logger.info(f"   Principal ID: {request.user_principal_id or 'Direct keys'}")
        logger.info(f"   Custom config: {'Yes' if request.config else 'No'}")
        
        # Convert config to dict if provided
        config_dict = None
        if request.config:
            config_dict = request.config.dict()
            # Ensure auto-confirmation is enabled for API calls
            config_dict['auto_confirm'] = True
            config_dict['require_confirmation'] = False
            
        # Submit Celery task
        task = run_futures_bot_trading.delay(
            user_principal_id=request.user_principal_id,
            config=config_dict
        )
        
        logger.info(f"✅ Celery task submitted: {task.id}")
        
        return {
            "status": "submitted",
            "task_id": task.id,
            "message": "Futures Bot execution submitted to Celery queue",
            "queue": "futures_trading",
            "auto_confirm": True,
            "config": config_dict or "default"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute Futures Bot: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@router.post("/schedule")
async def schedule_futures_bot(request: FuturesBotScheduleRequest):
    """
    Schedule periodic Futures Bot trading
    
    This endpoint sets up automated trading at specified intervals.
    All trades are auto-confirmed.
    """
    try:
        from core.tasks import schedule_futures_bot_trading
        
        logger.info(f"⏰ API request to schedule Futures Bot")
        logger.info(f"   Interval: {request.interval_minutes} minutes")
        logger.info(f"   Principal ID: {request.user_principal_id or 'Direct keys'}")
        
        # Validate interval
        if request.interval_minutes < 5:
            raise HTTPException(status_code=400, detail="Minimum interval is 5 minutes")
        if request.interval_minutes > 10080:  # 1 week
            raise HTTPException(status_code=400, detail="Maximum interval is 1 week (10080 minutes)")
        
        # Convert config to dict if provided
        config_dict = None
        if request.config:
            config_dict = request.config.dict()
            # Ensure auto-confirmation is enabled
            config_dict['auto_confirm'] = True
            config_dict['require_confirmation'] = False
            
        # Submit scheduling task
        task = schedule_futures_bot_trading.delay(
            interval_minutes=request.interval_minutes,
            user_principal_id=request.user_principal_id,
            config=config_dict
        )
        
        logger.info(f"✅ Schedule task submitted: {task.id}")
        
        return {
            "status": "scheduled",
            "task_id": task.id,
            "message": f"Futures Bot scheduled to run every {request.interval_minutes} minutes",
            "interval_minutes": request.interval_minutes,
            "next_execution": f"In {request.interval_minutes} minutes",
            "auto_confirm": True,
            "config": config_dict or "default"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to schedule Futures Bot: {e}")
        raise HTTPException(status_code=500, detail=f"Scheduling failed: {str(e)}")

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of a Futures Bot Celery task
    """
    try:
        from utils.celery_app import app
        
        # Get task result
        task_result = app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready()
        }
        
        if task_result.ready():
            if task_result.successful():
                response["result"] = task_result.result
            else:
                response["error"] = str(task_result.info)
        else:
            response["info"] = task_result.info
            
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/status")
async def get_futures_bot_status():
    """
    Get general Futures Bot status and configuration
    """
    try:
        from utils.celery_app import app
        
        # Check Celery worker status
        worker_status = app.control.ping()
        
        return {
            "service": "Futures Bot API",
            "status": "active",
            "celery_workers": len(worker_status) if worker_status else 0,
            "auto_confirmation": True,
            "supported_pairs": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            "supported_timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
            "features": [
                "Multi-timeframe analysis",
                "LLM-powered signals",
                "Auto-confirmation",
                "Risk management",
                "Database API keys",
                "Scheduled execution"
            ],
            "queues": ["futures_trading"],
            "endpoints": {
                "execute": "POST /futures-bot/execute",
                "schedule": "POST /futures-bot/schedule", 
                "status": "GET /futures-bot/task-status/{task_id}"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/stop-all")
async def stop_all_scheduled_tasks():
    """
    Stop all scheduled Futures Bot tasks
    """
    try:
        from utils.celery_app import app
        
        # Revoke all scheduled futures trading tasks
        active_tasks = app.control.inspect().active()
        scheduled_tasks = app.control.inspect().scheduled()
        
        revoked_count = 0
        
        # Revoke active futures trading tasks
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    if 'futures_bot' in task.get('name', '').lower():
                        app.control.revoke(task['id'], terminate=True)
                        revoked_count += 1
                        
        # Revoke scheduled futures trading tasks
        if scheduled_tasks:
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    if 'futures_bot' in task.get('name', '').lower():
                        app.control.revoke(task['id'])
                        revoked_count += 1
        
        logger.info(f"🛑 Stopped {revoked_count} Futures Bot tasks")
        
        return {
            "status": "stopped",
            "message": f"Stopped {revoked_count} Futures Bot tasks",
            "revoked_tasks": revoked_count
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to stop tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Stop failed: {str(e)}")

# Example usage documentation
@router.get("/examples")
async def get_api_examples():
    """
    Get API usage examples for Futures Bot integration
    """
    return {
        "examples": {
            "execute_default": {
                "method": "POST",
                "url": "/futures-bot/execute",
                "body": {},
                "description": "Execute with default config and direct API keys"
            },
            "execute_custom": {
                "method": "POST", 
                "url": "/futures-bot/execute",
                "body": {
                    "config": {
                        "trading_pair": "ETHUSDT",
                        "leverage": 5,
                        "timeframes": ["1h", "4h"],
                        "testnet": True
                    }
                },
                "description": "Execute with custom configuration"
            },
            "execute_database": {
                "method": "POST",
                "url": "/futures-bot/execute", 
                "body": {
                    "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai"
                },
                "description": "Execute using database API keys"
            },
            "schedule_hourly": {
                "method": "POST",
                "url": "/futures-bot/schedule",
                "body": {
                    "interval_minutes": 60,
                    "config": {
                        "trading_pair": "BTCUSDT",
                        "leverage": 10
                    }
                },
                "description": "Schedule hourly execution"
            },
            "check_status": {
                "method": "GET",
                "url": "/futures-bot/task-status/{task_id}",
                "description": "Check task execution status"
            }
        },
        "curl_examples": {
            "execute": "curl -X POST 'http://localhost:8000/futures-bot/execute' -H 'Content-Type: application/json' -d '{}'",
            "schedule": "curl -X POST 'http://localhost:8000/futures-bot/schedule' -H 'Content-Type: application/json' -d '{\"interval_minutes\": 60}'",
            "status": "curl 'http://localhost:8000/futures-bot/status'"
        },
        "notes": [
            "All trades are auto-confirmed (no user interaction required)",
            "Testnet is enabled by default for safety",
            "LLM analysis is enabled by default",
            "Tasks are queued in 'futures_trading' queue",
            "Results include full trading details and account status"
        ]
    }
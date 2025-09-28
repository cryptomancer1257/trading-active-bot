#!/usr/bin/env python3
"""
Execution Logger for Bot Trading Activities
Captures and stores logs from Celery tasks
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from core.database import get_db
from core import models

class ExecutionLogger:
    """Logger that stores execution logs in database"""
    
    def __init__(self, bot_id: int, subscription_id: Optional[int] = None, task_id: Optional[str] = None):
        self.bot_id = bot_id
        self.subscription_id = subscription_id
        self.task_id = task_id
        self.logger = logging.getLogger(f"bot_{bot_id}")
        
    def log(self, log_type: str, message: str, level: str = 'info', data: Optional[Dict[str, Any]] = None):
        """Log a message to database"""
        try:
            db = next(get_db())
            
            execution_log = models.ExecutionLog(
                bot_id=self.bot_id,
                subscription_id=self.subscription_id,
                task_id=self.task_id,
                log_type=log_type,
                message=message,
                level=level,
                data=data,
                created_at=datetime.now()
            )
            
            db.add(execution_log)
            db.commit()
            
            # Also log to console
            self.logger.info(f"[{log_type.upper()}] {message}")
            
        except Exception as e:
            print(f"Failed to log to database: {e}")
            # Fallback to console logging
            self.logger.info(f"[{log_type.upper()}] {message}")
    
    def system(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log system message"""
        self.log('system', message, 'info', data)
    
    def analysis(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log analysis message"""
        self.log('analysis', message, 'info', data)
    
    def llm(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log LLM analysis message"""
        self.log('llm', message, 'info', data)
    
    def transaction(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log transaction message"""
        self.log('transaction', message, 'info', data)
    
    def position(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log position message"""
        self.log('position', message, 'info', data)
    
    def order(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log order message"""
        self.log('order', message, 'info', data)
    
    def error(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log error message"""
        self.log('error', message, 'error', data)
    
    def warning(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        self.log('warning', message, 'warning', data)

# Global logger instance
execution_loggers = {}

def get_execution_logger(bot_id: int, subscription_id: Optional[int] = None, task_id: Optional[str] = None):
    """Get or create execution logger for bot"""
    key = f"{bot_id}_{subscription_id}_{task_id}"
    if key not in execution_loggers:
        execution_loggers[key] = ExecutionLogger(bot_id, subscription_id, task_id)
    return execution_loggers[key]

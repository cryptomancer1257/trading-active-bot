from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any

class Action(BaseModel):
    """Trading action with detailed information"""
    action: Literal["BUY", "SELL", "HOLD"]
    type: Optional[Literal["PERCENTAGE", "USDT_AMOUNT", "QUANTITY"]] = None
    value: Optional[float] = None
    reason: Optional[str] = None  # Explanation for the action
    recommendation: Optional[Dict[str, Any]] = None  # LLM/Technical analysis recommendation details
    
    def __init__(self, action=None, value=None, reason=None, recommendation=None, **kwargs):
        """Initialize Action with backward compatibility for positional arguments"""
        if action is not None and isinstance(action, str):
            # Old style: Action("BUY", 0.5, "reason")
            super().__init__(action=action, value=value, reason=reason, recommendation=recommendation, **kwargs)
        else:
            # New style: Action(action="BUY", value=0.5, reason="reason", recommendation=...)
            super().__init__(**kwargs)
    
    @classmethod
    def buy(cls, type: str, value: float, reason: str = "", recommendation: Optional[Dict[str, Any]] = None):
        """Create a BUY action"""
        return cls(action="BUY", type=type, value=value, reason=reason, recommendation=recommendation)

    @classmethod
    def sell(cls, type: str, value: float, reason: str = "", recommendation: Optional[Dict[str, Any]] = None):
        """Create a SELL action"""
        return cls(action="SELL", type=type, value=value, reason=reason, recommendation=recommendation)

    @classmethod
    def hold(cls, reason: str = "", recommendation: Optional[Dict[str, Any]] = None):
        """Create a HOLD action"""
        return cls(action="HOLD", value=0.0, reason=reason, recommendation=recommendation)
    
    def __str__(self):
        return f"Action(action={self.action}, value={self.value}, reason={self.reason})" 
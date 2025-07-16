from pydantic import BaseModel
from typing import Literal, Optional

class Action(BaseModel):
    """Trading action with detailed information"""
    action: Literal["BUY", "SELL", "HOLD"]
    type: Optional[Literal["PERCENTAGE", "USDT_AMOUNT", "QUANTITY"]] = None
    value: Optional[float] = None
    reason: Optional[str] = None  # Explanation for the action
    
    def __init__(self, action: str, value: float = 0.0, reason: str = ""):
        """Initialize Action with action type, value, and reason"""
        super().__init__()
        self.action = action
        self.value = value
        self.reason = reason
    
    @classmethod
    def buy(cls, type: str, value: float, reason: str = ""):
        """Create a BUY action"""
        action = cls(action="BUY", value=value, reason=reason)
        action.type = type
        return action

    @classmethod
    def sell(cls, type: str, value: float, reason: str = ""):
        """Create a SELL action"""
        action = cls(action="SELL", value=value, reason=reason)
        action.type = type
        return action

    @classmethod
    def hold(cls, reason: str = ""):
        """Create a HOLD action"""
        return cls(action="HOLD", value=0.0, reason=reason)
    
    def __str__(self):
        return f"Action(action={self.action}, value={self.value}, reason={self.reason})" 
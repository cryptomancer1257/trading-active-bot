import pandas as pd
from pydantic import BaseModel
from typing import Literal, Optional

class Action(BaseModel):
    action: Literal["BUY", "SELL", "HOLD"]
    type: Optional[Literal["PERCENTAGE", "USDT_AMOUNT", "QUANTITY"]] = None
    value: Optional[float] = None

    @classmethod
    def buy(cls, type: str, value: float):
        return cls(action="BUY", type=type, value=value)

    @classmethod
    def sell(cls, type: str, value: float):
        return cls(action="SELL", type=type, value=value)

    @classmethod
    def hold(cls):
        return cls(action="HOLD")

class CustomBot:
    bot_name: str = "Base Bot"
    bot_description: str = "This is a base class for all trading bots."

    def __init__(self, bot_config: dict, user_api_keys: dict):
        self.config = bot_config
        self.api_keys = user_api_keys
        # Trong thực tế, bạn sẽ khởi tạo client ở đây
        # self.client = Client(user_api_keys['key'], user_api_keys['secret'])
        print(f"Bot '{self.bot_name}' initialized with config: {self.config}")

    def prepare_data(self, candles_df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def predict(self, prepared_df: pd.DataFrame) -> Action:
        raise NotImplementedError
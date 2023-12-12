from typing import List
from pydantic import BaseModel
import datetime


class RobotDataResponseItem(BaseModel):
    BotID: int
    BotName: str
    BotKey: str
    BotStatus: int
    MessageCount: int
    CreatedAt: datetime.datetime


class RobotDataResponse(BaseModel):
    code: int
    msg: str
    data: List[RobotDataResponseItem]


class RobotDataResponseInfo(BaseModel):
    code: int
    msg: str
    data: RobotDataResponseItem

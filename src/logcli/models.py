from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class LogStats(BaseModel):
    total: int = Field(ge=0)
    error_count: int = Field(default=0, ge=0)
    warn_count: int = Field(default=0, ge=0)

    @property
    def error_rate(self) -> float:
        return self.error_count / self.total if self.total else 0.0


Level = Literal["INFO", "WARN", "ERROR"]


class LogRecord(BaseModel):
    timestamp: datetime
    level: Level
    message: str


if __name__ == "__main__":  # ≈ 「這個檔案被直接執行時才跑」，之後會細講
    # s = LogStats(total=100)
    # print(s)
    # print(s.error_rate)

    # empty = LogStats(total=0)
    # print(empty.error_rate)

    try:
        LogStats(total=-1)
    except ValidationError as e:
        print(e)

from collections import Counter
from datetime import datetime

from .models import LogRecord


class LogParseError(Exception):
    def __init__(self, raw: str, reason: str, field: str | None = None):
        self.raw = raw
        self.reason = reason
        self.field = field
        super().__init__(f"解析失敗 {raw!r}:{reason}")


def extract_level(log_line: str) -> str | None:
    """
    字串裡含 "ERROR" 回傳 "ERROR"
    含 "WARN" 回傳 "WARN"
    含 "INFO" 回傳 "INFO"
    都沒有回傳 None
    """

    if "ERROR" in log_line:
        return "ERROR"
    elif "WARN" in log_line:
        return "WARN"
    elif "INFO" in log_line:
        return "INFO"
    else:
        return None


def count_levels(lines: list[str]) -> Counter[str]:
    return Counter(level for line in lines if (level := extract_level(line)) is not None)


def parse_line(line: str) -> LogRecord:
    try:
        parts = line.split(" ", 2)
        if len(parts) < 3:
            raise LogParseError(raw=line, reason="訊息字串缺少錯誤內容")
        time = parts[0]
        level = parts[1]
        reason = parts[2]
        format_time = datetime.fromisoformat(time)
        if level not in ("INFO", "WARN", "ERROR"):
            raise LogParseError(raw=line, reason="level 不在 INFO/WARN/ERROR 之內")
        return LogRecord(timestamp=format_time, level=level, message=reason)
    except ValueError as e:
        raise LogParseError(raw=line, reason="timestamp 格式錯誤") from e


if __name__ == "__main__":
    tests = [
        "2026-07-22T10:00:00 ERROR 資料庫 連線 失敗",  # ✅ 正常:訊息含空格也要完整保留
        "2026-07-22T10:00:00 CRITICAL 等級不存在",  # ❌ level 不合法
        "not-a-time ERROR 時間格式壞掉",  # ❌ timestamp 壞 → 要 from e 鏈
        "只有兩段 INFO",  # ❌ 缺欄位(切不出三段)
        "onlyoneword",  # ❌ 缺欄位(只有一段)
    ]
    for line in tests:
        try:
            record = parse_line(line)
            print("OK  ->", record)
        except LogParseError as e:
            print("FAIL->", e)

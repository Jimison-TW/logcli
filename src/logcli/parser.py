import logging
import os
from collections import Counter
from datetime import datetime

from .logging_config import setup_logging
from .models import LogRecord

logger = logging.getLogger(__name__)


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
    parts = line.split(" ", 2)
    if len(parts) < 3:
        raise LogParseError(raw=line, reason="訊息字串缺少錯誤內容")
    time = parts[0]
    level = parts[1]
    reason = parts[2]
    try:
        format_time = datetime.fromisoformat(time)
    except ValueError as e:
        raise LogParseError(raw=line, reason="timestamp 格式錯誤") from e
    if level not in ("INFO", "WARN", "ERROR"):
        raise LogParseError(raw=line, reason="level 不在 INFO/WARN/ERROR 之內")
    return LogRecord(timestamp=format_time, level=level, message=reason)


if __name__ == "__main__":
    verbose_enable = os.environ.get("LOGCLI_VERBOSE", "").lower() in ("1", "true", "yes")
    setup_logging(verbose=verbose_enable)

    tests = [
        "2026-07-22T10:00:00 ERROR 資料庫 連線 失敗",  # ✅ 正常:訊息含空格也要完整保留
        "2026-07-22T10:00:00 CRITICAL 等級不存在",  # ❌ level 不合法
        "not-a-time ERROR 時間格式壞掉",  # ❌ timestamp 壞 → 要 from e 鏈
        "只有兩段 INFO",  # ❌ 缺欄位(切不出三段)
        "onlyoneword",  # ❌ 缺欄位(只有一段)
    ]
    success = 0
    failed = 0
    for line in tests:
        try:
            record = parse_line(line)
            logger.debug("%s", record)
            success += 1
        except LogParseError as e:
            logger.warning("%s", e)  # 給使用者：乾淨一行
            logger.debug("解析失敗細節", exc_info=True)  # 給開發者：--verbose 才看得到 traceback
            failed += 1

    logger.info("parse success: %s, failed: %s", success, failed)

import argparse
import csv
import json
import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import TypeIs, get_args

from openpyxl import Workbook

from .logging_config import setup_logging
from .models import Level, LogRecord

logger = logging.getLogger(__name__)
LOG_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"  # 時間戳
    r" (?P<level>\w+)"  # 空格 + 等級
    r"( \[(?P<ip>[\d.]+)\])?"  # 可選:空格 + [IP]
    r"( code=(?P<code>\w\d{4}))?"  # 可選:空格 + code=
    r" (?P<message>.+)"  # 空格 + 訊息(剩下全部)
)


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


def is_legal_level(s: str) -> TypeIs[Level]:
    return s in get_args(Level)


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
    if not is_legal_level(level):
        raise LogParseError(raw=line, reason="level 不在 INFO/WARN/ERROR 之內")
    return LogRecord(timestamp=format_time, level=level, message=reason)


def read_lines(path: Path) -> list[str]:
    if path.exists() and path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
        return lines
    elif not path.exists():
        raise FileNotFoundError(path)
    elif not path.is_file():
        raise FileExistsError()
    return []
    # with open(path, encoding="utf-8") as f:
    #     lines = f.read().splitlines()  # 每行一個字串、去掉換行


def build_rows(data: list[str]) -> list[tuple[str, int]]:
    return sorted(count_levels(data).items())


def write_csv_report(data: list[str], output: Path) -> None:
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["level", "count"])
        writer.writerows(build_rows(data))


def write_excel_report(data: list[str], output: Path) -> None:
    wb = Workbook()
    ws = wb.active  # ← 用預設那張,不要 create_sheet()
    assert ws is not None  # 預設一定有,但堵住 Worksheet|None 的型別/None 疑慮
    ws.title = "logcli"  # 幫它改名(不是多開一張)
    ws.append(["level", "count"])
    for item in build_rows(data):
        ws.append(item)
    wb.save(output)


def extract_fields(log: str) -> LogRecord:
    m = LOG_PATTERN.search(log)
    if m is None:
        raise LogParseError(raw=log, reason="找不到符合的欄位")
    level = m.group("level")
    if not is_legal_level(level):
        raise LogParseError(raw=log, reason="level 不合法")
    # 這行之後 mypy 就把 level 從 str 縮成 Level 了(TypeIs)
    try:
        f_time = datetime.fromisoformat(m.group("timestamp"))
        return LogRecord(
            timestamp=f_time,
            level=level,
            message=m.group("message"),
            ip=m.group("ip"),
            code=m.group("code"),
        )
    except ValueError as e:
        raise LogParseError(raw=log, reason="timestamp 格式錯誤") from e


def main() -> None:
    parser = argparse.ArgumentParser(description="解析錯誤訊息")
    parser.add_argument("-v", "--verbose", action="store_true", help="開 DEBUG log")

    sub = parser.add_subparsers(dest="command", required=True)
    sub_parse = sub.add_parser("parse", help="要讀取的檔案目錄路徑")
    sub_parse.add_argument("file", help="log 檔路徑", type=Path)
    sub_parse.add_argument("--level", choices=["INFO", "WARN", "ERROR"], help="只看某個等級")
    sub_parse.add_argument("--top", type=int, help="顯示最常見的前 N 個")
    sub_parse.add_argument("--json", action="store_true", help="把統計結果以 JSON 印出來")
    sub_parse.add_argument("--output", type=Path, help="把統計結果寫成 CSV 檔")

    lines = []
    args = parser.parse_args()
    level = args.level
    top_count = args.top
    with_json = args.json
    out_path: Path | None = args.output
    setup_logging(verbose=args.verbose)
    lines = read_lines(args.file)

    if out_path is not None:
        if out_path.suffix == ".csv":
            write_csv_report(lines, out_path)
        elif out_path.suffix == ".xlsx":
            write_excel_report(lines, out_path)
        else:
            ValueError(f"不支援的輸出格式:{out_path.suffix}(只支援 .csv / .xlsx)")

    if top_count is not None or with_json:
        show_top_n(lines, top_count=top_count, with_json=with_json)

    success = 0
    failed = 0
    for line in lines:
        try:
            record = parse_line(line)
            if record.level != level and level is not None:
                continue
            logger.debug("%s", record)
            success += 1
        except LogParseError as e:
            logger.warning("%s", e)  # 給使用者：乾淨一行
            logger.debug("解析失敗細節", exc_info=True)  # 給開發者：--verbose 才看得到 traceback
            failed += 1

    logger.info("parse success: %s, failed: %s", success, failed)


def show_top_n(data: list[str], top_count: int | None, with_json: bool) -> None:
    counter = count_levels(data)
    common = counter.most_common(top_count)
    if with_json:
        print(json.dumps(common))
    else:
        for level, count in common:
            print(f"{level}: {count}")


if __name__ == "__main__":
    main()
    # tests = [
    #     "2026-07-22T10:00:00 ERROR 資料庫 連線 失敗",  # ✅ 正常:訊息含空格也要完整保留
    #     "2026-07-22T10:00:00 CRITICAL 等級不存在",  # ❌ level 不合法
    #     "not-a-time ERROR 時間格式壞掉",  # ❌ timestamp 壞 → 要 from e 鏈
    #     "只有兩段 INFO",  # ❌ 缺欄位(切不出三段)
    #     "onlyoneword",  # ❌ 缺欄位(只有一段)
    # ]

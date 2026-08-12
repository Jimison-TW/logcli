import argparse
import csv
import json
import logging
import re
from collections import Counter
from collections.abc import Iterable, Iterator
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


def count_levels(lines: Iterable[str]) -> Counter[str]:
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
    return []  # pragma: no cover  ← 不可達,mypy 要
    # with open(path, encoding="utf-8") as f:
    #     lines = f.read().splitlines()  # 每行一個字串、去掉換行


def read_lines_streaming(path: Path) -> Iterator[str]:
    if not path.is_file():  # ⭐ 這函式沒有 yield → 普通函式 → 呼叫當下就檢查
        raise FileNotFoundError(path)
    return _stream_lines(path)  # 回傳內層造好的 generator


def _stream_lines(path: Path) -> Iterator[str]:  # ← yield 藏在這，惰性
    with path.open(encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")


def build_rows(data: Counter[str]) -> list[tuple[str, int]]:
    return sorted(data.items())


def write_csv_report(rows: list[tuple[str, int]], output: Path) -> None:
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["level", "count"])
        writer.writerows(rows)


def write_excel_report(rows: list[tuple[str, int]], output: Path) -> None:
    wb = Workbook()
    ws = wb.active  # ← 用預設那張,不要 create_sheet()
    assert ws is not None  # 預設一定有,但堵住 Worksheet|None 的型別/None 疑慮
    ws.title = "logcli"  # 幫它改名(不是多開一張)
    ws.append(["level", "count"])
    for item in rows:
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


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="解析錯誤訊息")
    parser.add_argument("-v", "--verbose", action="store_true", help="開 DEBUG log")
    sub = parser.add_subparsers(dest="command", required=True)
    sub_parse = sub.add_parser("parse", help="要讀取的檔案目錄路徑")
    sub_parse.add_argument("file", help="log 檔路徑", type=Path)
    sub_parse.add_argument("--level", choices=["INFO", "WARN", "ERROR"], help="只看某個等級")
    sub_parse.add_argument("--top", type=int, help="顯示最常見的前 N 個")
    sub_parse.add_argument("--json", action="store_true", help="把統計結果以 JSON 印出來")
    sub_parse.add_argument("--output", type=Path, help="把統計結果寫成報表檔")

    args = parser.parse_args()
    level = args.level
    top_count = args.top
    with_json = args.json
    out_path: Path | None = args.output
    setup_logging(verbose=args.verbose)

    # ⭐ 單次掃描:一個迴圈同時「數等級」+「parse」,generator 只抽一次
    counter: Counter[str] = Counter()
    success = 0
    failed = 0
    for line in read_lines_streaming(args.file):  # ← 讀的是 args.file 不是 out_path
        lvl = extract_level(line)
        if lvl is not None:
            counter[lvl] += 1
        try:
            record = parse_line(line)
            if level is not None and record.level != level:
                continue
            logger.debug("%s", record)
            success += 1
        except LogParseError as e:
            logger.warning("%s", e)
            logger.debug("解析失敗細節", exc_info=True)
            failed += 1

    # ⭐ 掃描結束,counter 已算好;以下全吃這個小 Counter(可重複用)
    if out_path is not None:
        rows = build_rows(counter)  # ← 先轉成 rows 再寫,別把 Counter 直接丟進去
        if out_path.suffix == ".csv":
            write_csv_report(rows, out_path)
        elif out_path.suffix == ".xlsx":
            write_excel_report(rows, out_path)
        else:
            raise ValueError(f"不支援的輸出格式:{out_path.suffix}(只支援 .csv / .xlsx)")

    if top_count is not None or with_json:
        show_top_n(counter, top_count=top_count, with_json=with_json)  # ← 傳算好的 Counter

    logger.info("parse success: %s, failed: %s", success, failed)


def show_top_n(counter: Counter[str], top_count: int | None, with_json: bool) -> None:
    common = counter.most_common(top_count)  # ← 不再自己 count_levels,直接吃傳進來的
    if with_json:
        print(json.dumps(common))
    else:
        for lvl, count in common:
            print(f"{lvl}: {count}")


if __name__ == "__main__":
    main()
    # tests = [
    #     "2026-07-22T10:00:00 ERROR 資料庫 連線 失敗",  # ✅ 正常:訊息含空格也要完整保留
    #     "2026-07-22T10:00:00 CRITICAL 等級不存在",  # ❌ level 不合法
    #     "not-a-time ERROR 時間格式壞掉",  # ❌ timestamp 壞 → 要 from e 鏈
    #     "只有兩段 INFO",  # ❌ 缺欄位(切不出三段)
    #     "onlyoneword",  # ❌ 缺欄位(只有一段)
    # ]

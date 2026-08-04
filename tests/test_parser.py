from collections import Counter

import pytest

from logcli.parser import count_levels, extract_level, read_lines


@pytest.mark.parametrize(
    "log, expected",
    [
        ("2026-07-22T10:00:00 ERROR 資料庫 連線 失敗", "ERROR"),
        ("2026-07-22T10:00:02 WARN 記憶體偏高", "WARN"),
        ("2026-07-22T10:00:01 INFO 服務啟動", "INFO"),
        ("2026-07-22T10:00:00 CRITICAL 等級不存在", None),
        ("2026-07-22T10:00:00 INFO 等級不存在ERROR", "ERROR"),
    ],
)
def test_extract(log, expected):
    assert extract_level(log) == expected


@pytest.mark.parametrize(
    "log_list, expected",
    [
        ([], Counter([])),
        (["2026-07-22T10:00:00 CRITICAL 等級不存在"], Counter([])),
        (
            ["2026-07-22T10:00:01 INFO 服務啟動", "2026-07-22T10:00:00 INFO 等級不存在"],
            Counter({"INFO": 2}),
        ),
        (["2026-07-22T10:00:00 INFO 等級不存在ERROR"], Counter({"ERROR": 1})),
    ],
)
def test_counter(log_list, expected):
    assert count_levels(log_list) == expected


def test_counter_missing_level():
    result = count_levels(
        ["2026-07-22T10:00:01 INFO 服務啟動", "2026-07-22T10:00:00 INFO 等級不存在"]
    )
    assert result["ERROR"] == 0


@pytest.fixture
def sample_log_file(tmp_path):
    # tmp_path 是一個 Path,指向一個空的暫存目錄
    file = tmp_path / "test.log"  # ← Path 用 / 接路徑(≈ path.join),不是字串拼接
    file.write_text(
        "2026-07-22T10:00:00 ERROR 資料庫 連線 失敗\n2026-07-22T10:00:00 CRITICAL 等級不存在",
        encoding="utf-8",
    )
    return file


def test_read_lines(sample_log_file):
    result = read_lines(sample_log_file)
    assert len(result) == 2


def test_read_lines_missing(tmp_path):
    missing = tmp_path / "nope.log"
    with pytest.raises(FileNotFoundError):
        read_lines(missing)


def test_read_lines_empty(tmp_path):
    empty = tmp_path / "empty.log"  # ← 在目錄底下指定一個檔名
    empty.write_text("", encoding="utf-8")  # ← 造出這個檔,內容你想想「空」是什麼
    result = read_lines(empty)  # ← 讀「檔」,不是讀「目錄」
    assert result == []

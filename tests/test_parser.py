from collections import Counter

from logcli.parser import count_levels, extract_level


def test_extract_error():
    assert extract_level("2026-07-22T10:00:00 ERROR 資料庫 連線 失敗") == "ERROR"


def test_extract_warn():
    assert extract_level("2026-07-22T10:00:02 WARN 記憶體偏高") == "WARN"


def test_extract_info():
    assert extract_level("2026-07-22T10:00:01 INFO 服務啟動") == "INFO"


def test_returns_none_when_no_level():
    assert extract_level("2026-07-22T10:00:00 CRITICAL 等級不存在") is None


def test_error_wins_over_info():
    assert extract_level("2026-07-22T10:00:00 INFO 等級不存在ERROR") == "ERROR"


def test_counter_empty_list():
    assert count_levels([]) == Counter([])


def test_counter_no_level():
    assert count_levels(["2026-07-22T10:00:00 CRITICAL 等級不存在"]) == Counter([])


def test_counter_same_level():
    assert count_levels(
        ["2026-07-22T10:00:01 INFO 服務啟動", "2026-07-22T10:00:00 INFO 等級不存在"]
    ) == Counter({"INFO": 2})


def test_counter_multi_level():
    assert count_levels(["2026-07-22T10:00:00 INFO 等級不存在ERROR"]) == Counter({"ERROR": 1})


def test_counter_single_key():
    result = count_levels(
        ["2026-07-22T10:00:01 INFO 服務啟動", "2026-07-22T10:00:00 INFO 等級不存在"]
    )
    assert result["INFO"] == 2

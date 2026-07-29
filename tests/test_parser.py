from collections import Counter

import pytest

from logcli.parser import count_levels, extract_level


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

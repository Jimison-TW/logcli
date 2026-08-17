from pathlib import Path

import pytest


@pytest.fixture
def sample_log_file(tmp_path: Path) -> Path:
    # tmp_path 是一個 Path,指向一個空的暫存目錄
    file = tmp_path / "test.log"  # ← Path 用 / 接路徑(≈ path.join),不是字串拼接
    file.write_text(
        "2026-07-22T10:00:00 ERROR 資料庫 連線 失敗\n2026-07-22T10:00:00 CRITICAL 等級不存在",
        encoding="utf-8",
    )
    return file


@pytest.fixture
def make_test_case(tmp_path: Path):
    log = tmp_path / "test.log"

    def _make(test_content):  # ← 內部函式，收參數
        log.write_text(
            test_content,
            encoding="utf-8",
        )
        return log

    return _make  # ← 回傳「函式本身」，不是呼叫它

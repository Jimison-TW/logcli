# logcli

[![CI](https://github.com/Jimison-TW/logcli/actions/workflows/ci.yml/badge.svg)](https://github.com/Jimison-TW/logcli/actions/workflows/ci.yml)

一個日誌解析 CLI 工具（前端轉 Python 學習專案，Week 4 會擴充成完整的日誌分析工具）。

## 功能

- `logcli parse <file>`：解析 log 檔，統計各等級數量
- `--level INFO|WARN|ERROR`：只看某個等級
- `--top N`：顯示最常見的前 N 個等級
- `--format text|table`：輸出格式，`table` 用 [rich](https://github.com/Textualize/rich) 畫漂亮表格（預設 `text`）
- `--json`：以 JSON 輸出統計結果
- `--output report.csv|report.xlsx`：把統計結果寫成 CSV / Excel 報表（依副檔名判斷）
- `--since / --until`：只統計某時間區間內的 log（如 `--since 2026-01-01`）
- `-v / --verbose`：開 DEBUG log

## 安裝

```bash
pip install -e .
```

## 使用範例

```bash
# 基本統計 + 取前 3 名等級
logcli parse app.log --top 3

# 用 rich 表格輸出等級統計
logcli parse app.log --format table
```

`--format table` 的輸出：

```text
    Log 等級統計
┏━━━━━━━┳━━━━━━━┓
┃ level ┃ count ┃
┡━━━━━━━╇━━━━━━━┩
│ ERROR │     2 │
│ WARN  │     1 │
└───────┴───────┘
```

```bash
# 只看 ERROR、寫成 CSV 報表
logcli parse app.log --level ERROR --output report.csv

# 過濾時間區間
logcli parse app.log --since 2026-01-01 --until 2026-01-31
```

## 測試

```bash
pytest -v
```

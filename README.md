# logcli

一個日誌解析 CLI 工具（前端轉 Python 學習專案，Week 4 會擴充成完整的日誌分析工具）。

## 功能

- `logcli parse <file>`：解析 log 檔，統計各等級數量
- `--level INFO|WARN|ERROR`：只看某個等級
- `--top N`：顯示最常見的前 N 個等級
- `--json`：以 JSON 輸出統計結果
- `-v / --verbose`：開 DEBUG log

## 安裝

```bash
pip install -e .
```

## 測試

```bash
pytest -v
```

## 技術筆記

- [前端轉 Python 的 6 個工程化差異（W1）](../docs/W1技術筆記.md)

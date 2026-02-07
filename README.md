# Louvois Salary CLI

本專案以 **Python + CLI** 模擬法國軍隊失敗的薪資系統（Louvois）。專案重點如下：

1. **純 CLI**：僅使用命令列操作，沒有資料庫或網頁介面。
2. **基本資料放在 `data/`**：人員、軍種、單位、軍銜等基礎資料以 JSON、enum 等形式存放於 `data/` 資料夾。
3. **專案文件放在 `docs/`**：所有設計說明與文件集中在 `docs/`。

## 專案結構

```
.
├── main.py
├── README.md
├── data/
└── docs/
```

## 文件位置

- `docs/user_stories/`：使用者故事
- `docs/domain_rules/`：Domain Rule Card（YAML）

## 快速開始

```bash
python3 main.py
python3 main.py | tee output/005.csv
```

# Louvois Salary

本專案用多個版本演進方式，模擬法國軍隊失敗的薪資系統（Louvois）的規則與資料流。

## 版本規劃

- **v1 (CLI 版 / Python)**：以 CLI + JSON 資料為主，全部邏輯集中於 `main.py`（教學/示範用）
- 已實作規則：**R001–R405（共 32 條）**
- **專案文件放在 `docs/`**：所有設計說明與文件集中在 `docs/`。
- **基本資料放在 `data/`**：人員、軍種、單位、軍銜等基礎資料以 JSON、enum 等形式存放於 `data/` 資料夾。

## 快速開始

```bash
python main.py
python main.py | tee output/005.csv
```

## 文件索引

- `docs/user_stories/`：所有使用者故事
- `docs/domain_rules/`：所有 Domain Rule Card
- `docs/PROJECT_v1.md`：v1 專案目標與版本規劃


## 專案結構

```
.
├── main.py
├── README.md
├── data/
└── docs/
```

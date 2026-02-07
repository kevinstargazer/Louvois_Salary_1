# 專案文件：Louvois Salary CLI

本文件描述此專案的目標、範圍與文件結構。

## 目標

- 以 Python + CLI 模擬法國軍隊失敗的薪資系統（Louvois）。
- 用可重現、可測試的方式呈現薪資計算與資料流。

## 範圍與限制

- 介面：僅 CLI，不含資料庫與網頁。
- 資料來源：基礎資料以 JSON、enum 等格式存放在 `data/`。
- 規則與需求：以使用者故事為主體，集中存放於 `docs/user_stories/`。
- 為了模擬最糟情況，全部邏輯寫在 `main.py`，且僅使用基本的 `if`、`for`。
- CLI 會輸出執行時間（`runtime_seconds=...`）。

## 文件結構

- `docs/PROJECT.md`：本文件，描述專案總覽。
- `docs/基本資料配置指南.md`：基本資料的配置與格式建議。
- `docs/基本資料規則.md`：基本資料的規則說明。
- `docs/58種薪資規則.md`：薪資規則清單來源文件。
- `docs/user_stories/`：使用者故事與規則拆分（共 58 條規則）。
- `docs/domain_rules/`：Domain Rule Card（YAML 格式）。

## 專案資料

- `data/branch_enum.py`：軍種 Enum。
- `data/rank_enum.py`：軍階 Enum。
- `data/units.json`：單位資料（30 筆）。
- `data/employees.json`：人員資料（30 筆）。
- `data/missions.json`：派遣任務資料（15 筆）。
- `data/rules.json`：薪資規則（已建立第一筆 R001）。
- `main.py`：CLI 入口。

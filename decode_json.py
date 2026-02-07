import json

input_file = "data/rules.json"
output_file = "data/rules_01.json"

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ 解碼完成，輸出檔案：decoded.json")

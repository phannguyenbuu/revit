import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r"scratch\columns_for_revit.json", encoding="utf-8") as f:
    cols = json.load(f)

for c in cols:
    if abs(c["x"] - 15.250) < 0.01 and abs(c["y"] - 5.300) < 0.01:
        print("Column B-5:", c)
    if abs(c["x"] - 18.850) < 0.01:
        print(f"Column at X=18.850 (Trục 6): Y={c['y']} -> {c['symbol_name']}")

import json

with open(r"scratch\cad_selection_analyzed.json", encoding="utf-8") as f:
    data = json.load(f)

print("--- CUA SO items ---")
for it in data["items"]:
    if it["layer"] == "CUA SO":
        print(f"{it['type']} {it['handle']} box={it['box_rvt']}")

print("\n--- COT items ---")
for it in data["items"]:
    if it["layer"] == "COT":
        print(f"{it['type']} {it['handle']} box={it['box_rvt']}")

print("\n--- Net-02 items ---")
for it in data["items"]:
    if it["layer"] == "Net-02":
        print(f"{it['type']} {it['handle']} box={it['box_rvt']}")

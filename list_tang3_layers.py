import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_tang3_extracted.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]

layers = {}
for it in items:
    lay = it['layer']
    obj = it['objectName']
    key = f"{lay} | {obj}"
    layers[key] = layers.get(key, 0) + 1

for k, v in sorted(layers.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k}: {v}")

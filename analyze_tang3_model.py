import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_tang3_extracted.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]

DX = 10587.5
DY = 1400406.0

def to_rvt(x, y):
    return round((x + DX) / 1000.0, 4), round((y + DY) / 1000.0, 4)

# 1. Texts
print("=== TEXTS IN TANG 3 ===")
texts = []
for it in items:
    if 'text' in it:
        t = it['text'].strip()
        ins = it['insertion']
        rx, ry = to_rvt(ins[0], ins[1])
        texts.append({"text": t, "rvt": [rx, ry], "layer": it['layer']})

for t in texts:
    print(f"  '{t['text']}' at {t['rvt']} ({t['layer']})")

# 2. Blocks
print("\n=== BLOCKS IN TANG 3 ===")
blocks = []
for it in items:
    if 'blockName' in it:
        bn = it['blockName']
        ins = it['insertion']
        rx, ry = to_rvt(ins[0], ins[1])
        blocks.append({"block": bn, "rvt": [rx, ry], "layer": it['layer']})

door_blocks = [b for b in blocks if any(k in b['block'].upper() for k in ['C1000', 'CD2C', 'DNB', 'CUA'])]
print(f"Door blocks ({len(door_blocks)}):")
for db in door_blocks:
    print(f"  {db['block']} at {db['rvt']}")

# 3. Wall polylines & lines (S5)
s5_polys = [it for it in items if it['layer'] == 'S5']
print(f"\nTotal S5 items: {len(s5_polys)}")

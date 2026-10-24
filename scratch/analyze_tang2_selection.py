import json
import os

json_path = r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang2.json'
with open(json_path, 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"Total items in selection: {len(items)}")

# 1. Blocks
blocks = [it for it in items if it['type'] == 'AcDbBlockReference']
print(f"\n--- Block References ({len(blocks)}) ---")
block_names = {}
for b in blocks:
    name = b['name']
    block_names[name] = block_names.get(name, 0) + 1
for name, count in sorted(block_names.items(), key=lambda x: -x[1]):
    print(f"  {name}: {count}")

for b in blocks:
    print(f"  Block '{b['name']}' at ({b['point'][0]:.2f}, {b['point'][1]:.2f}), rot={b['rot']:.1f}, layer={b['layer']}")

# 2. Texts and Tags
texts = [it for it in items if it['type'] in ('AcDbText', 'AcDbMText')]
print(f"\n--- Texts ({len(texts)}) ---")
for t in texts:
    print(f"  [{t['layer']}] at ({t['point'][0]:.2f}, {t['point'][1]:.2f}): {t['text']}")

# 3. Lines and Polylines by Layer
print("\n--- Entities by Layer ---")
layer_counts = {}
for it in items:
    lay = it['layer']
    layer_counts[lay] = layer_counts.get(lay, 0) + 1
for lay, c in sorted(layer_counts.items(), key=lambda x: -x[1]):
    print(f"  Layer {lay}: {c} items")

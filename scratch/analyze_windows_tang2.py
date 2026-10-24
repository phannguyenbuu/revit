import json
import math

with open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang2.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

# Find all window tags in TBI (tags starting with S, K, HG)
win_tags = [it for it in items if it['type'] == 'AcDbText' and it['layer'] in ('TBI', 'Chu thich-0.25') and any(it['text'].startswith(prefix) for prefix in ['S', 'K', 'HG'])]
print(f"Total window tags: {len(win_tags)}")
for wt in sorted(win_tags, key=lambda w: (round(w['point'][1], 1), round(w['point'][0], 1))):
    print(f"  Tag {wt['text']} at ({wt['point'][0]:.2f}, {wt['point'][1]:.2f})")

# Let's inspect window blocks KH-CUA
kh_cua = [it for it in items if it['type'] == 'AcDbBlockReference' and it.get('name') == 'KH-CUA']
print(f"\nKH-CUA blocks: {len(kh_cua)}")
for b in kh_cua:
    print(f"  KH-CUA at ({b['point'][0]:.2f}, {b['point'][1]:.2f})")

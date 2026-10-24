import json

with open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang_tum.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print(f"Total items: {len(d['items'])}")

by_layer = {}
for item in d['items']:
    by_layer.setdefault(item['layer'], []).append(item)

for layer, items in by_layer.items():
    print(f"\n--- LAYER: {layer} ({len(items)} items) ---")
    for it in items:
        info = f"{it['objectName']} (Handle={it['handle']})"
        if 'text' in it:
            info += f" TEXT='{it['text']}'"
        if 'blockName' in it:
            info += f" BLOCK='{it['blockName']}' @ {it.get('insertion')}"
        if 'bbox' in it:
            b = it['bbox']
            info += f" bbox=[({b['min'][0]:.1f}, {b['min'][1]:.1f}) - ({b['max'][0]:.1f}, {b['max'][1]:.1f})]"
        print("  ", info)

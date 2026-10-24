import json
import re

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_tang3_extracted.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]

DX = 10587.5
DY = 1400406.0

def to_rvt(x, y):
    return round((x + DX) / 1000.0, 4), round((y + DY) / 1000.0, 4)

# 1. Parse Texts
vni_map = {
    'VIEC': 'VIỆC', 'PHO': 'PHÓ', 'TRNG': 'TRƯỞNG', 'NGH': 'NGHỈ',
    'TRC': 'TRỰC', 'HOI': 'HỘI', 'KE': 'KẾ', 'TOAN': 'TOÁN',
    'HOP': 'HỌP', 'VA': 'VÀ', 'LAM': 'LÀM', 'NÖÕ': 'NỮ', 'N': 'NỮ',
    'm': 'm²'
}

def clean_vni(txt):
    # remove formatting like {\fVNI-Avo|b0|i0|c0|p2; ... }
    txt = re.sub(r'\{[^{}]*\}', '', txt)
    txt = re.sub(r'\\[A-Za-z0-9]+;?', ' ', txt)
    txt = txt.replace(r'\P', '\n')
    for k, v in vni_map.items():
        txt = txt.replace(k, v)
    # clean extra spaces
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    return '\n'.join(lines)

parsed_texts = []
door_tags = []
window_tags = []

for it in items:
    if 'text' in it:
        raw = it['text'].strip()
        ins = it['insertion']
        rx, ry = to_rvt(ins[0], ins[1])
        lay = it['layer']
        
        # Check if door tag
        if re.match(r'^D[1-9]$', raw):
            door_tags.append({"tag": raw, "pos": [rx, ry], "handle": it['handle']})
        # Check if window tag
        elif re.match(r'^[SK][1-9]$', raw):
            window_tags.append({"tag": raw, "pos": [rx, ry], "handle": it['handle']})
        else:
            clean = clean_vni(raw)
            if clean:
                parsed_texts.append({
                    "raw": raw,
                    "clean": clean,
                    "pos": [rx, ry],
                    "layer": lay
                })

print(f"Door tags ({len(door_tags)}): {[d['tag'] for d in door_tags]}")
print(f"Window tags ({len(window_tags)}): {[w['tag'] for w in window_tags]}")
print(f"Room texts ({len(parsed_texts)}):")
for pt in parsed_texts:
    lines = pt['clean'].split('\n')
    print(f"  {lines} at {pt['pos']}")

out = {
    "door_tags": door_tags,
    "window_tags": window_tags,
    "room_texts": parsed_texts
}

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\tang3_parsed_tags.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

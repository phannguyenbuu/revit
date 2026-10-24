import sys, json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\tang2_creation_data.json", "r", encoding="utf-8") as f:
    t2 = json.load(f)

for w in t2['walls']:
    if 'WC' in w['id']:
        print(w)

import json

with open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_tang3_extracted.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]

# Blocks
blocks = {}
for it in items:
    if 'blockName' in it:
        b = it['blockName']
        blocks[b] = blocks.get(b, 0) + 1

print("Block counts:")
for b, c in sorted(blocks.items(), key=lambda x: x[1], reverse=True)[:25]:
    print(f"  {b}: {c}")

# Texts
texts = []
for it in items:
    if 'text' in it:
        texts.append(it['text'])

print(f"\nTotal texts: {len(texts)}")
print("Sample texts:")
for t in texts[:30]:
    print(f"  '{t}'")

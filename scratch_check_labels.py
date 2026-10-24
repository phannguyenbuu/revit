import re

content = open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\AppData\Local\Temp\screen_entities.json', encoding='utf-8', errors='ignore').read()
matches = re.findall(r'"text":\s*"([^"]+)"', content)
numbers = sorted(list(set(int(m) for m in matches if m.isdigit() and 1 <= int(m) <= 30)))
print("Numbers found in screen_entities:", numbers)

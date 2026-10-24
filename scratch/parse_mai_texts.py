import re

with open('C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/mai_texts.json', 'r', encoding='latin-1') as f:
    content = f.read()

pattern = re.compile(r'\(([\d\.\+\-e]+)\s+([\d\.\+\-e]+)\s+\"([^\"]*)\"\s+\"([^\"]*)\"\)')
matches = pattern.findall(content)
print(f"Total matches: {len(matches)}")
for x, y, txt, lyr in matches:
    x_val = float(x)
    y_val = float(y)
    u = txt.upper()
    if any(k in u for k in ['MAU', 'MAT', 'BANG', 'TUM', 'TANG', 'SAN', '14', '17', '10', 'TL', 'KT', '+']):
        print(f"{x_val:.1f}, {y_val:.1f} [{lyr}]: {txt}")

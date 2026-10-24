import sys
import os
import json
import urllib.request

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Query Revit Model Info
data = json.loads(urllib.request.urlopen('http://127.0.0.1:8090/api/model').read().decode('utf-8'))
levels = data.get('levels', [])
grids = data.get('grids', [])

print("--- LEVELS ---")
for l in levels:
    print(f"ID: {l.get('id')}, Name: {l.get('name')}, Elev: {l.get('elevation')}")

print("\n--- GRIDS ---")
for g in sorted(grids, key=lambda x: (x.get('startX', 0), x.get('startY', 0))):
    print(f"Grid '{g.get('name')}': start=({round(g.get('startX', 0), 2)}, {round(g.get('startY', 0), 2)}) -> end=({round(g.get('endX', 0), 2)}, {round(g.get('endY', 0), 2)})")

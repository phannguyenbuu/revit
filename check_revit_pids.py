import psutil
for p in psutil.process_iter(['pid', 'name']):
    name = (p.info['name'] or '').lower()
    if 'revit' in name:
        print(f"PID: {p.pid}, Name: {p.info['name']}")

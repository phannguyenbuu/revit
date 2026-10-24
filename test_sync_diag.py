import urllib.request
import json
import os
import sys

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

print("--- 1. Testing 3ds Max Bridge (8096) ---")
try:
    max_req = urllib.request.Request(
        "http://127.0.0.1:8096/api/execute",
        data=json.dumps({"code": "(if selection.count > 0 then (local s = selection[1]; s.name + '|' + (s.pos as string) + '|' + (classof s as string)) else 'NO_SELECTION')"}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(max_req, timeout=5) as res:
        print("3ds Max Response:", res.read().decode('utf-8'))
except Exception as e:
    print("3ds Max Error:", e)

print("\n--- 2. Testing Revit Bridge (8090) ---")
try:
    revit_req = urllib.request.Request(
        "http://127.0.0.1:8090/api/execute",
        data=json.dumps({"action": "save_document"}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(revit_req, timeout=5) as res:
        print("Revit Response:", res.read().decode('utf-8'))
except Exception as e:
    print("Revit Error:", e)

print("\n--- 3. Running sync_max_to_revit.py --no-gui ---")
os.system(f'"{sys.executable}" d:\\Dropbox\\_Documents\\RevitAI\\sync_max_to_revit.py --no-gui')

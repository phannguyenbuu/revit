import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
from web_dashboard import app

client = app.test_client()

# Test Scan
res = client.post('/api/execute-action', json={
    'action': 'scan_cad_titleblocks',
    'scope': 'selection',
    'sortMode': 'x_then_y',
    'skipEmpty': True
})
data = res.get_json()
print('Status:', res.status_code)
print('Success:', data.get('success'))
print('Message:', data.get('message'))
print('Items count:', len(data.get('items', [])))
for it in data.get('items', []):
    print(f"[{it['stt']:02d}] {it['title']} ({it['sheetType']}) | Region: ({it['xmin']:.1f}, {it['ymin']:.1f}) -> ({it['xmax']:.1f}, {it['ymax']:.1f})")

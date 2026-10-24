import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
from web_dashboard import app

client = app.test_client()

# Test GET /api/cadlib-lisps
res = client.get('/api/cadlib-lisps')
data = res.get_json()
print("Status code:", res.status_code)
print("Success:", data.get("success"))
print("Total files:", data.get("totalFiles"))
print("Total commands:", data.get("totalCommands"))
print("Categories:", data.get("categories"))
print("First item:", data.get("items", [])[0]["file"], "->", data.get("items", [])[0]["commands"])

# Test action load_cad_lisp with 4HLR.lsp
first_lisp = data.get("items", [])[0]["fullPath"]
res2 = client.post('/api/execute-action', json={
    "action": "load_cad_lisp",
    "filePath": first_lisp
})
print("Load LISP result:", res2.status_code, res2.get_json())

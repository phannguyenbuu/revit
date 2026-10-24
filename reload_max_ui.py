import urllib.request
import json

mxs = """
(
    python.ExecuteFile @"d:\\Dropbox\\_Documents\\RevitAI\\3dsmax\\max_bridge.py"
    "OK"
)
"""

req = urllib.request.Request(
    'http://127.0.0.1:8096/api/execute',
    data=json.dumps({'language': 'maxscript', 'code': mxs}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req, timeout=10) as res:
    print(res.read().decode('utf-8'))

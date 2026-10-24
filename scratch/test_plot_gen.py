import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
from web_dashboard import app

client = app.test_client()

# First scan
res_scan = client.post('/api/execute-action', json={
    'action': 'scan_cad_titleblocks',
    'scope': 'selection',
    'sortMode': 'x_then_y',
    'skipEmpty': True
})
items = res_scan.get_json().get('items', [])

# Test generate batch plot script
res_plot = client.post('/api/execute-action', json={
    'action': 'batch_plot_cad',
    'subAction': 'generate_only',
    'items': items,
    'plotDevice': 'DWG To PDF.pc3',
    'paperSize': 'ISO_full_bleed_A3_(420.00_x_297.00_MM)',
    'plotStyle': 'monochrome.ctb'
})
data = res_plot.get_json()
print('Plot status:', res_plot.status_code)
print('Plot success:', data.get('success'))
print('Plot message:', data.get('message'))
print('Script path:', data.get('scriptPath'))
print('Output dir:', data.get('outputDir'))

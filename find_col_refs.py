import os
import re

files_to_check = [
    'column_cad_exporter.py',
    'column_plan_cad_exporter.py',
    'beam_plan_cad_exporter.py',
    'web_dashboard.py',
    'deploy_etabs.py',
    'static/js/etabs_hub.js',
    'templates/index.html',
    'etabs_service.py'
]

for f in files_to_check:
    if not os.path.exists(f):
        continue
    content = open(f, encoding='utf-8').read()
    matches = []
    for line_idx, line in enumerate(content.splitlines()):
        if any(w in line for w in ['C18', '18 Cột', '18 C\u1ed9t', '18x4', '18\u00d74', 'C7', 'C8', 'C9', 'C10']):
            matches.append((line_idx + 1, line.strip()))
    if matches:
        print(f"=== {f} ({len(matches)} matches) ===")
        for lno, txt in matches[:10]:
            print(f"  L{lno}: {txt[:100]}".encode('ascii', errors='replace').decode('ascii'))
        if len(matches) > 10:
            print(f"  ... and {len(matches) - 10} more")

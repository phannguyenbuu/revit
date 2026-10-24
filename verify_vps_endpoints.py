import urllib.request
import ezdxf
import os
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

endpoints = [
    ('/api/column-matrix', 'matrix_json'),
    ('/api/export-column-dxf', 'vps_column_cad.dxf'),
    ('/api/export-beam-plan-dxf?story=T3', 'vps_beam_plan.dxf'),
    ('/api/export-column-plan-dxf', 'vps_column_plan.dxf'),
    ('/api/export-tie-beam-dxf', 'vps_tie_beam.dxf'),
]

for ep, fname in endpoints:
    url = f'https://mr.pkld.online{ep}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            content = resp.read()
        if fname == 'matrix_json':
            data = json.loads(content.decode('utf-8'))
            cols = data['data']['column_labels']
            print(f"VPS /api/column-matrix: count={len(cols)}, labels={cols}")
        else:
            with open(fname, 'wb') as fp:
                fp.write(content)
            doc = ezdxf.readfile(fname)
            ltypes = [l.dxf.name for l in doc.linetypes]
            std_font = doc.styles.get('Standard').dxf.font if 'Standard' in doc.styles else 'N/A'
            has_dashdot = "DASHDOT" in ltypes
            has_dashed = "DASHED" in ltypes
            has_center = "CENTER" in ltypes
            print(f"VPS {fname}: size={len(content)}, font={std_font}, DASHDOT={has_dashdot}, DASHED={has_dashed}, CENTER={has_center}")
    except Exception as e:
        print(f"VPS {fname} error: {e}")

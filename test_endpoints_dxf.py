import urllib.request
import ezdxf
import io

endpoints = [
    ('/api/export-column-dxf', 'column_cad.dxf'),
    ('/api/export-beam-plan-dxf?story=T3', 'beam_plan.dxf'),
    ('/api/export-column-plan-dxf', 'column_plan.dxf'),
    ('/api/export-tie-beam-dxf', 'tie_beam.dxf'),
]

for ep, fname in endpoints:
    url = f'http://127.0.0.1:5000{ep}'
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            content = resp.read()
        doc = ezdxf.read(io.StringIO(content.decode('utf-8')))
        ltypes = [l.dxf.name for l in doc.linetypes]
        std_font = doc.styles.get('Standard').dxf.font if 'Standard' in doc.styles else 'N/A'
        has_dashdot = "DASHDOT" in ltypes
        has_dashed = "DASHED" in ltypes
        print(f"{fname}: size={len(content)}, font={std_font}, DASHDOT={has_dashdot}, DASHED={has_dashed}")
    except Exception as e:
        print(f"{fname} error: {e}")

import re

files = [
    'beam_cad_exporter.py',
    'tie_beam_cad_exporter.py',
    'column_cad_exporter.py',
    'beam_plan_cad_exporter.py',
    'column_plan_cad_exporter.py'
]

for f in files:
    content = open(f, encoding='utf-8').read()
    styles = set(re.findall(r'style[\'\"]?\s*[:=]\s*[\'\"]([^\'\"]+)[\'\"]', content))
    dimstyles = set(re.findall(r'dimstyle[\'\"]?\s*[:=]\s*[\'\"]([^\'\"]+)[\'\"]', content))
    print(f"{f}: styles={styles}, dimstyles={dimstyles}")

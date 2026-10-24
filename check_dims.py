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
    dim_calls = re.findall(r'add_\w*dim\w*', content)
    print(f"{f}: dim calls = {set(dim_calls)}")

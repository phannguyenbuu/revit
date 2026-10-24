import sys, json
sys.stdout.reconfigure(encoding='utf-8')

with open('etabs_beam_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

beams = data.get('beams', [])
print(f'Total beams in etabs_beam_data.json: {len(beams)}')

groups = {}
for b in beams:
    st = b.get('story', 'T1')
    l_id = b.get('long_beam_id') or b.get('label')
    key = f'{st}::{l_id}'
    if key not in groups:
        groups[key] = {'story': st, 'long_beam_id': l_id, 'spans': []}
    groups[key]['spans'].append(b)

print(f'Total long beam groups: {len(groups)}')

MAIN_CATALOG = [
    {'label': '2D18', 'count': 2, 'diam': 18, 'area': 5.09},
    {'label': '3D18', 'count': 3, 'diam': 18, 'area': 7.63},
    {'label': '4D18', 'count': 4, 'diam': 18, 'area': 10.18},
    {'label': '2D20', 'count': 2, 'diam': 20, 'area': 6.28},
    {'label': '3D20', 'count': 3, 'diam': 20, 'area': 9.42},
    {'label': '4D20', 'count': 4, 'diam': 20, 'area': 12.57},
    {'label': '2D22', 'count': 2, 'diam': 22, 'area': 7.60},
    {'label': '3D22', 'count': 3, 'diam': 22, 'area': 11.40},
    {'label': '4D22', 'count': 4, 'diam': 22, 'area': 15.21},
    {'label': '2D25', 'count': 2, 'diam': 25, 'area': 9.82},
    {'label': '3D25', 'count': 3, 'diam': 25, 'area': 14.73},
    {'label': '4D25', 'count': 4, 'diam': 25, 'area': 19.63}
]

EXTRA_CATALOG = [
    {'label': '0', 'count': 0, 'diam': 0, 'area': 0},
    {'label': '1D16', 'count': 1, 'diam': 16, 'area': 2.01},
    {'label': '2D16', 'count': 2, 'diam': 16, 'area': 4.02},
    {'label': '1D18', 'count': 1, 'diam': 18, 'area': 2.54},
    {'label': '2D18', 'count': 2, 'diam': 18, 'area': 5.09},
    {'label': '1D20', 'count': 1, 'diam': 20, 'area': 3.14},
    {'label': '2D20', 'count': 2, 'diam': 20, 'area': 6.28},
    {'label': '1D22', 'count': 1, 'diam': 22, 'area': 3.80},
    {'label': '2D22', 'count': 2, 'diam': 22, 'area': 7.60},
    {'label': '1D25', 'count': 1, 'diam': 25, 'area': 4.91},
    {'label': '2D25', 'count': 2, 'diam': 25, 'area': 9.82}
]

def select_extra(deficit):
    if deficit <= 0.0001:
        return {'label': '0', 'area': 0}
    cands = [x for x in EXTRA_CATALOG if x['area'] >= deficit]
    if cands:
        cands.sort(key=lambda x: x['area'])
        return cands[0]
    return EXTRA_CATALOG[-1]

tc_lung = []
tc_bung = []
thieu_thep = []

for key, g in sorted(groups.items()):
    chain = g['spans']
    maxAsTopL = max(b.get('as_top_left_cm2', 0) for b in chain)
    maxAsBotM = max(b.get('as_bot_mid_cm2', 0) for b in chain)
    maxAsTopR = max(b.get('as_top_right_cm2', 0) for b in chain)
    maxAsTop = max(maxAsTopL, maxAsTopR)
    maxB = max(b.get('width', 200) for b in chain)
    minBars = 3 if maxB >= 300 else 2
    
    optMainTop = [x for x in MAIN_CATALOG if x['count'] >= minBars and x['diam'] >= 18]
    if maxAsTop >= 8.5:
        c20 = [x for x in optMainTop if x['diam'] >= 20]
        if c20: optMainTop = c20
    chosenTop = optMainTop[0] if optMainTop else MAIN_CATALOG[0]

    optMainBot = [x for x in MAIN_CATALOG if x['count'] >= minBars and x['diam'] >= 18]
    if maxAsBotM >= 7.0:
        c20b = [x for x in optMainBot if x['diam'] >= 20]
        if c20b: optMainBot = c20b
    chosenBot = optMainBot[0] if optMainBot else MAIN_CATALOG[0]

    extraL = select_extra(maxAsTopL - chosenTop['area'])
    extraM = select_extra(maxAsBotM - chosenBot['area'])
    extraR = select_extra(maxAsTopR - chosenTop['area'])

    has_tc_lung = (extraL['area'] > 0 or extraR['area'] > 0)
    has_tc_bung = (extraM['area'] > 0)

    for span in chain:
        reqL = span.get('as_top_left_cm2', 0)
        reqM = span.get('as_bot_mid_cm2', 0)
        reqR = span.get('as_top_right_cm2', 0)
        capL = chosenTop['area'] + extraL['area']
        capM = chosenBot['area'] + extraM['area']
        capR = chosenTop['area'] + extraR['area']
        if reqL > capL or reqM > capM or reqR > capR:
            thieu_thep.append((key, span.get('label')))

    if has_tc_lung:
        tc_lung.append((key, f"Lưng: L={extraL['label']}, R={extraR['label']} (y/c={maxAsTop:.2f}, chủ={chosenTop['label']})"))
    if has_tc_bung:
        tc_bung.append((key, f"Bụng: {extraM['label']} (y/c={maxAsBotM:.2f}, chủ={chosenBot['label']})"))

print(f'\n--- DẦM CÓ THÉP TĂNG CƯỜNG LƯNG ({len(tc_lung)} dầm) ---')
for k, info in tc_lung:
    print(f'  {k}: {info}')

print(f'\n--- DẦM CÓ THÉP TĂNG CƯỜNG BỤNG ({len(tc_bung)} dầm) ---')
for k, info in tc_bung:
    print(f'  {k}: {info}')

print(f'\n--- DẦM THIẾU THÉP ({len(thieu_thep)} dầm) ---')
for item in thieu_thep:
    print(f'  {item}')

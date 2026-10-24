import revit_cli
import json
import urllib.request

base = revit_cli.get_base_url()
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.TestSimulateBandRefs',
    'methodName': 'Run'
}
req = urllib.request.Request(base + '/api/execute', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode())
ab = data.get('abSorted', [])
cd = data.get('cdSorted', [])

# Simulate buildCuratedChain for AB
ab_targets = [
    550, 700, 800, 900,
    1750, 3150, # D2-1
    4250, 4350, 4450,
    5950, 7350, # D2-2
    7950, 8050, 8150,
    8750, 10150, # D2-3
    11550, 11650, 11750,
    13150, 14550, # D2-4
    15150, 15250, 15350,
    15550, 16550, # D4-1
    18750, 18850, 18950,
    22350, 22450, 22550,
    22650, 23650, # D4-2
    25950, 26050, 26150,
    29550, 29650, 29750,
    30050, 31050, # D4-3
    33250, 33350, 33450,
    34750, 35550, # D5
    35650, 35950, 36150, 36850, 37050, 37150, 37550
]

chosen_ab = []
for t in ab_targets:
    match = [x for x in ab if abs(x - t) <= 45.0]
    if match:
        m = min(match, key=lambda x: abs(x - t))
        if not any(abs(c - m) < 45.0 for c in chosen_ab):
            chosen_ab.append(m)
chosen_ab.sort()

print("=== Clean AB Chosen Count ===", len(chosen_ab))
segs_ab = [round(chosen_ab[i+1] - chosen_ab[i], 1) for i in range(len(chosen_ab)-1)]
print("AB Segments:", segs_ab)

# Simulate buildCuratedChain for CD
cd_targets = [
    550, 700, 800, 900,
    1800, 2100, 3000, 3300,
    4250, 4350,
    4450, 5750, # D7-1
    7950, 8050, 8150,
    8387, 9387, # D4-1
    11550, 11650, 11750,
    15150, 15250, 15350,
    15487, 16487, # D4-2
    18750, 18850, 18950,
    20250, 21250, # D4-3
    22350, 22450, 22550,
    22862, 23862, # D4-4
    24337, 25337, # D4-5
    25950, 26050, 26150,
    28412, 29412, # D4-6
    29550, 29650, 29750,
    31950, 33150, # D7-2
    33250, 33350, 33450,
    33550, 34350, # D5
    34550, 34650, 34900, 35000, 35250, 37000, 37050, 37150,
    37350, 37450, 37550
]

chosen_cd = []
for t in cd_targets:
    match = [x for x in cd if abs(x - t) <= 45.0]
    if match:
        m = min(match, key=lambda x: abs(x - t))
        if not any(abs(c - m) < 45.0 for c in chosen_cd):
            chosen_cd.append(m)
chosen_cd.sort()

print("=== Clean CD Chosen Count ===", len(chosen_cd))
segs_cd = [round(chosen_cd[i+1] - chosen_cd[i], 1) for i in range(len(chosen_cd)-1)]
print("CD Segments:", segs_cd)

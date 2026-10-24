import json

data = json.load(open('etabs_beam_data.json', encoding='utf-8'))
for st in ['T1', 'T2']:
    print(f"=== STORY {st} ===")
    row = [b for b in data['beams'] if b['story'] == st and abs((b['p1'][1] + b['p2'][1]) / 2) < 350]
    row.sort(key=lambda b: min(b['p1'][0], b['p2'][0]))
    for idx, b in enumerate(row):
        lbl = b.get('label')
        as_l = b.get('as_top_left_cm2')
        as_m = b.get('as_bot_mid_cm2')
        as_r = b.get('as_top_right_cm2')
        reb_l = b.get('rebar_top_left')
        reb_m = b.get('rebar_bot_mid')
        reb_r = b.get('rebar_top_right')
        sec = b.get('section')
        length = b.get('length')
        print(f"Span {idx+1}: {lbl} ({sec}, L={length}) | AsReq: L={as_l}, M={as_m}, R={as_r} | Rebar: L={reb_l}, M={reb_m}, R={reb_r}")

import sys
import json
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
data = json.load(open('detailed_elements.json', encoding='utf-8'))
walls = data['walls']

# Define grid lines
X_AXES = [550, 4350, 8050, 11650, 15250, 18850, 22450, 26050, 29650, 33350, 37150]
Y_A = 100 # or 0
Y_B = 5300 # or 5400
Y_C = 7900 # or 7800
Y_D = 13100 # or 13200
Y_E = 14900

def get_recommended_top_offset(w):
    # If it's one of the facade pier walls with top offset 1500, leave it
    if w['topOffMm'] == 1500:
        return 1500, "Facade pier (unchanged)"
    
    # If base level is sân vườn or no top level, ignore
    if not w['topLevel']:
        return w['topOffMm'], "No top level"

    dir = w['dir']
    x0, y0, x1, y1 = w['x0'], w['y0'], w['x1'], w['y1']
    mid_x = (x0 + x1) / 2.0
    mid_y = (y0 + y1) / 2.0

    if dir == 'X':
        # Wall parallel to X (along Y = const)
        # Check if near Trục A (~0..100), B (~5300..5400), C (~7800..7900), D (~13100..13200), E (~14900)
        if abs(mid_y - 0) < 200 or abs(mid_y - 100) < 200:
            return -350, "Beam 220X350 (Trục A)"
        elif abs(mid_y - 5300) < 200 or abs(mid_y - 5400) < 200:
            return -350, "Beam 220X350 (Trục B)"
        elif abs(mid_y - 7800) < 200 or abs(mid_y - 7900) < 200:
            return -350, "Beam 220X350 (Trục C)"
        elif abs(mid_y - 13100) < 200 or abs(mid_y - 13200) < 200:
            return -350, "Beam 220X350 (Trục D)"
        elif abs(mid_y - 14900) < 200:
            return -350, "Beam 220X350 (Trục E)"
        else:
            # Internal partition wall under slab
            return -100, "Partition under slab 100mm"

    else:
        # Wall parallel to Y (along X = const)
        # Check if near one of the 11 column axes
        near_axis = any(abs(mid_x - ax) < 200 for ax in X_AXES)
        if near_axis:
            # Check Y range
            if mid_y < 5350:
                # Span A-B (5.2m)
                return -500, "Beam 220X500 (Nhịp A-B 5.2m)"
            elif 5250 <= mid_y <= 7950:
                # Span B-C (2.6m)
                return -350, "Beam 220X350 (Nhịp B-C 2.6m hành lang)"
            elif 7850 <= mid_y <= 13150:
                # Span C-D (5.2m)
                return -500, "Beam 220X500 (Nhịp C-D 5.2m)"
            elif mid_y > 13100:
                # Span D-E (1.8m)
                return -350, "Beam 220X350 (Nhịp D-E 1.8m thang)"
            else:
                return -350, "Beam 220X350"
        else:
            # Partition wall not on grid axis (e.g. WC or room division)
            return -100, "Partition under slab 100mm"

results = []
summary = defaultdict(int)
for w in walls:
    off, reason = get_recommended_top_offset(w)
    summary[(w['baseLevel'], off, reason)] += 1
    results.append({'id': w['id'], 'base': w['baseLevel'], 'top': w['topLevel'], 'oldOff': w['topOffMm'], 'newOff': off, 'reason': reason})

print("=== PROPOSED WALL TOP OFFSET SUMMARY ===")
for (base, off, reason), count in sorted(summary.items(), key=lambda x: str(x[0])):
    print(f"[{base}] -> Top Offset: {off}mm ({count} walls) -- {reason}")

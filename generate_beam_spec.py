import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

# Coordinates in mm - EXACT GRID LINES
X_AXES = [550, 4350, 8050, 11650, 15250, 18850, 22450, 26050, 29650, 33350, 37150]

Y_A = 0      # Trục A: Y = 0 (trùng tim tường Trục A)
Y_B = 5400   # Trục B: Y = 5400 (trùng tim tường Trục B)
Y_C = 7800   # Trục C: Y = 7800 (trùng tim tường Trục C)
Y_D = 13200  # Trục D: Y = 13200 (trùng tim tường Trục D)
Y_E = 14900  # Trục E: Y = 14900 (trùng tim tường Trục E)

# Levels:
# Level 2: Id 694, 3.6m
# Level 3: Id 1727584, 7.2m
# Level 4: Id 2360634, 10.8m
# Level Tum: Id 2360635, 14.4m
# Level Mái: Id 1209118, 17.2m

def generate_beams_for_typical_floor(level_id, level_name):
    beams = []
    # 1. Transverse Beams (Ngang nhà, strictly dx = 0)
    for x in X_AXES:
        # A-B (500)
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X500', 'p0': (x, Y_A), 'p1': (x, Y_B), 'tag': 'AB'})
        # B-C (350)
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x, Y_B), 'p1': (x, Y_C), 'tag': 'BC'})
        # C-D (500)
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X500', 'p0': (x, Y_C), 'p1': (x, Y_D), 'tag': 'CD'})
        # D-E (350) at stair bays
        if x in [4350, 8050, 29650, 33350]:
            beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x, Y_D), 'p1': (x, Y_E), 'tag': 'DE'})
    
    # 2. Longitudinal Beams (Dọc nhà, strictly dy = 0)
    for i in range(len(X_AXES) - 1):
        x0 = X_AXES[i]
        x1 = X_AXES[i+1]
        # Trục A (350)
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x0, Y_A), 'p1': (x1, Y_A), 'tag': 'A'})
        # Trục B (350)
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x0, Y_B), 'p1': (x1, Y_B), 'tag': 'B'})
        # Trục C (350)
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x0, Y_C), 'p1': (x1, Y_C), 'tag': 'C'})
        # Trục D (350)
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x0, Y_D), 'p1': (x1, Y_D), 'tag': 'D'})
    
    # Trục E (350)
    beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (4350, Y_E), 'p1': (8050, Y_E), 'tag': 'E'})
    beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (29650, Y_E), 'p1': (33350, Y_E), 'tag': 'E'})
    return beams

def generate_beams_for_tum_floor():
    level_id = 2360635
    level_name = "MẶT BẰNG TẦNG TUM"
    beams = []
    # Transverse
    # Nhịp A-B at Trục 4, 5, 6, 7, 8
    for x in [11650, 15250, 18850, 22450, 26050]:
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X500', 'p0': (x, Y_A), 'p1': (x, Y_B), 'tag': 'AB'})
    # Nhịp B-C at Trục 2 to 11
    for x in X_AXES[1:]:
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x, Y_B), 'p1': (x, Y_C), 'tag': 'BC'})
    # Nhịp C-D at Trục 2 to 11
    for x in X_AXES[1:]:
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X500', 'p0': (x, Y_C), 'p1': (x, Y_D), 'tag': 'CD'})
    # Nhịp D-E at 4350, 8050, 29650, 33350
    for x in [4350, 8050, 29650, 33350]:
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x, Y_D), 'p1': (x, Y_E), 'tag': 'DE'})
    
    # Longitudinal
    # Trục A between 4, 5, 6, 7, 8 (strictly dy = 0)
    tum_a_x = [11650, 15250, 18850, 22450, 26050]
    for i in range(len(tum_a_x) - 1):
        x0, x1 = tum_a_x[i], tum_a_x[i+1]
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x0, Y_A), 'p1': (x1, Y_A), 'tag': 'A'})
    
    # Trục B, C, D from Trục 2 to 11 (strictly dy = 0)
    for i in range(1, len(X_AXES) - 1):
        x0, x1 = X_AXES[i], X_AXES[i+1]
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x0, Y_B), 'p1': (x1, Y_B), 'tag': 'B'})
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x0, Y_C), 'p1': (x1, Y_C), 'tag': 'C'})
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x0, Y_D), 'p1': (x1, Y_D), 'tag': 'D'})
    
    # Trục E (strictly dy = 0)
    beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (4350, Y_E), 'p1': (8050, Y_E), 'tag': 'E'})
    beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (29650, Y_E), 'p1': (33350, Y_E), 'tag': 'E'})
    return beams

def generate_beams_for_mai_tum():
    level_id = 1209118
    level_name = "MẶT BẰNG MÁI"
    beams = []
    # Transverse at Trục 9 and 10 (strictly dx = 0)
    for x in [29650, 33350]:
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x, Y_C), 'p1': (x, Y_D), 'tag': 'CD'})
        beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (x, Y_D), 'p1': (x, Y_E), 'tag': 'DE'})
    
    # Longitudinal (strictly dy = 0)
    beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (29650, Y_C), 'p1': (33350, Y_C), 'tag': 'C'})
    beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (29650, Y_D), 'p1': (33350, Y_D), 'tag': 'D'})
    beams.append({'lvlId': level_id, 'lvlName': level_name, 'type': '220X350', 'p0': (29650, Y_E), 'p1': (33350, Y_E), 'tag': 'E'})
    return beams

all_beams = []
b2 = generate_beams_for_typical_floor(694, "MẶT BẰNG TẦNG 2")
b3 = generate_beams_for_typical_floor(1727584, "MẶT BẰNG TẦNG 3")
b4 = generate_beams_for_typical_floor(2360634, "MẶT BẰNG TẦNG 4")
btum = generate_beams_for_tum_floor()
bmai = generate_beams_for_mai_tum()

all_beams.extend(b2)
all_beams.extend(b3)
all_beams.extend(b4)
all_beams.extend(btum)
all_beams.extend(bmai)

print(f"Total beams to generate: {len(all_beams)}")

# Verify 100% straightness:
crooked = [b for b in all_beams if abs(b['p0'][0] - b['p1'][0]) > 0.1 and abs(b['p0'][1] - b['p1'][1]) > 0.1]
print(f"Crooked beams count: {len(crooked)}")
assert len(crooked) == 0, "There should be NO crooked beams!"

with open('beam_specs.json', 'w', encoding='utf-8') as f:
    json.dump(all_beams, f, indent=2, ensure_ascii=False)
print("Saved beam_specs.json with 100% straight grid-aligned beams!")

import json
import math

with open(r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\cad_selection_tang2.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

# 1. Door Arcs
arcs = [it for it in items if it['type'] == 'AcDbArc' and it['layer'] == 'A-Door']
print(f"Total door arcs in A-Door: {len(arcs)}")

# 2. Door Tags in TBI
door_tags = [it for it in items if it['type'] == 'AcDbText' and it['layer'] == 'TBI' and it['text'].startswith('D')]
print(f"Total door tags: {len(door_tags)}")
for dt in door_tags:
    print(f"  Tag {dt['text']} at ({dt['point'][0]:.2f}, {dt['point'][1]:.2f})")

# Let's match each arc with its closest door tag and door center
doors = []
for a in arcs:
    cx, cy = a['center'][0], a['center'][1]
    r = a['radius']
    sa, ea = a['startAngle'], a['endAngle']
    
    # find closest tag
    best_tag = None
    min_dist = float('inf')
    for dt in door_tags:
        dist = math.hypot(cx - dt['point'][0], cy - dt['point'][1])
        if dist < min_dist:
            min_dist = dist
            best_tag = dt['text']
            
    doors.append({
        'center': (round(cx, 3), round(cy, 3)),
        'radius_m': round(r, 3),
        'startAngle_deg': round(math.degrees(sa), 1),
        'endAngle_deg': round(math.degrees(ea), 1),
        'tag': best_tag,
        'tag_dist': round(min_dist, 2)
    })

doors.sort(key=lambda d: (d['center'][1], d['center'][0]))
print("\n--- Identified Doors from Arcs ---")
for i, d in enumerate(doors):
    print(f"  Door {i+1}: Tag={d['tag']} (dist={d['tag_dist']}m) center=({d['center'][0]:.2f}, {d['center'][1]:.2f}), width={d['radius_m']*1000:.0f}mm, angles=[{d['startAngle_deg']}, {d['endAngle_deg']}]")

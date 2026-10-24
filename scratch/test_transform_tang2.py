import json

with open('scratch/cad_selected_tang2.json') as f:
    data = json.load(f)

verts = data['vertices']
print(f"Total vertices in raw CAD: {len(verts)}")

if verts[0] == verts[-1]:
    unique_verts = verts[:-1]
else:
    unique_verts = verts

print(f"Unique polygon vertices: {len(unique_verts)}")
print("\nExact Transformation: X_revit = X_cad + 70953.54, Y_revit = Y_cad + 1400405.9")
header = f"{'Idx':4s} | {'CAD X':10s} {'CAD Y':12s} | {'Revit X':10s} {'Revit Y':10s} | {'Round50 X':10s} {'Round50 Y':10s} | {'Diff X':8s} {'Diff Y':8s}"
print(header)
print("-" * len(header))

for i, (xc, yc) in enumerate(unique_verts):
    xr = xc + 70953.54
    yr = yc + 1400405.9
    
    xr_round = round(xr / 50.0) * 50.0
    yr_round = round(yr / 50.0) * 50.0
    
    diff_x = xr_round - xr
    diff_y = yr_round - yr
    
    print(f"{i:4d} | {xc:10.2f} {yc:12.2f} | {xr:10.2f} {yr:10.2f} | {xr_round:10.1f} {yr_round:10.1f} | {diff_x:8.2f} {diff_y:8.2f}")

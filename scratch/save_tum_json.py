import os, json

brain_scratch = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch"
os.makedirs(brain_scratch, exist_ok=True)

outer_verts = [
    {"idx": 0, "name": "West Terrace South return", "x": 4250.0, "y": 4800.0},
    {"idx": 1, "name": "Middle Bay Terr South edge", "x": 11050.0, "y": 4800.0},
    {"idx": 2, "name": "Axis 4 South edge", "x": 11050.0, "y": -100.0},
    {"idx": 3, "name": "SE Corner (Wall 11 / Wall A)", "x": 37250.0, "y": -100.0},
    {"idx": 4, "name": "NE Corner (Wall 11 / Wall D)", "x": 37250.0, "y": 13300.0},
    {"idx": 5, "name": "East Stair Well East-Top", "x": 33250.0, "y": 13300.0},
    {"idx": 6, "name": "East Stair Well SE notch", "x": 33250.0, "y": 10100.0},
    {"idx": 7, "name": "East Stair Well SW notch", "x": 29750.0, "y": 10100.0},
    {"idx": 8, "name": "East Stair Well West-Top", "x": 29750.0, "y": 13300.0},
    {"idx": 9, "name": "West Stair Well East-Top", "x": 8150.0, "y": 13300.0},
    {"idx": 10, "name": "West Stair Well North-East", "x": 8150.0, "y": 15000.0},
    {"idx": 11, "name": "West Stair Well North-West", "x": 4250.0, "y": 15000.0}
]

hole_verts = [
    {"idx": 0, "name": "Hole NW", "x": 5650.0, "y": 13100.0},
    {"idx": 1, "name": "Hole NE", "x": 6750.0, "y": 13100.0},
    {"idx": 2, "name": "Hole SE", "x": 6750.0, "y": 9700.0},
    {"idx": 3, "name": "Hole SW", "x": 5650.0, "y": 9700.0}
]

data = {
    "cad_handle_outer": "4B7DA5",
    "cad_handle_hole": "44D972",
    "cad_layer_outer": "NET HAT MONG",
    "cad_layer_hole": "CHU",
    "cad_drawing_title": "MẶT BẰNG TẦNG TUM",
    "delta_x_mm": -113999.09,
    "delta_y_mm": 1400405.90,
    "outer_vertices": outer_verts,
    "hole_vertices": hole_verts
}

for path in ["scratch/cad_selected_tum_with_hole.json", os.path.join(brain_scratch, "cad_selected_tum_with_hole.json")]:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved to {path}")

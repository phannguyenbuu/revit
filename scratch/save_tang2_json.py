import os, json

# Ensure scratch directory in brain folder exists
brain_scratch = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch"
os.makedirs(brain_scratch, exist_ok=True)

# 16 unique vertices after transformation to Revit (in mm) with 50mm rounding:
vertices_revit_mm = [
    {"idx": 0, "name": "West Stair Well East-Top", "x": 4450.0, "y": 13300.0},
    {"idx": 1, "name": "NW Corner (Wall 1 / Wall D)", "x": 450.0, "y": 13300.0},
    {"idx": 2, "name": "West Balcony North return", "x": 450.0, "y": 8800.0},
    {"idx": 3, "name": "West Balcony NW corner", "x": -4050.0, "y": 8800.0},
    {"idx": 4, "name": "West Balcony SW corner", "x": -4050.0, "y": 4400.0},
    {"idx": 5, "name": "West Balcony South return", "x": 450.0, "y": 4400.0},
    {"idx": 6, "name": "SW Corner (Wall 1 / Wall A)", "x": 450.0, "y": -100.0},
    {"idx": 7, "name": "SE Corner (Wall 11 / Wall A)", "x": 37250.0, "y": -100.0},
    {"idx": 8, "name": "NE Corner (Wall 11 / Wall D)", "x": 37250.0, "y": 13300.0},
    {"idx": 9, "name": "East Stair Well East-Top", "x": 33250.0, "y": 13300.0},
    {"idx": 10, "name": "East Stair Well SE notch", "x": 33250.0, "y": 10100.0},
    {"idx": 11, "name": "East Stair Well SW notch", "x": 29750.0, "y": 10100.0},
    {"idx": 12, "name": "East Stair Well West-Top", "x": 29750.0, "y": 13300.0},
    {"idx": 13, "name": "West Stair Well West-Top", "x": 7950.0, "y": 13300.0},
    {"idx": 14, "name": "West Stair Well SW notch", "x": 7950.0, "y": 10100.0},
    {"idx": 15, "name": "West Stair Well SE notch", "x": 4450.0, "y": 10100.0}
]

data = {
    "cad_handle": "4A7ED3",
    "cad_layer": "NET HAT MONG",
    "delta_x_mm": 70953.54,
    "delta_y_mm": 1400405.90,
    "rounding_step_mm": 50.0,
    "vertices_revit_mm": vertices_revit_mm
}

for path in ["scratch/cad_selected_tang2.json", os.path.join(brain_scratch, "cad_selected_tang2.json")]:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved to {path}")

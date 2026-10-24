import json
import math

# 1. Walls Definition for Tầng 2
# Coordinates are in meters
walls = [
    # --- EXTERIOR 200mm WALLS ---
    # South Wall A (Y = 0.00)
    {"id": "Wall_A", "type": "gach200_xay moi", "p1": [0.55, 0.00], "p2": [37.15, 0.00]},
    
    # Corridor South Wall B (Y = 5.40)
    {"id": "Wall_B", "type": "gach200_xay moi", "p1": [0.55, 5.40], "p2": [37.15, 5.40]},
    
    # Corridor North Wall C (Y = 7.80)
    {"id": "Wall_C_west", "type": "gach200_xay moi", "p1": [0.55, 7.80], "p2": [4.35, 7.80]},
    {"id": "Wall_C_stair1", "type": "gach200_xay moi", "p1": [4.35, 7.80], "p2": [8.05, 7.80]},
    {"id": "Wall_C_mid", "type": "gach200_xay moi", "p1": [8.05, 7.80], "p2": [29.65, 7.80]},
    {"id": "Wall_C_stair2", "type": "gach200_xay moi", "p1": [29.65, 7.80], "p2": [33.35, 7.80]},
    {"id": "Wall_C_east", "type": "gach200_xay moi", "p1": [33.35, 7.80], "p2": [37.15, 7.80]},
    
    # North Wall D (Y = 13.20)
    {"id": "Wall_D_west", "type": "gach200_xay moi", "p1": [0.55, 13.20], "p2": [4.35, 13.20]},
    {"id": "Wall_D_mid", "type": "gach200_xay moi", "p1": [8.05, 13.20], "p2": [29.65, 13.20]},
    {"id": "Wall_D_east", "type": "gach200_xay moi", "p1": [33.35, 13.20], "p2": [37.15, 13.20]},
    
    # Stair 1 Towers (Trục 2-3, Y: 7.80 to 14.90)
    {"id": "Wall_Stair1_Left", "type": "gach200_xay moi", "p1": [4.35, 7.80], "p2": [4.35, 14.90]},
    {"id": "Wall_Stair1_Right", "type": "gach200_xay moi", "p1": [8.05, 7.80], "p2": [8.05, 14.90]},
    {"id": "Wall_Stair1_Back", "type": "gach200_xay moi", "p1": [4.35, 14.90], "p2": [8.05, 14.90]},
    
    # Stair 2 Towers (Trục 9-10, Y: 7.80 to 14.90)
    {"id": "Wall_Stair2_Left", "type": "gach200_xay moi", "p1": [29.65, 7.80], "p2": [29.65, 14.90]},
    {"id": "Wall_Stair2_Right", "type": "gach200_xay moi", "p1": [33.35, 7.80], "p2": [33.35, 14.90]},
    {"id": "Wall_Stair2_Back", "type": "gach200_xay moi", "p1": [29.65, 14.90], "p2": [33.35, 14.90]},
    
    # Outer End Walls: West (Trục 1) & East (Trục 11)
    {"id": "Wall_1", "type": "gach200_xay moi", "p1": [0.55, 0.00], "p2": [0.55, 13.20]},
    {"id": "Wall_11", "type": "gach200_xay moi", "p1": [37.15, 0.00], "p2": [37.15, 13.20]},
    
    # --- INTERIOR PARTITION WALLS ---
    # South Row Partitions (Y: 0.00 to 5.40)
    {"id": "Wall_Part_X4.35_S", "type": "gach200_xay moi", "p1": [4.35, 0.00], "p2": [4.35, 5.40]},
    {"id": "Wall_Part_X8.05_S", "type": "gach200_xay moi", "p1": [8.05, 0.00], "p2": [8.05, 5.40]},
    {"id": "Wall_Part_X15.25_S", "type": "gach200_xay moi", "p1": [15.25, 0.00], "p2": [15.25, 5.40]},
    {"id": "Wall_Part_X22.45_S", "type": "gach200_xay moi", "p1": [22.45, 0.00], "p2": [22.45, 5.40]},
    {"id": "Wall_Part_X33.35_S", "type": "gach200_xay moi", "p1": [33.35, 0.00], "p2": [33.35, 5.40]},
    
    # North Row Partitions (Y: 7.80 to 13.20)
    {"id": "Wall_Part_X11.65_N", "type": "gach200_xay moi", "p1": [11.65, 7.80], "p2": [11.65, 13.20]},
    {"id": "Wall_Part_X15.25_N", "type": "gach200_xay moi", "p1": [15.25, 7.80], "p2": [15.25, 13.20]},
    {"id": "Wall_Part_X22.45_N", "type": "gach200_xay moi", "p1": [22.45, 7.80], "p2": [22.45, 13.20]},
    {"id": "Wall_Part_X26.05_N", "type": "gach200_xay moi", "p1": [26.05, 7.80], "p2": [26.05, 13.20]},
    
    # West Bay Partition (Trục 2, Y: 5.40 to 7.80)
    {"id": "Wall_Part_X4.35_Mid", "type": "gach200_xay moi", "p1": [4.35, 5.40], "p2": [4.35, 7.80]},
    
    # East Bay WC Partitions (X: 33.35 to 37.15, Y: 7.80 to 13.20)
    {"id": "Wall_WC_Horiz_Y9.45", "type": "gach100_xay moi", "p1": [33.35, 9.45], "p2": [37.15, 9.45]},
    {"id": "Wall_WC_Stall_X35.0", "type": "gach100_xay moi", "p1": [35.00, 7.80], "p2": [35.00, 8.45]},
    {"id": "Wall_WC_Stall_Y8.45", "type": "gach100_xay moi", "p1": [35.00, 8.45], "p2": [36.15, 8.45]}
]

# 2. Doors Definition for Tầng 2
doors = [
    # Doors D4 on Wall B (Y = 5.40)
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 3.56, "y": 5.40, "hostWallId": "Wall_B"},
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 7.26, "y": 5.40, "hostWallId": "Wall_B"},
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 14.46, "y": 5.40, "hostWallId": "Wall_B"},
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 16.03, "y": 5.40, "hostWallId": "Wall_B"},
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 23.13, "y": 5.40, "hostWallId": "Wall_B"},
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 30.53, "y": 5.40, "hostWallId": "Wall_B"},
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 34.26, "y": 5.40, "hostWallId": "Wall_B"},
    
    # Doors D4 on Wall C (Y = 7.80)
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 12.61, "y": 7.80, "hostWallId": "Wall_C_mid"},
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 20.91, "y": 7.80, "hostWallId": "Wall_C_mid"},
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 25.08, "y": 7.80, "hostWallId": "Wall_C_mid"},
    
    # Doors D4 on North Partitions
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 11.65, "y": 12.39, "hostWallId": "Wall_Part_X11.65_N"},
    {"tag": "D4", "symbol": "D4_1000x2200", "x": 26.05, "y": 12.39, "hostWallId": "Wall_Part_X26.05_N"},
    
    # Doors D7 on Stair Bay Walls (Y = 7.80)
    {"tag": "D7", "symbol": "D4_1000x2200", "x": 5.22, "y": 7.80, "hostWallId": "Wall_C_stair1"},
    {"tag": "D7", "symbol": "D4_1000x2200", "x": 32.17, "y": 7.80, "hostWallId": "Wall_C_stair2"},
    
    # Doors D5 on WC Wall (Y = 9.45)
    {"tag": "D5", "symbol": "D5_800x2200", "x": 33.49, "y": 9.45, "hostWallId": "Wall_WC_Horiz_Y9.45"},
    {"tag": "D5", "symbol": "D5_800x2200", "x": 34.54, "y": 9.45, "hostWallId": "Wall_WC_Horiz_Y9.45"}
]

# 3. Windows Definition for Tầng 2
windows = [
    # Windows S1 on South Wall A (Y = 0.00)
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 6.07, "y": 0.00, "hostWallId": "Wall_A", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 9.64, "y": 0.00, "hostWallId": "Wall_A", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 13.22, "y": 0.00, "hostWallId": "Wall_A", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 16.92, "y": 0.00, "hostWallId": "Wall_A", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 20.45, "y": 0.00, "hostWallId": "Wall_A", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 24.14, "y": 0.00, "hostWallId": "Wall_A", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 27.60, "y": 0.00, "hostWallId": "Wall_A", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 31.32, "y": 0.00, "hostWallId": "Wall_A", "sill": 0.90},
    
    # Windows S1 on North Wall D (Y = 13.20)
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 9.69, "y": 13.20, "hostWallId": "Wall_D_mid", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 13.29, "y": 13.20, "hostWallId": "Wall_D_mid", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 16.89, "y": 13.20, "hostWallId": "Wall_D_mid", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 20.49, "y": 13.20, "hostWallId": "Wall_D_mid", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 24.09, "y": 13.20, "hostWallId": "Wall_D_mid", "sill": 0.90},
    {"tag": "S1", "symbol": "S1_1500x1400", "x": 27.85, "y": 13.20, "hostWallId": "Wall_D_mid", "sill": 0.90},
    
    # Window S4 on North Wall D (Y = 13.20, WC NAM)
    {"tag": "S4", "symbol": "S4_1500x1400", "x": 34.37, "y": 13.20, "hostWallId": "Wall_D_east", "sill": 0.90},
    
    # Windows S2 on West Wall 1 (X = 0.55)
    {"tag": "S2", "symbol": "S1_1500x1400", "x": 0.55, "y": 3.52, "hostWallId": "Wall_1", "sill": 0.90},
    {"tag": "S2", "symbol": "S1_1500x1400", "x": 0.55, "y": 9.45, "hostWallId": "Wall_1", "sill": 0.90},
    
    # Windows S3 on East Wall 11 (X = 37.15)
    {"tag": "S3", "symbol": "900X1900", "x": 37.15, "y": 10.86, "hostWallId": "Wall_11", "sill": 0.90},
    {"tag": "S3", "symbol": "900X1900", "x": 37.15, "y": 12.03, "hostWallId": "Wall_11", "sill": 0.90},
    
    # Windows K3 on Stair Towers (Wall E, Y = 14.90)
    {"tag": "K3", "symbol": "K3_3100x2100", "x": 6.01, "y": 14.90, "hostWallId": "Wall_Stair1_Back", "sill": 0.90},
    {"tag": "K3", "symbol": "K3_3100x2100", "x": 31.31, "y": 14.90, "hostWallId": "Wall_Stair2_Back", "sill": 0.90}
]

# 4. Room & Tag Texts Definition
texts = [
    # Rooms
    {"text": "P. KHÁCH\n24m²", "x": 2.77, "y": 3.51, "type": "3.5mm Arial"},
    {"text": "KHO HỒ SƠ\n12m²", "x": 6.66, "y": 3.49, "type": "3.5mm Arial"},
    {"text": "P. LÀM VIỆC (3 CBCS)\n36m²", "x": 11.41, "y": 3.64, "type": "3.5mm Arial"},
    {"text": "P. LÀM VIỆC (3 CBCS)\n36m²", "x": 18.85, "y": 3.64, "type": "3.5mm Arial"},
    {"text": "P. LÀM VIỆC (5 CBCS)\n60m²", "x": 28.47, "y": 3.64, "type": "3.5mm Arial"},
    {"text": "P. VĂN THƯ\n18m²", "x": 35.35, "y": 3.48, "type": "3.5mm Arial"},
    {"text": "P. LÀM VIỆC LL THAM GIA BẢO VỆ ANTT\n18m²", "x": 2.58, "y": 10.76, "type": "3.5mm Arial"},
    {"text": "P. NGHỈ TRỰC\nPHÓ TRƯỞNG CAX\n14m²", "x": 9.68, "y": 11.38, "type": "3.5mm Arial"},
    {"text": "P. LÀM VIỆC\nPHÓ TRƯỞNG CAX\n21m²", "x": 13.17, "y": 11.38, "type": "3.5mm Arial"},
    {"text": "P. TRUYỀN THỐNG\n36m²", "x": 19.03, "y": 11.47, "type": "3.5mm Arial"},
    {"text": "P. LÀM VIỆC\nPHÓ TRƯỞNG CAX\n21m²", "x": 24.52, "y": 11.38, "type": "3.5mm Arial"},
    {"text": "P. NGHỈ TRỰC\nPHÓ TRƯỞNG CAX\n14m²", "x": 28.12, "y": 11.38, "type": "3.5mm Arial"},
    {"text": "WC NAM\nS=13m²", "x": 34.32, "y": 11.48, "type": "3.5mm Arial"},
    {"text": "WC NỮ\nS=3.5m²", "x": 35.54, "y": 9.08, "type": "3.5mm Arial"},
    
    # Door Tags
    {"text": "D4", "x": 3.41, "y": 5.94, "type": "2.5mm Arial"},
    {"text": "D4", "x": 7.08, "y": 5.86, "type": "2.5mm Arial"},
    {"text": "D4", "x": 14.30, "y": 5.95, "type": "2.5mm Arial"},
    {"text": "D4", "x": 15.89, "y": 5.90, "type": "2.5mm Arial"},
    {"text": "D4", "x": 23.03, "y": 5.94, "type": "2.5mm Arial"},
    {"text": "D4", "x": 30.33, "y": 5.85, "type": "2.5mm Arial"},
    {"text": "D4", "x": 34.14, "y": 5.88, "type": "2.5mm Arial"},
    {"text": "D4", "x": 12.33, "y": 7.12, "type": "2.5mm Arial"},
    {"text": "D4", "x": 20.72, "y": 7.15, "type": "2.5mm Arial"},
    {"text": "D4", "x": 24.99, "y": 7.12, "type": "2.5mm Arial"},
    {"text": "D4", "x": 10.72, "y": 12.22, "type": "2.5mm Arial"},
    {"text": "D4", "x": 26.60, "y": 12.22, "type": "2.5mm Arial"},
    {"text": "D7", "x": 5.22, "y": 8.07, "type": "2.5mm Arial"},
    {"text": "D7", "x": 32.17, "y": 8.07, "type": "2.5mm Arial"},
    {"text": "D5", "x": 33.74, "y": 9.65, "type": "2.5mm Arial"},
    {"text": "D5", "x": 34.79, "y": 8.88, "type": "2.5mm Arial"},
    
    # Window Tags
    {"text": "S1", "x": 6.07, "y": -0.68, "type": "2.5mm Arial"},
    {"text": "S1", "x": 9.64, "y": -0.68, "type": "2.5mm Arial"},
    {"text": "S1", "x": 13.22, "y": -0.68, "type": "2.5mm Arial"},
    {"text": "S1", "x": 16.92, "y": -0.68, "type": "2.5mm Arial"},
    {"text": "S1", "x": 20.45, "y": -0.68, "type": "2.5mm Arial"},
    {"text": "S1", "x": 24.14, "y": -0.68, "type": "2.5mm Arial"},
    {"text": "S1", "x": 27.60, "y": -0.72, "type": "2.5mm Arial"},
    {"text": "S1", "x": 31.32, "y": -0.68, "type": "2.5mm Arial"},
    {"text": "S1", "x": 9.69, "y": 12.42, "type": "2.5mm Arial"},
    {"text": "S1", "x": 13.29, "y": 12.42, "type": "2.5mm Arial"},
    {"text": "S1", "x": 16.89, "y": 12.42, "type": "2.5mm Arial"},
    {"text": "S1", "x": 20.49, "y": 12.42, "type": "2.5mm Arial"},
    {"text": "S1", "x": 24.09, "y": 12.42, "type": "2.5mm Arial"},
    {"text": "S1", "x": 27.85, "y": 12.42, "type": "2.5mm Arial"},
    {"text": "S4", "x": 34.37, "y": 12.57, "type": "2.5mm Arial"},
    {"text": "S2", "x": -0.19, "y": 3.52, "type": "2.5mm Arial"},
    {"text": "S2", "x": -0.21, "y": 9.45, "type": "2.5mm Arial"},
    {"text": "S3", "x": 37.72, "y": 10.86, "type": "2.5mm Arial"},
    {"text": "S3", "x": 37.75, "y": 12.03, "type": "2.5mm Arial"},
    {"text": "K3", "x": 6.01, "y": 14.50, "type": "2.5mm Arial"},
    {"text": "K3", "x": 31.31, "y": 14.50, "type": "2.5mm Arial"}
]

data = {
    "walls": walls,
    "doors": doors,
    "windows": windows,
    "texts": texts
}

out_path = r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\tang2_creation_data.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Data prepared successfully: {len(walls)} walls, {len(doors)} doors, {len(windows)} windows, {len(texts)} texts.")

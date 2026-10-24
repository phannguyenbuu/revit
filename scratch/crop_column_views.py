from PIL import Image

im = Image.open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_columns_all_result.png")
w, h = im.size

# Crop 1: Right zone (WC zone, Trục 9 to 11, Trục A to E)
# In image coords, right ~ 70% to 100% of width
crop1 = im.crop((int(w * 0.70), int(h * 0.10), int(w * 0.98), int(h * 0.90)))
crop1.save(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\crop_columns_wc_zone.png")

# Crop 2: Left zone (Stairs left, Trục 1 to 4)
crop2 = im.crop((int(w * 0.02), int(h * 0.10), int(w * 0.35), int(h * 0.90)))
crop2.save(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\crop_columns_left_zone.png")

# Crop 3: Middle zone (Trục 4 to 8)
crop3 = im.crop((int(w * 0.32), int(h * 0.15), int(w * 0.72), int(h * 0.85)))
crop3.save(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\crop_columns_middle_zone.png")

print("Cropped successfully!")

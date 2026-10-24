from PIL import Image

img = Image.open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\acad_topmost.png")
w, h = img.size

# Bottom middle-right area: x from 30% to 75%, y from 50% to 80%
crop_box = (int(w * 0.30), int(h * 0.50), int(w * 0.75), int(h * 0.80))
cropped = img.crop(crop_box)
crop_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\crop_k1_zone.png"
cropped.save(crop_path)
print(f"Saved crop to {crop_path}")

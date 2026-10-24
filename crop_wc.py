from PIL import Image

# plan_tang2_perfect.png resolution is 3800 wide
# Crop coordinates of view were X in [-2.5, 39.5] (width 42m), Y in [-3.5, 16.5] (height 20m)
img = Image.open(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\plan_tang2_perfect.png")
w, h = img.size

# WC is at X in [32, 37.2], Y in [7.5, 10]
# Revit view bounds:
# X: [-2.5, 39.5] -> width 42.0m
# Y: [-3.5, 16.5] -> height 20.0m
# In image: X increases left to right, Y increases bottom to top
def to_pixel(x, y):
    px = int((x - (-2.5)) / 42.0 * w)
    py = int((16.5 - y) / 20.0 * h)
    return px, py

x1, y1 = to_pixel(32.0, 11.0)
x2, y2 = to_pixel(37.5, 7.0)

crop = img.crop((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
crop.save(r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\scratch\wc_revit_crop.png")
print("Cropped WC area from Revit plan")

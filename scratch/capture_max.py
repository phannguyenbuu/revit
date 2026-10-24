import os
import sys

try:
    from PIL import ImageGrab
    im = ImageGrab.grab()
    out_path = r"D:\Dropbox\_Documents\RevitAI\scratch\max_screen_updated.png"
    im.save(out_path)
    print("Screenshot saved to", out_path)
except Exception as e:
    print("Error:", e)

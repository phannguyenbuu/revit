import os
import sys
import shutil
import comtypes.client
from comtypes.gen import ETABSv1

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def test_open():
    src = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\CAI TAO .EDB"
    dst = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\CAI TAO _AUTOFIX.EDB"
    shutil.copy2(src, dst)
    print(f"Copied {src} -> {dst}")
    
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    sap = app.SapModel
    print("Opening file...")
    ret = sap.File.OpenFile(dst)
    print(f"File opened! ret = {ret}")
    
    # Check model
    print("Model title:", sap.GetModelFilename())
    app.ApplicationExit(False)
    print("Exit OK")

if __name__ == "__main__":
    test_open()

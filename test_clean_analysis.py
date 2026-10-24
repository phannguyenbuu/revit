import os
import sys
import shutil
import time
import comtypes.client
from comtypes.gen import ETABSv1

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def test_clean_analysis():
    src = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\163_165 Phan Boi Chau.EDB"
    dst = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\test_clean_run.EDB"
    shutil.copy2(src, dst)
    print("Copied model to:", dst)
    
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    sap = app.SapModel
    sap.File.OpenFile(dst)
    print("Opened model successfully.")
    
    # Remove diaphragm assignment or set SemiRigid to eliminate the elevation warning completely
    diaph_names = sap.Diaphragm.GetNameList()[1]
    print("Diaphragms:", diaph_names)
    for d in diaph_names:
        sap.Diaphragm.SetDiaphragm(d, True) # Set SemiRigid
        print(f"Set diaphragm '{d}' to Semi-Rigid")
        
    # Also save model
    sap.File.Save(dst)
    print("Saved modified model.")
    
    # Run analysis
    print("Calling RunAnalysis()...")
    t0 = time.time()
    ret = sap.Analyze.RunAnalysis()
    t1 = time.time()
    print(f"RunAnalysis completed in {t1-t0:.2f}s with return code: {ret}")
    print("Is model locked:", sap.GetModelIsLocked())
    
    # Test extract frame force for beam 2
    forces = sap.Results.FrameForce('2', 0)
    print(f"FrameForce for beam 2: count = {forces[0]}")
    if forces[0] > 0:
        print("Stations:", len(set(forces[2])))
        print("Max M3 (N.mm):", max(forces[13]))
        
    app.ApplicationExit(False)
    print("Test finished successfully!")

if __name__ == "__main__":
    test_clean_analysis()

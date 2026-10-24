import os
import sys
import comtypes.client
from comtypes.gen import ETABSv1

def main():
    edb_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\CAI TAO .EDB"
    print(f"Connecting to ETABS OAPI to read: {edb_path}")
    
    helper = comtypes.client.CreateObject('ETABSv1.Helper')
    helper = helper.QueryInterface(ETABSv1.cHelper)
    
    # Try connecting to active registered instance first
    app = None
    try:
        app = helper.GetObject("CSI.ETABS.API.ETABSObject")
        print("Connected to active ETABS instance via GetObject!")
    except Exception as e:
        print("GetObject failed:", e)
        
    if not app:
        print("Launching new ETABS OAPI session...")
        app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
        ret = app.ApplicationStart()
        print("ApplicationStart code:", ret)
        app.SetAsActiveObject()
        
    sap = app.SapModel
    current_file = sap.GetModelFilename()
    print("Current open file in ETABS:", current_file)
    
    if not current_file or "CAI TAO" not in current_file:
        print(f"Opening model {edb_path}...")
        ret = sap.File.OpenFile(edb_path)
        print("OpenFile return code:", ret)
        
    print("--------------------------------------------------")
    print(" MODEL SUMMARY:")
    print(" - File:", sap.GetModelFilename())
    print(" - Analysis Locked:", sap.GetModelIsLocked())
    print(" - Version:", sap.GetVersion())
    
    # Stories
    try:
        story_ret = sap.Story.GetNameList()
        # In comtypes, out parameters are returned as tuple: (ret_code, num, names)
        print(" - Stories count/names:", story_ret)
    except Exception as e:
        print(" - Story error:", e)
        
    # Frames
    try:
        total_frames = sap.FrameObj.Count()
        print(" - Total Frame Elements (Columns/Beams/Braces):", total_frames)
    except Exception as e:
        print(" - Frame error:", e)
        
    # Areas
    try:
        total_areas = sap.AreaObj.Count()
        print(" - Total Area Elements (Floors/Walls):", total_areas)
    except Exception as e:
        print(" - Area error:", e)
        
    # Materials
    try:
        mat_ret = sap.PropMaterial.GetNameList()
        print(" - Materials:", mat_ret)
    except Exception as e:
        print(" - Material error:", e)

    # Load Patterns
    try:
        loads_ret = sap.LoadPatterns.GetNameList()
        print(" - Load Patterns:", loads_ret)
    except Exception as e:
        print(" - Load patterns error:", e)
        
    print("--------------------------------------------------")
    print("OAPI interrogation successful!")

if __name__ == "__main__":
    main()

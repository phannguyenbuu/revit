import comtypes.client
from comtypes.gen import ETABSv1

def test_results():
    edb_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\CAI TAO .EDB"
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    
    app = None
    try:
        app = helper.GetObject("CSI.ETABS.API.ETABSObject")
    except Exception:
        pass
        
    if not app:
        app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
        app.ApplicationStart()
        app.SetAsActiveObject()
        
    sap = app.SapModel
    if not sap.GetModelFilename() or "CAI TAO" not in sap.GetModelFilename():
        sap.File.OpenFile(edb_path)
        
    print("Model loaded:", sap.GetModelFilename())
    print("Is locked (analyzed):", sap.GetModelIsLocked())
    
    # Check results setup
    ret = sap.Results.Setup.DeselectAllCasesAndCombosForOutput()
    print("DeselectAllCases:", ret)
    
    # Select TT or Combo1 if available
    try:
        sap.Results.Setup.SetCaseSelectedForOutput("TT")
        print("Selected case TT for output")
    except Exception as e:
        print("SetCaseSelectedForOutput error:", e)
        
    # Test Story Drifts
    try:
        # In CSI OAPI:
        # StoryDrifts(NumberResults, Story, LoadCase, StepType, StepNum, Direction, Drift, Label, Ret)
        res = sap.Results.StoryDrifts()
        print("StoryDrifts raw result tuple length:", len(res) if isinstance(res, (list, tuple)) else type(res))
        if isinstance(res, (list, tuple)):
            print("StoryDrifts sample:", res[:4])
    except Exception as e:
        print("StoryDrifts error:", e)
        
    # Test Base Reactions
    try:
        res = sap.Results.BaseReact()
        print("BaseReact raw result:", res)
    except Exception as e:
        print("BaseReact error:", e)

    # Let's inspect Frame names
    try:
        frame_names = sap.FrameObj.GetNameList()
        print("Frames count:", frame_names[0])
        first_frames = frame_names[1][:5] if frame_names[1] else []
        print("First 5 frames:", first_frames)
        
        if first_frames:
            f_name = first_frames[0]
            # FrameForce: (NumberResults, Obj, ObjSta, Elm, ElmSta, LoadCase, StepType, StepNum, P, V2, V3, T, M2, M3, ret)
            forces = sap.Results.FrameForce(f_name, 0) # 0 = Item
            print(f"FrameForce for {f_name} raw result length:", len(forces) if isinstance(forces, (list, tuple)) else type(forces))
    except Exception as e:
        print("FrameForce error:", e)

if __name__ == "__main__":
    test_results()

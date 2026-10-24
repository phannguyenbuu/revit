import sys
import comtypes.client

try:
    print("Testing ETABSv1.Helper...")
    helper = comtypes.client.CreateObject('ETABSv1.Helper')
    # QueryInterface if needed
    try:
        from comtypes.gen import ETABSv1
        helper = helper.QueryInterface(ETABSv1.cHelper)
    except Exception:
        pass
    
    etabs = helper.GetObject("CSI.ETABS.API.ETABSObject")
    sap_model = etabs.SapModel
    print("SUCCESS: Connected to running ETABS instance!")
    filename = sap_model.GetModelFilename()
    print("Current Model File:", filename if filename else "(New / Unsaved model)")
    print("Model Locked:", sap_model.GetModelIsLocked())
    
    # Get stories count
    try:
        num_stories = 0
        names = []
        ret = sap_model.Story.GetNameList(num_stories, names)
        print("Stories:", ret)
    except Exception as e:
        print("Story info error:", e)

except Exception as ex:
    print("ETABS connection error:", ex)
    import traceback
    traceback.print_exc()

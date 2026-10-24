import comtypes.client
from comtypes.gen import ETABSv1
import psutil

# Find running ETABS process
etabs_pids = []
for p in psutil.process_iter(['pid', 'name']):
    if 'etabs' in p.info['name'].lower():
        etabs_pids.append(p.info['pid'])

print(f"Found running ETABS PIDs: {etabs_pids}")
if not etabs_pids:
    print("No ETABS process found.")
    exit(1)

pid = etabs_pids[0]
print(f"Connecting to ETABS PID {pid}...")

helper = comtypes.client.CreateObject('ETABSv1.Helper')
helper = helper.QueryInterface(ETABSv1.cHelper)

obj = helper.GetObjectProcess("CSI.ETABS.API.ETABSObject", pid)
print("Result cOAPI object:", obj)

if obj:
    sap = obj.SapModel
    print("==================================================")
    print(" SUCCESS! CONNECTED TO ACTIVE ETABS INSTANCE!")
    print("==================================================")
    print(" - Model File :", sap.GetModelFilename())
    print(" - Is Locked  :", sap.GetModelIsLocked())
    print(" - Units Code :", sap.GetPresentUnits())
    
    # Check Stories
    try:
        ret = sap.Story.GetNameList()
        print(" - Stories    :", ret)
    except Exception as e:
        print(" - Story error:", e)

    # Check Material count
    try:
        ret = sap.PropMaterial.GetNameList()
        print(" - Materials  :", ret)
    except Exception as e:
        print(" - Mat error  :", e)

    # Check Frames count
    try:
        ret = sap.FrameObj.Count()
        print(" - Total Frames (Columns/Beams):", ret)
    except Exception as e:
        print(" - Frame error:", e)

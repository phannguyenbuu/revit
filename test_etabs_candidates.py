import comtypes.client
from comtypes.gen import ETABSv1

helper = comtypes.client.CreateObject('ETABSv1.Helper')
helper = helper.QueryInterface(ETABSv1.cHelper)

candidates = [
    "CSI.ETABS.API.ETABSObject",
    "",
    "ETABS",
    "ETABSv1",
    "ETABSv1.cOAPI",
    "ETABSv1.ETABSObject",
    "CSiAPIv1",
    "CSiAPIv1.cOAPI",
    "CSI.ETABS.API",
    "CSI.ETABS.API.ETABSObject.22",
    "ETABS 22",
    "ETABS22"
]

pid = 44100
for name in candidates:
    try:
        obj = helper.GetObjectProcess(name, pid)
        print(f"typeName='{name}' -> {obj}")
        if obj:
            print("FOUND! SapModel:", obj.SapModel)
            break
    except Exception as e:
        print(f"typeName='{name}' -> Error: {e}")

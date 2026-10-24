import comtypes.client
from comtypes.gen import ETABSv1

print("Initializing ETABS OAPI...")
helper = comtypes.client.CreateObject('ETABSv1.Helper')
helper = helper.QueryInterface(ETABSv1.cHelper)

etabs_app = helper.CreateObjectProgId('CSI.ETABS.API.ETABSObject')
sap = etabs_app.SapModel

print("1. Start ETABS Application GUI...")
# In CSI OAPI: ApplicationStart(Units, Visible, FileName)
# eUnits: 6 = kN_m_C, 10 = N_mm_C, 8 = Ton_m_C
ret = sap.InitializeNewModel(6) # kN_m_C
print(" - InitializeNewModel:", ret)

ret2 = sap.File.NewBlank()
print(" - File.NewBlank:", ret2)

# Create a material
ret3 = sap.PropMaterial.SetMaterial("B30", 2) # 2 = Concrete
print(" - SetMaterial B30:", ret3)

# Add a Story
ret4 = sap.Story.SetStories_2(["Base", "Story1", "Story2"], [0.0, 3.6, 7.2], [3.6, 3.6, 3.6], [False, False, False], [None, None, None], [False, False, False], [None, None, None])
print(" - SetStories:", ret4)

# Create a column/frame
# FrameObj.AddByCoord(xi, yi, zi, xj, yj, zj, propName, userName)
ret5 = sap.FrameObj.AddByCoord(0, 0, 0, 0, 0, 3.6, "Default", "Col1")
print(" - Add Column Col1:", ret5)

# Check total frames
count = sap.FrameObj.Count()
print(" - Total frames in model:", count)

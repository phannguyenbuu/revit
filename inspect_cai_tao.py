import sys
import comtypes.client
from comtypes.gen import ETABSv1

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def inspect_model_dimensions():
    edb_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\CAI TAO .EDB"
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    sap = app.SapModel
    sap.File.OpenFile(edb_path)
    
    print("=== THÔNG TIN MÔ HÌNH ETABS: CAI TAO ===")
    units = sap.GetPresentUnits()
    print(f"Hệ đơn vị hiện tại (Units code): {units}") # 6 = kN_m_C
    
    # 1. Tầng (Stories)
    story_names = sap.Story.GetNameList()[1]
    print(f"\n1. CÁC TẦNG ({len(story_names)} tầng):")
    for s in story_names:
        elev = sap.Story.GetElevation(s)[0]
        height = sap.Story.GetHeight(s)[0]
        print(f" - Tầng {s:6s}: Cao độ = {elev:6.2f} m | Chiều cao tầng = {height:5.2f} m")

    # 2. Tiết diện thanh (Frame Sections: Cột & Dầm)
    sec_names = sap.PropFrame.GetNameList()[1]
    print(f"\n2. DANH SÁCH TIẾT DIỆN KHUNG ({len(sec_names)} tiết diện):")
    for name in sec_names:
        # Check type
        prop_info = sap.PropFrame.GetRectangle(name)
        # prop_info returns: [FileName, MatProp, t3 (Depth), t2 (Width), Color, Notes, GUID, ret]
        if prop_info[-1] == 0:
            mat = prop_info[1]
            h = prop_info[2] # Depth (m)
            b = prop_info[3] # Width (m)
            print(f" - Tiết diện [Hộp chữ nhật] '{name:15s}': b = {b*1000:5.0f} mm x h = {h*1000:5.0f} mm (Bê tông: {mat})")
        else:
            # Check other shapes (circle, etc.)
            circle_info = sap.PropFrame.GetCircle(name)
            if circle_info[-1] == 0:
                print(f" - Tiết diện [Tròn] '{name:15s}': D = {circle_info[2]*1000:5.0f} mm")
            else:
                print(f" - Tiết diện khác: '{name}'")

    # 3. Tiết diện sàn (Area Props / Slabs)
    area_props = sap.PropArea.GetNameList()[1]
    print(f"\n3. DANH SÁCH BẢN SÀN & VÁCH ({len(area_props)} tiết diện):")
    for name in area_props:
        slab_info = sap.PropArea.GetSlab(name)
        # slab_info: [SlabType, ShellType, MatProp, Thickness, Color, Notes, GUID, ret]
        if slab_info[-1] == 0:
            thickness = slab_info[3] # Thickness (m)
            mat = slab_info[2]
            print(f" - Sàn/Vách '{name:15s}': Chiều dày t = {thickness*1000:5.0f} mm (Vật liệu: {mat})")
        else:
            print(f" - Bản sàn: '{name}'")

    # 4. Thống kê cột và dầm trong mô hình
    total_frames = sap.FrameObj.Count()
    print(f"\n4. PHÂN LOẠI 161 PHẦN TỬ THANH (DẦM & CỘT):")
    all_frames = sap.FrameObj.GetNameList()[1]
    
    columns = []
    beams = []
    braces = []
    
    for f in all_frames:
        # Get coordinates
        p1, p2, ret = sap.FrameObj.GetPoints(f)
        x1, y1, z1, _ = sap.PointObj.GetCoordCartesian(p1)
        x2, y2, z2, _ = sap.PointObj.GetCoordCartesian(p2)
        sec = sap.FrameObj.GetSection(f)[0]
        
        # If delta Z > delta XY -> Column
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        dz = abs(z2 - z1)
        
        if dz > 0.1 and dx < 0.05 and dy < 0.05:
            columns.append((f, sec, (x1, y1, z1), (x2, y2, z2)))
        elif dz < 0.05:
            beams.append((f, sec, (x1, y1, z1), (x2, y2, z2)))
        else:
            braces.append((f, sec, (x1, y1, z1), (x2, y2, z2)))
            
    print(f" - Tổng số Cột (Columns): {len(columns)}")
    print(f" - Tổng số Dầm (Beams)  : {len(beams)}")
    print(f" - Giằng/Khác (Braces)  : {len(braces)}")
    
    print("\nMột số cột tiêu biểu:")
    for c in columns[:6]:
        print(f"   * Cột ID {c[0]:>3s}: Tiết diện {c[1]:12s} tại (X={c[2][0]:.2f}, Y={c[2][1]:.2f}) từ Z={c[2][2]:.2f}m đến Z={c[3][2]:.2f}m")
        
    print("\nMột số dầm tiêu biểu:")
    for b in beams[:6]:
        L = ((b[3][0]-b[2][0])**2 + (b[3][1]-b[2][1])**2)**0.5
        print(f"   * Dầm ID {b[0]:>3s}: Tiết diện {b[1]:12s} dài L={L:.2f}m tại cao độ Z={b[2][2]:.2f}m")

    # 5. Tổ hợp tải trọng (Load Combinations)
    combos = sap.RespCombo.GetNameList()[1]
    print(f"\n5. CÁC TỔ HỢP TẢI TRỌNG ({len(combos)} tổ hợp):")
    print("   " + ", ".join(combos[:15]))
    
    app.ApplicationExit(False)

if __name__ == "__main__":
    inspect_model_dimensions()

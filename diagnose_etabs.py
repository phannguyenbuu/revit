import sys
import comtypes.client
from comtypes.gen import ETABSv1

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def diagnose_etabs_errors():
    edb_path = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\CAI TAO .EDB"
    helper = comtypes.client.CreateObject('ETABSv1.Helper').QueryInterface(ETABSv1.cHelper)
    app = helper.CreateObjectProgId("CSI.ETABS.API.ETABSObject")
    app.ApplicationStart()
    sap = app.SapModel
    sap.File.OpenFile(edb_path)
    
    print("==================================================")
    print("1. CHẨN ĐOÁN LỖI DIAPHRAGM (CƠ THỂ CỨNG KHÁC CAO ĐỘ):")
    print("==================================================")
    # Get all Diaphragms
    diaph_names = sap.Diaphragm.GetNameList()[1]
    print("Danh sách Diaphragm đã định nghĩa:", diaph_names)
    
    # Check all points and their assigned diaphragm and Z coord
    pt_names = sap.PointObj.GetNameList()[1]
    diaph_points = {} # diaph_name -> list of (pt, x, y, z)
    
    for p in pt_names:
        # Get diaphragm assigned to point
        res = sap.PointObj.GetDiaphragm(p)
        # res: [DiaphragmOption, DiaphragmName, ret]
        if len(res) >= 2 and res[-1] == 0:
            d_name = res[1] if isinstance(res[1], str) else res[0]
            if d_name and str(d_name).strip():
                x, y, z, _ = sap.PointObj.GetCoordCartesian(p)
                if d_name not in diaph_points:
                    diaph_points[d_name] = []
                diaph_points[d_name].append((p, x, y, z))
            
    # Check areas (slabs) assigned diaphragm
    area_names = sap.AreaObj.GetNameList()[1]
    area_diaphs = {}
    for a in area_names:
        res = sap.AreaObj.GetDiaphragm(a)
        if len(res) >= 2 and res[-1] == 0:
            d_name = res[0] if isinstance(res[0], str) else res[1]
            if d_name and str(d_name).strip():
                # get points of area
                pts = sap.AreaObj.GetPoints(a)[1]
                z_list = []
                for p in pts:
                    x, y, z, _ = sap.PointObj.GetCoordCartesian(p)
                    z_list.append(z)
                avg_z = sum(z_list) / len(z_list) if z_list else 0
                area_diaphs[a] = (d_name, avg_z)
                if d_name not in diaph_points:
                    diaph_points[d_name] = []
                for p in pts:
                    x, y, z, _ = sap.PointObj.GetCoordCartesian(p)
                    diaph_points[d_name].append((p, x, y, z))
                
    for d_name, pts in diaph_points.items():
        z_vals = set(round(pt[3], 2) for pt in pts)
        is_semi, ret = sap.Diaphragm.GetDiaphragm(d_name)
        type_str = "Semi-Rigid" if is_semi else "Rigid"
        print(f"\nDiaphragm '{d_name}' (Loại: {type_str}):")
        print(f" - Số điểm gán: {len(pts)}")
        print(f" - Các cao độ Z khác nhau: {sorted(list(z_vals))} mm")
        if len(z_vals) > 1 and not is_semi:
            print(f"  >>> PHÁT HIỆN NGUYÊN NHÂN CẢNH BÁO DIAPHRAGM!")
            print(f"  >>> Diaphragm '{d_name}' là Rigid nhưng chứa các điểm ở {len(z_vals)} cao độ khác nhau:")
            for z in sorted(list(z_vals)):
                sample_pts = [p[0] for p in pts if round(p[3], 2) == z][:5]
                print(f"       * Z = {z:8.1f} mm: các điểm mẫu {sample_pts}")

    print("\n==================================================")
    print("2. CHẨN ĐOÁN CÁC CẢNH BÁO 'TOO CLOSE' (QUÁ GẦN NHAU):")
    print("==================================================")
    # Check sample pairs from CAI TAO .WRN
    # Example: T4F10 & F14 at (18250, 5970, 15600)
    # Note: In ETABS, T4F10 means Frame 10 on Story T4 or Frame with label 10
    # Let's inspect frames around (18250, 5970, 15600)
    target_x, target_y, target_z = 18250.0, 5970.0, 15600.0
    print(f"\nKiểm tra vùng tọa độ (X={target_x}, Y={target_y}, Z={target_z}):")
    
    all_frames = sap.FrameObj.GetNameList()[1]
    nearby_frames = []
    for f in all_frames:
        p1, p2, _ = sap.FrameObj.GetPoints(f)
        x1, y1, z1, _ = sap.PointObj.GetCoordCartesian(p1)
        x2, y2, z2, _ = sap.PointObj.GetCoordCartesian(p2)
        
        # Check distance from p1 or p2 to target
        d1 = ((x1-target_x)**2 + (y1-target_y)**2 + (z1-target_z)**2)**0.5
        d2 = ((x2-target_x)**2 + (y2-target_y)**2 + (z2-target_z)**2)**0.5
        if d1 < 50.0 or d2 < 50.0:
            nearby_frames.append((f, (x1, y1, z1), (x2, y2, z2), min(d1, d2)))
            
    print(f"Tìm thấy {len(nearby_frames)} dầm/cột kết nối tại nút này:")
    for nf in nearby_frames:
        print(f" - Frame '{nf[0]}': P1={nf[1]} -> P2={nf[2]} (Khoảng cách tới nút: {nf[3]:.2f} mm)")

    # Also check tolerance of CheckModel
    print("\nThông số kiểm tra Check Model:")
    # In CSI OAPI: CheckModel or tolerance
    app.ApplicationExit(False)

if __name__ == "__main__":
    diagnose_etabs_errors()

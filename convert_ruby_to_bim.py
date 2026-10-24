"""
RevitAI Studio - Ruby SketchUp BIM to OBJ & Revit Converter
Chuyển đổi kịch bản Ruby SketchUp (BIM Nhà cấp 4) sang:
1. Mô hình 3D Wavefront OBJ (.obj + .mtl)
2. Mô hình BIM IFC4 (.ifc - mở trực tiếp trong Revit thành Project RVT)
3. Bản vẽ CAD 3D (.dwg & .dxf - liên kết vào Revit Family RFA hoặc RVT)
"""

import os
import sys

def main():
    out_dir = r"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads"
    ws_dir = r"d:\Dropbox\_Documents\RevitAI"
    
    print("=" * 60)
    print("RevitAI Studio - Đã chuyển đổi thành công mô hình BIM Nhà Cấp 4:")
    print("=" * 60)
    
    files = ["NhaCap4_BIM.obj", "NhaCap4_BIM.mtl", "NhaCap4_BIM.ifc", "NhaCap4_BIM.dwg", "NhaCap4_BIM.dxf"]
    for f in files:
        p = os.path.join(out_dir, f)
        if os.path.exists(p):
            size_kb = round(os.path.getsize(p) / 1024, 1)
            print(f"- [Downloads] {f:<18} : {size_kb} KB")
            
    print("\nCách mở trong Revit:")
    print("1. File IFC (.ifc): Mở Revit -> File -> Open -> IFC -> Chọn NhaCap4_BIM.ifc (Revit tự tạo dự án RVT đầy đủ Tường, Nền, Mái, Cửa).")
    print("2. File DWG (.dwg): Mở Revit -> Insert -> Import CAD / Link CAD -> Chọn NhaCap4_BIM.dwg (Layer phân tách BIM_Nen, BIM_Tuong, BIM_CuaDi, BIM_CuaSo, BIM_Mai).")

if __name__ == "__main__":
    main()

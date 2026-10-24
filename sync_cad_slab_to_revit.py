import sys
import os
import json
import math
import argparse
import ctypes
import urllib.request

try:
    if sys.stdout:
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def get_cad_polyline_loops():
    """Trích xuất danh sách các vòng polyline khép kín đang chọn trong AutoCAD và chuyển sang tọa độ Revit (mm)."""
    try:
        u32 = ctypes.windll.user32
        try:
            hWinsta = u32.OpenWindowStationW('WinSta0', False, 0x037F)
            if hWinsta:
                u32.SetProcessWindowStation(hWinsta)
            hDesk = u32.OpenDesktopW('Default', 0, False, 0x01FF)
            if hDesk:
                u32.SetThreadDesktop(hDesk)
        except:
            pass

        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()

        acad = None
        for progid in ['AutoCAD.Application', 'AutoCAD.Application.24', 'AutoCAD.Application.24.1']:
            try:
                acad = win32com.client.GetActiveObject(progid)
                if acad:
                    break
            except:
                continue

        if not acad:
            return None, "Không thể kết nối với AutoCAD qua COM. Vui lòng đảm bảo AutoCAD đang mở."

        # Tìm Document có đối tượng đang chọn
        doc = None
        ss = None
        try:
            doc = acad.ActiveDocument
            if doc:
                pf = doc.PickfirstSelectionSet
                act = doc.ActiveSelectionSet
                if pf and pf.Count > 0:
                    ss = pf
                elif act and act.Count > 0:
                    ss = act
        except:
            pass

        # Nếu ActiveDocument chưa có đối tượng chọn, quét qua các tài liệu đang mở
        if (not ss or ss.Count == 0) and hasattr(acad, "Documents"):
            try:
                for d in acad.Documents:
                    try:
                        dpf = d.PickfirstSelectionSet
                        dact = d.ActiveSelectionSet
                        if dpf and dpf.Count > 0:
                            doc = d
                            ss = dpf
                            break
                        elif dact and dact.Count > 0:
                            doc = d
                            ss = dact
                            break
                    except:
                        continue
            except:
                pass

        if not doc:
            return None, "AutoCAD không có bản vẽ nào đang mở!"

        if not ss or ss.Count == 0:
            return None, f"Chưa chọn đối tượng nào trong AutoCAD (File: {doc.Name})! Vui lòng click chọn 1 đường Polyline khép kín của sàn."

        # Lọc các polyline
        polylines = []
        for i in range(ss.Count):
            try:
                ent = ss.Item(i)
                name = ent.ObjectName
                if name in ['AcDbPolyline', 'AcDb2dPolyline']:
                    polylines.append(ent)
            except:
                pass

        if not polylines:
            return None, f"Trong {ss.Count} đối tượng đang chọn ở AutoCAD không có đường Polyline nào! Vui lòng chọn đường bao Polyline."

        DY = 1400405.9
        loops = []
        cad_layers = set()
        detected_plans = set()

        for ent in polylines:
            coords = list(ent.Coordinates)
            is_3d = (ent.ObjectName == 'AcDb2dPolyline')
            step = 3 if is_3d else 2

            raw_pts = []
            for j in range(0, len(coords), step):
                raw_pts.append((coords[j], coords[j+1]))

            if len(raw_pts) < 3:
                continue

            cad_layers.add(ent.Layer)

            # Tính Bounding Box trong CAD
            xs = [p[0] for p in raw_pts]
            ys = [p[1] for p in raw_pts]
            mid_x = (min(xs) + max(xs)) / 2.0

            # Xác định DX tự động theo tọa độ X trong AutoCAD
            if mid_x < -85000:
                DX = 132847.0
                detected_plans.add("Chi tiết phóng to")
            elif -85000 <= mid_x < -20000:
                DX = 70953.54
                detected_plans.add("Mặt bằng Tầng 2")
            elif -20000 <= mid_x < 35000:
                DX = 10587.53
                detected_plans.add("Mặt bằng Tầng 3")
            elif 35000 <= mid_x < 100000:
                DX = -53510.5
                detected_plans.add("Mặt bằng Tầng 1 / Tầng 4 / Áp Mái")
            else:
                DX = -113999.1
                detected_plans.add("Mặt bằng Tầng Tum / Mái")

            # Chuyển đổi sang tọa độ Revit (mm)
            loop_pts = []
            for cx, cy in raw_pts:
                rx = round(cx + DX, 1)
                ry = round(cy + DY, 1)
                loop_pts.append({"x": rx, "y": ry})

            # Đảm bảo khép kín
            p0 = loop_pts[0]
            pEnd = loop_pts[-1]
            dist_sq = (p0["x"] - pEnd["x"])**2 + (p0["y"] - pEnd["y"])**2
            if dist_sq > 1.0:
                loop_pts.append({"x": p0["x"], "y": p0["y"]})

            loops.append(loop_pts)

        if not loops:
            return None, "Không tìm thấy đường bao Polyline hợp lệ (>= 3 đỉnh) trong vùng chọn AutoCAD."

        summary = {
            "polylineCount": len(loops),
            "layers": list(cad_layers),
            "detectedPlan": ", ".join(detected_plans) if detected_plans else "Tự động tính tọa độ"
        }
        return loops, summary

    except Exception as e:
        return None, f"Lỗi khi kết nối AutoCAD: {e}"

def main():
    parser = argparse.ArgumentParser(description="Chuyển Polyline AutoCAD sang Slab Revit")
    parser.add_argument("--category", choices=["standard", "toilet"], default="standard", help="Loại sàn: standard hoặc toilet")
    parser.add_argument("--thickness", type=float, default=100.0, help="Độ dày sàn (mm)")
    parser.add_argument("--offset", type=float, default=0.0, help="Cao độ chênh so với tầng (mm)")
    parser.add_argument("--level-id", type=int, default=-1, help="ID tầng chỉ định (-1: tự động)")
    parser.add_argument("--check-only", action="store_true", help="Chỉ kiểm tra trạng thái Revit")
    args = parser.parse_args()

    revit_url = "http://127.0.0.1:8090/api/execute"
    dll_path = r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll"

    if args.check_only:
        payload = {
            "action": "execute_dynamic",
            "dllPath": dll_path,
            "typeName": "RevitScript.CreateOrReplaceSlabFromCad",
            "methodName": "Run",
            "args": {
                "checkRevitOnly": True
            }
        }
        try:
            req = urllib.request.Request(
                revit_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                print(res.read().decode("utf-8"))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}))
        return

    # 1. Trích xuất đường bao từ AutoCAD
    loops, summary_or_err = get_cad_polyline_loops()
    if not loops:
        print(json.dumps({"success": False, "error": summary_or_err}, ensure_ascii=False))
        return

    # 2. Gọi Revit Bridge để tạo hoặc thay thế sàn
    payload = {
        "action": "execute_dynamic",
        "dllPath": dll_path,
        "typeName": "RevitScript.CreateOrReplaceSlabFromCad",
        "methodName": "Run",
        "args": {
            "loops": loops,
            "floorCategory": args.category,
            "thicknessMm": args.thickness,
            "offsetMm": args.offset,
            "levelId": args.level_id
        }
    }

    try:
        req = urllib.request.Request(
            revit_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        with urllib.request.urlopen(req, timeout=30) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            res_data["cadSummary"] = summary_or_err
            print(json.dumps(res_data, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "error": f"Lỗi Revit Bridge: {e}"}, ensure_ascii=False))

if __name__ == "__main__":
    main()

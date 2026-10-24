import sys
import os
import time
import json
import urllib.request
import ctypes
import winsound

try:
    if sys.stdout:
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def show_alert(message, title="Dong Bo 3ds Max <-> Revit", icon_type=0x40):
    if "--no-gui" in sys.argv:
        try:
            print(f"[{title}] {message}")
        except:
            print(f"Success: {title}")
        return
    ctypes.windll.user32.MessageBoxW(0, message, title, icon_type | 0x0)

def main():
    t_start = time.time()
    max_url = "http://127.0.0.1:8096/api/execute"
    revit_url = "http://127.0.0.1:8090/api/execute"

    # 1. Export selected objects from 3ds Max via ACIS SAT (Solid B-Rep), fallback to DWG
    max_code = """
(
    local selObjs = for o in selection collect o
    if selObjs.count == 0 then (
        "ERROR|Vui lòng chọn ít nhất 1 vật thể trong 3ds Max trước khi bấm đồng bộ!"
    ) else (
        local shiftVec = [19973.3, 0.0, 0.0]
        
        -- Check if all objects are modeled near origin vs building coordinates
        local minX = 1e9
        for o in selObjs do minX = amin minX o.min.x
        if minX > -5000.0 then (
            shiftVec = [0, 0, 0]
        )
        
        local tempDir = getDir #temp
        local satPath = tempDir + "\\\\Sync_3dsMax_To_Revit.sat"
        local dwgPath = tempDir + "\\\\Sync_3dsMax_To_Revit.dwg"
        if doesFileExist satPath do deleteFile satPath
        if doesFileExist dwgPath do deleteFile dwgPath
        
        -- Tạo bản sao tạm để chuyển đổi sang Body Object / ACIS Solid
        local exportObjs = #()
        for o in selObjs do (
            local cObj = copy o
            move cObj shiftVec
            if classOf cObj != Body_Object do (
                try (
                    convertToPoly cObj
                    ConvertToBody cObj
                ) catch ()
            )
            append exportObjs cObj
        )
        
        select exportObjs
        local satSuccess = false
        try (
            satSuccess = exportFile satPath #noPrompt selectedOnly:true using:ACIS_SAT
        ) catch (
            satSuccess = false
        )
        
        local exportFormat = "SAT"
        local finalPath = satPath
        
        -- Nếu xuất SAT không thành công hoặc file rỗng, tự động fallback sang DWG
        if not satSuccess or not (doesFileExist satPath) or (getFileSize satPath <= 0) then (
            exportFormat = "DWG"
            finalPath = dwgPath
            for cObj in exportObjs do (
                try (
                    convertToMesh cObj
                    autoEdge cObj 25.0 true
                ) catch ()
            )
            select exportObjs
            exportFile dwgPath #noPrompt selectedOnly:true
        )
        
        -- Xóa bản sao tạm, khôi phục vùng chọn gốc
        delete exportObjs
        select selObjs
        
        if doesFileExist finalPath then (
            local desc = if selObjs.count == 1 then selObjs[1].name else ((selObjs.count as string) + " vật thể (" + selObjs[1].name + "...)")
            "SUCCESS|" + desc + "|" + finalPath + "|" + exportFormat
        ) else (
            "ERROR|Xuất file từ 3ds Max thất bại!"
        )
    )
)
"""
    try:
        req = urllib.request.Request(
            max_url,
            data=json.dumps({"code": max_code}).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read().decode("utf-8"))
            max_result_str = data.get("result", "")
    except Exception as e:
        show_alert(f"Không thể kết nối tới 3ds Max Bridge (Port 8096)!\nLỗi: {e}\n\nHãy đảm bảo 3ds Max đang mở.", "Lỗi 3ds Max", 0x10)
        return

    if not max_result_str or max_result_str.startswith("ERROR|"):
        err = max_result_str[6:] if max_result_str.startswith("ERROR|") else "3ds Max không trả về kết quả hợp lệ."
        show_alert(err, "Thông báo 3ds Max", 0x30)
        return

    parts = max_result_str.split("|")
    max_obj_name = parts[1]
    file_path = parts[2]
    export_format = parts[3] if len(parts) > 3 else ("SAT" if file_path.endswith(".sat") else "DWG")

    if not os.path.exists(file_path):
        show_alert(f"File xuất ra không tồn tại:\n{file_path}", "Lỗi file hình học", 0x10)
        return

    # 2. Send reload command to Revit
    dll_path = r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll"
    if not os.path.exists(dll_path):
        dll_path = r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_Sync.dll"

    create_new = "--create-new" in sys.argv
    new_fam_name = ""
    if "--family-name" in sys.argv:
        try:
            new_fam_name = sys.argv[sys.argv.index("--family-name") + 1]
        except:
            pass

    revit_payload = {
        "action": "execute_dynamic",
        "dllPath": dll_path,
        "typeName": "RevitScript.Sync3dsMaxToRevitFamily",
        "methodName": "Run",
        "args": {
            "filePath": file_path,
            "dwgPath": file_path,
            "satPath": file_path if file_path.endswith(".sat") else "",
            "exportFormat": export_format,
            "maxObjectName": max_obj_name,
            "createNewFamily": create_new,
            "newFamilyName": new_fam_name
        }
    }

    def call_revit_sync(payload):
        req = urllib.request.Request(
            revit_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        with urllib.request.urlopen(req, timeout=40) as res:
            return json.loads(res.read().decode("utf-8"))

    try:
        revit_res = call_revit_sync(revit_payload)
    except Exception as e:
        detail = ""
        if hasattr(e, "read"):
            try:
                detail = "\nChi tiết: " + e.read().decode("utf-8", errors="ignore")
            except:
                pass
        show_alert(f"Không thể kết nối tới Revit Bridge (Port 8090)!\nLỗi: {e}{detail}\n\nHãy đảm bảo Revit đang mở và không kẹt lệnh.", "Lỗi Revit", 0x10)
        return

    # Nếu không chọn Family nhưng đang chạy Desktop GUI: hỏi người dùng có muốn tạo Family mới không
    if not revit_res.get("success") and revit_res.get("needCreateNew") and "--no-gui" not in sys.argv:
        confirm = ctypes.windll.user32.MessageBoxW(
            0,
            f"Chưa có Family nào được chọn trong Revit (hoặc đối tượng đang chọn không phải là Family).\n\nBạn có muốn TẠO MỚI Family '{max_obj_name}' trong Revit từ các vật thể 3ds Max này không?",
            "Tạo Family Mới trong Revit?",
            0x24 # MB_YESNO | MB_ICONQUESTION
        )
        if confirm == 6: # IDYES
            revit_payload["args"]["createNewFamily"] = True
            revit_payload["args"]["newFamilyName"] = max_obj_name
            try:
                revit_res = call_revit_sync(revit_payload)
            except Exception as e:
                show_alert(f"Lỗi khi gửi lệnh tạo Family mới tới Revit: {e}", "Lỗi Revit", 0x10)
                return

    elapsed = round(time.time() - t_start, 1)

    if revit_res.get("success") == True:
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except:
            pass
        fam_name = revit_res.get("revitFamilyName", "N/A")
        inst_id = revit_res.get("instanceId", "N/A")
        is_new = revit_res.get("isNewFamily", False)
        title_tag = "TẠO MỚI FAMILY THÀNH CÔNG" if is_new else "ĐỒNG BỘ THÀNH CÔNG"
        is_sat = (export_format == "SAT") or (revit_res.get("freeFormCount", 0) > 0)
        geom_type = "Khối Solid B-Rep (FreeFormElement - Cắt lát 2D & Mặt cắt chuẩn BIM)" if is_sat else "Mesh DWG (Đã ẩn nét tam giác)"
        msg = f"{title_tag} trong {elapsed}s!\n\n• 3ds Max: {max_obj_name}\n• Định dạng: {export_format} ({geom_type})\n• Revit Family: {fam_name} (ID {inst_id})\n• Vật liệu: Mặt phẳng trắng, nét viền đen sắc nét."
        show_alert(msg, "Đồng Bộ 3ds Max ↔ Revit", 0x40)
    else:
        err = revit_res.get("error", "Đồng bộ thất bại không rõ nguyên nhân.")
        if revit_res.get("needCreateNew"):
            err += " (needCreateNew)"
        show_alert(err, "Lỗi Đồng Bộ Revit", 0x30)

if __name__ == "__main__":
    main()

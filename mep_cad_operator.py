import os
import sys
import subprocess
import time

try:
    if sys.stdout:
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LSP_PATH = os.path.join(CURRENT_DIR, "mep_cleaner_and_leader.lsp").replace("\\", "/")
ACCORE_EXE = r"C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe"

def run_on_active_autocad(action="full", layer="P-PIPE", search_char="+", max_dist=5000.0, offset_y=250.0):
    """Gửi lệnh AutoLISP trực tiếp vào cửa sổ AutoCAD đang mở qua Windows WM_COPYDATA."""
    import send_to_acad
    
    hwnd, title = send_to_acad.get_acad_hwnd()
    if not hwnd:
        return "ERROR: Không tìm thấy cửa sổ AutoCAD đang mở trên màn hình."
        
    doc_name = title.split("[")[-1].replace("]", "") if "[" in title else title
    lsp_forward = LSP_PATH.replace("\\", "/")
    
    run_id = int(time.time() * 1000)
    res_file = os.path.join(CURRENT_DIR, f"_acad_act_{run_id}.txt").replace("\\", "/")
    run_file = os.path.join(CURRENT_DIR, f"_acad_run_{run_id}.lsp").replace("\\", "/")
    
    if action == "delete_solids":
        inner_cmd = "(setq cnt (RunDeleteSolids))"
        succ_desc = "Xóa Hatch Solid/Solid"
    elif action == "add_leaders":
        inner_cmd = f'(setq cnt (RunMepLeaderEx "{layer}" "{search_char}" {max_dist} {offset_y}))'
        succ_desc = "Tạo Leader cao độ"
    else:
        inner_cmd = f'(setq cnt (RunFullMepPolishEx "{layer}" "{search_char}" {max_dist} {offset_y}))'
        succ_desc = "Tối ưu bản vẽ MEP toàn diện"

    lsp_content = f"""(vl-load-com)
(defun *error* (msg)
  (setq _f (open "{res_file}" "w"))
  (write-line (strcat "ERROR: " msg) _f)
  (close _f)
  (princ)
)
(load "{lsp_forward}")
{inner_cmd}
(command "_.REGEN")
(setq _f (open "{res_file}" "w"))
(write-line (strcat "SUCCESS: " (vl-prin1-to-string cnt)) _f)
(close _f)
(princ)
"""
    try:
        with open(run_file, "w", encoding="utf-8") as f:
            f.write(lsp_content)
            
        send_to_acad.send_acad_command('")" ) ) ) ) (princ)\n', skip_esc=False)
        time.sleep(0.2)
        
        ok, msg = send_to_acad.send_acad_command(f'(load "{run_file}")\n', timeout_ms=45000, skip_esc=True)
        if not ok:
            return f"ERROR: Không thể gửi lệnh vào AutoCAD: {msg}"
            
        for _ in range(45):
            time.sleep(1.0)
            if os.path.exists(res_file):
                with open(res_file, "r", encoding="utf-8") as f:
                    out = f.read().strip()
                if out.startswith("SUCCESS:"):
                    cnt_str = out.replace("SUCCESS:", "").strip()
                    return f"SUCCESS: {succ_desc} hoàn tất trên [{doc_name}]. Kết quả: {cnt_str}"
                elif out.startswith("ERROR:"):
                    return f"ERROR: AutoCAD báo lỗi: {out}"
        return f"SUCCESS: Đã gửi lệnh vào AutoCAD [{doc_name}]. Đang xử lý ngầm trong AutoCAD."
    finally:
        for f_temp in [run_file, res_file]:
            try:
                if os.path.exists(f_temp):
                    os.remove(f_temp)
            except:
                pass


def run_on_dwg_file(dwg_path, action="full", layer="P-PIPE-CNTR", search_char="+", max_dist=5000.0, offset_y=250.0):
    """Chạy không cần mở AutoCAD UI (Headless qua accoreconsole.exe) trên 1 file DWG."""
    if not os.path.exists(dwg_path):
        return False, f"File không tồn tại: {dwg_path}"
    
    scr_content = f"""(load "{LSP_PATH}")
"""
    if action == "delete_solids":
        scr_content += "(RunDeleteSolids)\n"
    elif action == "add_leaders":
        scr_content += f'(RunMepLeaderEx "{layer}" "{search_char}" {max_dist} {offset_y})\n'
    else:
        scr_content += f'(RunFullMepPolishEx "{layer}" "{search_char}" {max_dist} {offset_y})\n'
    
    scr_content += "QSAVE\nQUIT\n"
    
    # Tạo tên file script duy nhất để tránh xung đột
    scr_file = os.path.join(CURRENT_DIR, f"_temp_mep_{int(time.time()*1000)}.scr")
    with open(scr_file, "w", encoding="utf-8") as f:
        f.write(scr_content)
        
    cmd = [ACCORE_EXE, "/i", dwg_path, "/s", scr_file]
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180
        )
        elapsed = round(time.time() - t0, 1)
        out = proc.stdout if proc.stdout else ""
        if "\x00" in out:
            out = out.replace("\x00", "")
        success = proc.returncode == 0
        return success, f"Đã xử lý trong {elapsed}s. {out[-200:].strip() if out else 'OK'}"
    except Exception as e:
        return False, f"Lỗi accoreconsole: {e}"
    finally:
        try:
            if os.path.exists(scr_file):
                os.remove(scr_file)
        except:
            pass

def run_batch_dwg(folder_path, action="full", layer="P-PIPE-CNTR", search_char="+", max_dist=5000.0, offset_y=250.0):
    """Xử lý hàng loạt tất cả file DWG trong thư mục qua accoreconsole."""
    if not os.path.exists(folder_path):
        return {"success": False, "message": f"Thư mục không tồn tại: {folder_path}"}
        
    dwg_files = []
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            if f.lower().endswith(".dwg") and not f.startswith("~"):
                dwg_files.append(os.path.join(root, f))
                
    if not dwg_files:
        return {"success": False, "message": f"Không tìm thấy file DWG nào trong: {folder_path}"}
        
    total = len(dwg_files)
    results = []
    success_count = 0
    
    for i, dwg in enumerate(dwg_files, 1):
        rel_name = os.path.relpath(dwg, folder_path)
        ok, msg = run_on_dwg_file(dwg, action=action, layer=layer, search_char=search_char, max_dist=max_dist, offset_y=offset_y)
        if ok:
            success_count += 1
        results.append({
            "index": i,
            "file": rel_name,
            "success": ok,
            "message": msg
        })
        
    return {
        "success": True,
        "total": total,
        "processed": success_count,
        "failed": total - success_count,
        "results": results
    }


if __name__ == "__main__":
    print("Test run on active AutoCAD:")
    print(run_on_active_autocad(action="full"))


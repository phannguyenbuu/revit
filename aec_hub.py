#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
aec_hub.py - AEC Automation Hub Manager & Status Inspector
Quản lý trạng thái đa phần mềm: AutoCAD, 3ds Max, Revit và Web Dashboard.
Hoạt động độc lập và không phụ thuộc vào việc phần mềm nào phải bật trước.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

try:
    import psutil
except ImportError:
    psutil = None

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_all_aec_processes():
    """Quét 1 lần duy nhất toàn bộ tiến trình để phát hiện AutoCAD, 3ds Max, Revit."""
    procs = {'acad': None, '3dsmax': None, 'revit': None}
    if not psutil:
        return procs
    for p in psutil.process_iter(['pid', 'name']):
        try:
            name = (p.info.get('name') or '').lower()
            if 'acad' in name and not procs['acad']:
                procs['acad'] = p
            elif '3dsmax' in name and not procs['3dsmax']:
                procs['3dsmax'] = p
            elif 'revit' in name and not procs['revit']:
                procs['revit'] = p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return procs


def get_open_files_with_ext(proc, ext):
    """Lấy danh sách các file đang mở của tiến trình có đuôi chỉ định."""
    files = []
    if not proc or not psutil:
        return files
    try:
        for f in proc.open_files():
            path = f.path
            if path.lower().endswith(ext.lower()):
                base = os.path.basename(path)
                if not base.startswith(('~', '$', '.')):
                    files.append(path)
    except Exception:
        pass
    return list(dict.fromkeys(files))


def probe_http_json(url, timeout=0.3):
    """Gửi yêu cầu HTTP GET nhẹ nhàng để kiểm tra endpoint."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AECHub/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.status == 200:
                data = res.read().decode('utf-8', errors='ignore')
                return json.loads(data)
    except Exception:
        pass
    return None


def get_autocad_status(proc=None):
    """Kiểm tra trạng thái AutoCAD."""
    if proc is None and psutil:
        proc = get_all_aec_processes().get('acad')
    if not proc:
        return {
            "name": "AutoCAD",
            "running": False,
            "status": "offline",
            "message": "Chưa mở (Tùy chọn - không bắt buộc)",
            "pid": None,
            "activeFile": None,
            "openFiles": []
        }

    pid = proc.pid
    open_dwgs = get_open_files_with_ext(proc, '.dwg')
    active_doc = os.path.basename(open_dwgs[0]) if open_dwgs else None

    com_connected = False
    try:
        import win32com.client
        acad = win32com.client.GetActiveObject('AutoCAD.Application')
        if acad and hasattr(acad, 'ActiveDocument'):
            active_doc = acad.ActiveDocument.Name
            com_connected = True
    except Exception:
        pass

    return {
        "name": "AutoCAD",
        "running": True,
        "status": "online",
        "message": f"Đang hoạt động (PID {pid})",
        "pid": pid,
        "comConnected": com_connected,
        "activeFile": active_doc,
        "openFiles": open_dwgs
    }


def get_3dsmax_status(proc=None):
    """Kiểm tra trạng thái 3ds Max và Max Bridge (Port 8096)."""
    if proc is None and psutil:
        proc = get_all_aec_processes().get('3dsmax')

    bridge_ports = [8096, 8098]
    bridge_online = False
    active_scene = None
    bridge_port = None
    bridge_info = {}

    # Chỉ probe cổng nếu tiến trình đang chạy
    if proc:
        for p in bridge_ports:
            data = probe_http_json(f"http://127.0.0.1:{p}/api/status", timeout=0.3)
            if data and isinstance(data, dict):
                bridge_online = True
                bridge_port = p
                bridge_info = data
                active_scene = data.get("current_scene") or data.get("scene") or data.get("title")
                break

    if not proc and not bridge_online:
        return {
            "name": "3ds Max",
            "running": False,
            "bridgeOnline": False,
            "status": "offline",
            "message": "Chưa mở (Tùy chọn - không bắt buộc)",
            "pid": None,
            "port": None,
            "activeFile": None,
            "openFiles": []
        }

    pid = proc.pid if proc else None
    open_max = get_open_files_with_ext(proc, '.max')
    if not active_scene and open_max:
        active_scene = os.path.basename(open_max[0])

    msg = f"Đang hoạt động (PID {pid})" if pid else "Bridge đang phản hồi"
    if bridge_online:
        msg += f" • Bridge :Port {bridge_port} Online"
    else:
        msg += " • Bridge :8096 chưa nạp"

    return {
        "name": "3ds Max",
        "running": True,
        "bridgeOnline": bridge_online,
        "status": "online",
        "message": msg,
        "pid": pid,
        "port": bridge_port,
        "activeFile": active_scene,
        "openFiles": open_max,
        "bridgeInfo": bridge_info
    }


def get_revit_status(proc=None):
    """Kiểm tra trạng thái Revit và Revit Bridge (Port 8090, 8088, 8092)."""
    if proc is None and psutil:
        proc = get_all_aec_processes().get('revit')

    ports_to_check = []
    local_port_file = os.path.join(CURRENT_DIR, "bridge_port.txt")
    if os.path.exists(local_port_file):
        try:
            with open(local_port_file, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val.isdigit():
                    ports_to_check.append(int(val))
        except Exception:
            pass
    for p in [8090, 8088, 8092]:
        if p not in ports_to_check:
            ports_to_check.append(p)

    bridge_online = False
    bridge_port = None
    status_data = {}
    model_data = {}

    if proc:
        for p in ports_to_check:
            s = probe_http_json(f"http://127.0.0.1:{p}/api/status", timeout=0.3)
            if s and isinstance(s, dict) and not s.get("error"):
                bridge_online = True
                bridge_port = p
                status_data = s
                m = probe_http_json(f"http://127.0.0.1:{p}/api/model", timeout=0.3)
                if m and isinstance(m, dict):
                    model_data = m
                break

    if not proc and not bridge_online:
        return {
            "name": "Autodesk Revit",
            "running": False,
            "bridgeOnline": False,
            "status": "offline",
            "message": "Chưa mở (Tùy chọn - không bắt buộc)",
            "pid": None,
            "port": None,
            "activeFile": None,
            "activeView": None,
            "counts": {},
            "openFiles": []
        }

    pid = proc.pid if proc else None
    open_rvt = get_open_files_with_ext(proc, '.rvt')
    active_doc = status_data.get("title")
    if not active_doc and open_rvt:
        active_doc = os.path.basename(open_rvt[0])

    active_view = status_data.get("activeView")
    view_name = active_view.get("name") if isinstance(active_view, dict) else str(active_view or "")

    msg = f"Đang hoạt động (PID {pid})" if pid else "Bridge đang phản hồi"
    if bridge_online:
        msg += f" • Bridge :Port {bridge_port} Online"
    else:
        msg += " • Bridge :8090 chưa nạp"

    return {
        "name": "Autodesk Revit",
        "running": True,
        "bridgeOnline": bridge_online,
        "status": "online",
        "message": msg,
        "pid": pid,
        "port": bridge_port,
        "activeFile": active_doc,
        "activeView": view_name,
        "counts": model_data.get("counts", {}),
        "openFiles": open_rvt
    }


def get_dashboard_status():
    """Kiểm tra trạng thái Web Dashboard (Port 5000)."""
    running = False
    try:
        req = urllib.request.Request("http://127.0.0.1:5000/favicon.ico")
        with urllib.request.urlopen(req, timeout=0.6) as res:
            if res.status in (200, 302, 304):
                running = True
    except Exception:
        # Thử lại với root
        try:
            req = urllib.request.Request("http://127.0.0.1:5000/")
            with urllib.request.urlopen(req, timeout=0.6) as res:
                if res.status in (200, 302, 304):
                    running = True
        except Exception:
            running = False

    return {
        "name": "Web Dashboard",
        "running": running,
        "port": 5000,
        "url": "http://127.0.0.1:5000",
        "message": "Sẵn sàng (http://127.0.0.1:5000)" if running else "Chưa khởi động"
    }


def get_hub_status():
    """Lấy tổng hợp trạng thái của toàn bộ hệ sinh thái AEC."""
    procs = get_all_aec_processes()
    acad = get_autocad_status(procs.get('acad'))
    max_app = get_3dsmax_status(procs.get('3dsmax'))
    revit = get_revit_status(procs.get('revit'))
    dash = get_dashboard_status()

    # Tính toán tóm tắt
    active_apps = []
    if acad.get("running"):
        active_apps.append("AutoCAD")
    if max_app.get("running") or max_app.get("bridgeOnline"):
        active_apps.append("3ds Max")
    if revit.get("running") or revit.get("bridgeOnline"):
        active_apps.append("Revit")

    summary_str = ", ".join(active_apps) if active_apps else "Tất cả phần mềm đang ở chế độ chờ"

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "autocad": acad,
        "max": max_app,
        "revit": revit,
        "dashboard": dash,
        "activeCount": len(active_apps),
        "summary": summary_str
    }


def print_banner():
    """In giao diện bảng điều khiển AEC Automation Hub trực quan ra console."""
    status = get_hub_status()
    acad = status["autocad"]
    max_app = status["max"]
    revit = status["revit"]
    dash = status["dashboard"]

    print("================================================================================")
    print("        AEC AUTOMATION HUB • MULTI-CAD ECOSYSTEM (AutoCAD • 3ds Max • Revit)   ")
    print("================================================================================")
    print(f" Thời gian kiểm tra: {status['timestamp']}")
    print(f" Phần mềm đang mở:   {status['summary']}")
    print("--------------------------------------------------------------------------------")

    # 1. AutoCAD
    if acad["running"]:
        doc_info = f" • Bản vẽ: {acad['activeFile']}" if acad['activeFile'] else ""
        print(f" [AutoCAD]    🟢 ONLINE   (PID {acad['pid']}){doc_info}")
    else:
        print(f" [AutoCAD]    ⚪ OFFLINE  (Chưa mở - Tùy chọn)")

    # 2. 3ds Max
    if max_app["running"] or max_app["bridgeOnline"]:
        scene_info = f" • Scene: {max_app['activeFile']}" if max_app['activeFile'] else ""
        b_port = f" :Port {max_app['port']}" if max_app['port'] else ""
        state_dot = "🟢 ONLINE" if max_app["bridgeOnline"] else "🟡 RUNNING"
        print(f" [3ds Max]    {state_dot}   (PID {max_app['pid']}{b_port}){scene_info}")
    else:
        print(f" [3ds Max]    ⚪ OFFLINE  (Chưa mở - Tùy chọn)")

    # 3. Revit
    if revit["running"] or revit["bridgeOnline"]:
        doc_info = f" • Model: {revit['activeFile']}" if revit['activeFile'] else ""
        v_info = f" [{revit['activeView']}]" if revit['activeView'] else ""
        b_port = f" :Port {revit['port']}" if revit['port'] else ""
        state_dot = "🟢 ONLINE" if revit["bridgeOnline"] else "🟡 RUNNING"
        print(f" [Revit]      {state_dot}   (PID {revit['pid']}{b_port}){doc_info}{v_info}")
    else:
        print(f" [Revit]      ⚪ OFFLINE  (Chưa mở - Tùy chọn)")

    # 4. Web Dashboard
    if dash["running"]:
        print(f" [Dashboard]  🟢 SẴN SÀNG  {dash['url']} (Giao diện điều khiển Web)")
    else:
        print(f" [Dashboard]  ⚪ CHƯA BẬT (Chạy run_dashboard.bat để khởi động trên cổng 5000)")

    print("================================================================================")
    print(" Ghi chú: Hệ thống hoạt động độc lập cho từng phần mềm. KHÔNG BẮT BUỘC Revit")
    print("          phải được bật để sử dụng các tính năng của AutoCAD hoặc 3ds Max.")
    print("================================================================================")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["json", "--json", "-j"]:
        print(json.dumps(get_hub_status(), indent=2, ensure_ascii=False))
    else:
        print_banner()

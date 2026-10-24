import sys
import json
import urllib.request
import urllib.error
import os

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def is_revit_running():
    try:
        import psutil
        for p in psutil.process_iter(['name']):
            if p.info['name'] and 'revit' in p.info['name'].lower():
                return True
        return False
    except Exception:
        return True

def get_base_url():
    for p_file in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge_port.txt"),
        os.path.join(os.environ.get("TEMP", ""), "revit_bridge_port.txt")
    ]:
        if os.path.exists(p_file):
            try:
                with open(p_file, "r", encoding="utf-8") as f:
                    val = f.read().strip()
                    if val.isdigit():
                        return f"http://127.0.0.1:{val}"
            except Exception:
                pass
    if is_revit_running():
        for p in [8090, 8088, 8092]:
            try:
                req = urllib.request.Request(f"http://127.0.0.1:{p}/api/status")
                with urllib.request.urlopen(req, timeout=0.3) as res:
                    if res.status == 200:
                        return f"http://127.0.0.1:{p}"
            except Exception:
                pass
    return "http://127.0.0.1:8090"

BASE_URL = get_base_url()

def request_json(url, data=None, timeout=120):
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8') if data else None,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.loads(res.read().decode('utf-8'))
    except urllib.error.URLError as e:
        return {"error": f"Connection failed to {url}: {e}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    if len(sys.argv) < 2:
        import aec_hub
        aec_hub.print_banner()
        return

    cmd = sys.argv[1].lower()

    if cmd in ["hub", "all", "aec"]:
        import aec_hub
        if "--json" in sys.argv:
            print(json.dumps(aec_hub.get_hub_status(), indent=2, ensure_ascii=False))
        else:
            aec_hub.print_banner()
    elif cmd == "status":
        res = request_json(f"{BASE_URL}/api/status", timeout=1.5)
        if "error" in res:
            import aec_hub
            r_stat = aec_hub.get_revit_status()
            res = {
                "online": r_stat.get("bridgeOnline", False),
                "app": "Autodesk Revit",
                "status": "offline" if not r_stat.get("running") else "bridge_offline",
                "message": r_stat.get("message", "Revit chưa bật hoặc chưa nạp Revit Bridge (Port 8090)"),
                "pid": r_stat.get("pid"),
                "activeFile": r_stat.get("activeFile")
            }
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "model":
        res = request_json(f"{BASE_URL}/api/model", timeout=1.5)
        if "error" in res:
            res = {
                "online": False,
                "status": "offline",
                "message": "Revit chưa kết nối hoặc chưa mở model."
            }
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "query":
        cat = sys.argv[2] if len(sys.argv) > 2 else "walls"
        res = request_json(f"{BASE_URL}/api/execute", {"action": "query", "category": cat})
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "create-level":
        if len(sys.argv) < 4:
            print("Usage: revit_cli.py create-level <name> <elevation_meters>")
            sys.exit(1)
        name = sys.argv[2]
        elev = float(sys.argv[3])
        res = request_json(f"{BASE_URL}/api/execute", {"action": "create_level", "name": name, "elevation": elev})
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "create-grid":
        if len(sys.argv) < 7:
            print("Usage: revit_cli.py create-grid <name> <startX> <startY> <endX> <endY>")
            sys.exit(1)
        name = sys.argv[2]
        x1, y1, x2, y2 = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
        res = request_json(f"{BASE_URL}/api/execute", {"action": "create_grid", "name": name, "startX": x1, "startY": y1, "endX": x2, "endY": y2})
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "link-cad":
        if len(sys.argv) < 3:
            print("Usage: revit_cli.py link-cad <dwg_path>")
            sys.exit(1)
        dwg = sys.argv[2]
        res = request_json(f"{BASE_URL}/api/execute", {"action": "link_cad", "dwgPath": dwg, "currentViewOnly": True})
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "convert-ifc":
        ifc_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/Downloads/machine")
        out_dir = sys.argv[3] if len(sys.argv) > 3 else ifc_dir
        res = request_json(f"{BASE_URL}/api/execute", {"action": "convert_ifc_to_rfa", "ifcDir": ifc_dir, "outputDir": out_dir})
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "apply-colors":
        dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "Release", "net10.0-windows", "DynamicConverter.dll")
        res = request_json(f"{BASE_URL}/api/execute", {
            "action": "execute_dynamic",
            "dllPath": dll_path,
            "typeName": "RevitScript.ColorChanger",
            "methodName": "ApplyPdfColors"
        })
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "inspect-family":
        dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "Release", "net10.0-windows", "DynamicConverter.dll")
        res = request_json(f"{BASE_URL}/api/execute", {
            "action": "execute_dynamic",
            "dllPath": dll_path,
            "typeName": "RevitScript.Script",
            "methodName": "InspectFamily"
        })
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "save":
        res = request_json(f"{BASE_URL}/api/execute", {"action": "save_document"})
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "hide-floors":
        dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "Release", "net10.0-windows", "DynamicConverter.dll")
        res = request_json(f"{BASE_URL}/api/execute", {
            "action": "execute_dynamic",
            "dllPath": dll_path,
            "typeName": "RevitScript.FloorHider",
            "methodName": "Run",
            "mode": "hide"
        })
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif cmd == "unhide-floors":
        dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "Release", "net10.0-windows", "DynamicConverter.dll")
        res = request_json(f"{BASE_URL}/api/execute", {
            "action": "execute_dynamic",
            "dllPath": dll_path,
            "typeName": "RevitScript.FloorHider",
            "methodName": "Run",
            "mode": "unhide"
        })
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()

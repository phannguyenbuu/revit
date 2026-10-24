#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
3ds Max AI Copilot CLI
Command-line interface to interact with Autodesk 3ds Max through the AI Bridge.
"""

import sys
import os
import json
import urllib.request
import urllib.error

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_base_url():
    # 1. Check local repo port file
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge_port.txt"),
        os.path.join(os.environ.get("TEMP", ""), "max_bridge_port.txt")
    ]
    for p_file in candidates:
        if os.path.exists(p_file):
            try:
                with open(p_file, "r", encoding="utf-8") as f:
                    val = f.read().strip()
                    if val.isdigit():
                        return f"http://127.0.0.1:{val}"
            except Exception:
                pass

    # 2. Probe candidate ports and verify it is 3ds Max
    for p in [8096, 8098, 8099, 8097, 8094]:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{p}/api/status")
            with urllib.request.urlopen(req, timeout=0.5) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode('utf-8'))
                    if data.get("app") == "Autodesk 3ds Max":
                        return f"http://127.0.0.1:{p}"
        except Exception:
            pass

    return "http://127.0.0.1:8096"

BASE_URL = get_base_url()

def request_json(endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8') if data is not None else None,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=45) as res:
            return json.loads(res.read().decode('utf-8'))
    except urllib.error.URLError as e:
        return {"error": f"Connection failed to 3ds Max bridge ({url}): {e}"}
    except Exception as e:
        return {"error": str(e)}

def print_help():
    help_text = """
3ds Max AI Copilot CLI - Điều khiển 3ds Max từ Terminal / AI

Cách dùng:
  python max_cli.py status                       Xem trạng thái 3ds Max & scene hiện tại
  python max_cli.py scene [limit]                Xem danh sách đối tượng, layer, vật liệu
  python max_cli.py execute "<maxscript_code>"   Chạy mã MAXScript trực tiếp trong 3ds Max
  python max_cli.py execute-py "<python_code>"   Chạy mã Python trực tiếp trong 3ds Max
  python max_cli.py create <type> [x] [y] [z]    Tạo đối tượng (Box, Sphere, Teapot, Cylinder)
  python max_cli.py create-lights                Tạo hệ thống chiếu sáng 3-Point Light
  python max_cli.py create-camera [x] [y] [z]    Tạo Camera
  python max_cli.py render [output.png] [w] [h]  Render khung nhìn hiện tại ra ảnh
  python max_cli.py export <filepath> [--sel]    Xuất file FBX / OBJ / DAE
  python max_cli.py clean                        Dọn dẹp layer rác & giải phóng bộ nhớ
  python max_cli.py chat "<nội dung>"            Gửi prompt tương tác tới chatbot trong 3ds Max
"""
    print(help_text.strip())

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "status":
        res = request_json("/api/status")
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "scene":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 50
        res = request_json("/api/scene")
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "execute":
        if len(sys.argv) < 3:
            print("Lỗi: Vui lòng nhập mã MAXScript cần chạy. Ví dụ: python max_cli.py execute \"box length:50 width:50\"")
            sys.exit(1)
        code = sys.argv[2]
        res = request_json("/api/execute", {"language": "maxscript", "code": code})
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "execute-py":
        if len(sys.argv) < 3:
            print("Lỗi: Vui lòng nhập mã Python cần chạy.")
            sys.exit(1)
        code = sys.argv[2]
        res = request_json("/api/execute", {"language": "python", "code": code})
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "create":
        ptype = sys.argv[2] if len(sys.argv) > 2 else "Box"
        x = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
        y = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
        z = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
        name = sys.argv[6] if len(sys.argv) > 6 else None
        res = request_json("/api/action", {
            "action": "create_primitive",
            "type": ptype,
            "position": [x, y, z],
            "name": name
        })
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "create-lights":
        res = request_json("/api/action", {"action": "create_light_setup"})
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "create-camera":
        x = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
        y = float(sys.argv[3]) if len(sys.argv) > 3 else -250.0
        z = float(sys.argv[4]) if len(sys.argv) > 4 else 150.0
        res = request_json("/api/action", {
            "action": "create_camera",
            "position": [x, y, z]
        })
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "render":
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.getcwd(), "quick_render.png")
        w = int(sys.argv[3]) if len(sys.argv) > 3 else 1920
        h = int(sys.argv[4]) if len(sys.argv) > 4 else 1080
        res = request_json("/api/action", {
            "action": "quick_render",
            "output_path": os.path.abspath(out),
            "width": w,
            "height": h
        })
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "export":
        if len(sys.argv) < 3:
            print("Lỗi: Vui lòng nhập đường dẫn file xuất (FBX / OBJ / ...)")
            sys.exit(1)
        out = sys.argv[2]
        sel_only = "--sel" in sys.argv or "--selected" in sys.argv
        res = request_json("/api/action", {
            "action": "export_model",
            "path": os.path.abspath(out),
            "selected_only": sel_only
        })
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "clean":
        res = request_json("/api/action", {"action": "clean_scene"})
        print(json.dumps(res, indent=2, ensure_ascii=False))

    elif cmd == "chat":
        if len(sys.argv) < 3:
            print("Lỗi: Vui lòng nhập nội dung chat.")
            sys.exit(1)
        prompt = " ".join(sys.argv[2:])
        res = request_json("/api/chat", {"prompt": prompt})
        print(json.dumps(res, indent=2, ensure_ascii=False))

    else:
        print(f"Lệnh không xác định: {cmd}")
        print_help()

if __name__ == "__main__":
    main()

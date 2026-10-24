#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
revit_tray.py
Ứng dụng System Tray / Taskbar Icon cho RevitAI Automation Hub
- Biểu tượng thường trực ở góc Taskbar (System Tray).
- Click chuột trái: Mở RevitAI Dashboard dạng cửa sổ ứng dụng (App Mode).
- Click chuột phải: Menu điều khiển (Mở Dashboard, Kiểm tra Revit Bridge, Mở thư mục, Thoát).
- Tự động duy trì và giám sát Flask Server trên cổng 5000.
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser
import urllib.request
import urllib.error
from PIL import Image
import pystray

# Đảm bảo UTF-8
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(CURRENT_DIR, "revit_ai.ico")
PNG_PATH = os.path.join(CURRENT_DIR, "revit_ai.png")
PORT = 5000
DASHBOARD_URL = f"http://127.0.0.1:{PORT}"

server_process = None


def is_server_running():
    try:
        with urllib.request.urlopen(f"{DASHBOARD_URL}/api/model-info", timeout=1.0) as res:
            return res.status == 200
    except Exception:
        return False


def start_flask_server():
    """Khởi động Flask Server nếu chưa chạy."""
    global server_process
    if is_server_running():
        return

    dashboard_script = os.path.join(CURRENT_DIR, "web_dashboard.py")
    python_exe = sys.executable
    # Sử dụng pythonw nếu có để ẩn cửa sổ console
    pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = python_exe

    server_process = subprocess.Popen(
        [pythonw, dashboard_script],
        cwd=CURRENT_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )


def open_dashboard(icon=None, item=None):
    """Mở giao diện Web dạng cửa sổ App độc lập (Chrome hoặc Edge App mode)."""
    # Đảm bảo server đang chạy
    if not is_server_running():
        start_flask_server()
        time.sleep(1.0)

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    for browser in [chrome_path, edge_path]:
        if os.path.exists(browser):
            try:
                subprocess.Popen([browser, f"--app={DASHBOARD_URL}"])
                return
            except Exception:
                pass

    # Fallback vào trình duyệt mặc định
    webbrowser.open(DASHBOARD_URL)


def check_aec_status(icon=None, item=None):
    """Kiểm tra kết nối tới AutoCAD, 3ds Max, Revit và hiển thị thông báo khay hệ thống."""
    try:
        import aec_hub
        stat = aec_hub.get_hub_status()
        acad = stat["autocad"]
        max_app = stat["max"]
        revit = stat["revit"]

        lines = []
        acad_desc = f"🟢 Online ({acad['activeFile']})" if (acad['running'] and acad['activeFile']) else ("🟢 Online" if acad['running'] else "⚪ Offline")
        lines.append(f"• AutoCAD: {acad_desc}")

        max_desc = f"🟢 Online ({max_app['activeFile']})" if (max_app['running'] and max_app['activeFile']) else ("🟢 Online" if (max_app['running'] or max_app['bridgeOnline']) else "⚪ Offline")
        lines.append(f"• 3ds Max: {max_desc}")

        revit_desc = f"🟢 Online ({revit['activeFile']})" if (revit['running'] and revit['activeFile']) else ("🟢 Online" if (revit['running'] or revit['bridgeOnline']) else "⚪ Offline")
        lines.append(f"• Revit: {revit_desc}")

        msg = "\n".join(lines)
        if icon:
            icon.notify(msg, f"AEC Hub: {stat['summary']}")
    except Exception as ex:
        if icon:
            icon.notify(f"Lỗi kiểm tra AEC Hub: {ex}", "AEC Hub")


def open_project_folder(icon=None, item=None):
    """Mở thư mục dự án trong Windows File Explorer."""
    os.startfile(CURRENT_DIR)


def exit_action(icon, item):
    """Thoát ứng dụng Taskbar và dừng tiến trình con nếu có."""
    global server_process
    icon.stop()
    if server_process:
        try:
            server_process.terminate()
        except Exception:
            pass


def main():
    # 1. Khởi động Flask server ngầm
    start_flask_server()

    # 2. Tải icon
    if os.path.exists(PNG_PATH):
        image = Image.open(PNG_PATH)
    elif os.path.exists(ICON_PATH):
        image = Image.open(ICON_PATH)
    else:
        # Fallback tạo icon tạm
        image = Image.new('RGB', (64, 64), color=(79, 70, 229))

    # 3. Tạo menu ngữ cảnh
    menu = pystray.Menu(
        pystray.MenuItem("🚀 Mở AEC Hub Dashboard", open_dashboard, default=True),
        pystray.MenuItem("⚡ Kiểm tra trạng thái CAD • Max • Revit", check_aec_status),
        pystray.MenuItem("📁 Mở thư mục dự án", open_project_folder),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌ Thoát", exit_action)
    )

    # 4. Khởi tạo Tray Icon
    icon = pystray.Icon(
        "RevitAI_Studio",
        image,
        "RevitAI Automation Hub (Port 5000)",
        menu
    )

    # Hiển thị thông báo chào mừng
    def show_welcome():
        time.sleep(1.0)
        try:
            icon.notify(
                "Click đúp vào icon để mở Dashboard điều khiển AutoCAD • 3ds Max • Revit!",
                "RevitAI Hub đã sẵn sàng (Port 5000)"
            )
        except Exception:
            pass

    threading.Thread(target=show_welcome, daemon=True).start()

    # 5. Chạy vòng lặp sự kiện của khay hệ thống
    icon.run()


if __name__ == "__main__":
    main()

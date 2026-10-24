#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Auto-installer for 3ds Max AI Copilot Bridge & Chatbot.
Installs startup hooks into 3ds Max user scripts and macros directories.
"""

import os
import sys
import shutil

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")
MAX_BASE_DIR = os.path.join(LOCALAPPDATA, "Autodesk", "3dsMax")
SOURCE_STARTUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "max_bridge_startup.ms")

def install():
    print("=" * 60)
    print(" Cài đặt 3ds Max AI Copilot Bridge & Chatbot")
    print("=" * 60)

    if not os.path.exists(SOURCE_STARTUP):
        print(f"Lỗi: Không tìm thấy file nguồn: {SOURCE_STARTUP}")
        return False

    if not os.path.exists(MAX_BASE_DIR):
        print(f"Cảnh báo: Không tìm thấy thư mục 3ds Max tại {MAX_BASE_DIR}")
        return False

    installed_versions = []

    for entry in os.listdir(MAX_BASE_DIR):
        full_path = os.path.join(MAX_BASE_DIR, entry)
        if os.path.isdir(full_path):
            enu_path = os.path.join(full_path, "ENU")
            if os.path.exists(enu_path):
                # 1. Startup folder
                startup_dir = os.path.join(enu_path, "scripts", "startup")
                os.makedirs(startup_dir, exist_ok=True)
                dest_startup = os.path.join(startup_dir, "max_ai_bridge_startup.ms")
                shutil.copy2(SOURCE_STARTUP, dest_startup)

                # 2. Usermacros folder
                macros_dir = os.path.join(enu_path, "usermacros")
                os.makedirs(macros_dir, exist_ok=True)
                dest_macro = os.path.join(macros_dir, "MaxAI_Chatbot.mcr")
                shutil.copy2(SOURCE_STARTUP, dest_macro)

                print(f"[OK] Đã cài đặt hook tự động cho: {entry}")
                print(f"     - Startup: {dest_startup}")
                print(f"     - Macro  : {dest_macro}")
                installed_versions.append(entry)

    if installed_versions:
        print("\n" + "=" * 60)
        print(f"Hoàn tất cài đặt thành công cho {len(installed_versions)} phiên bản 3ds Max!")
        print("Tất cả các lần khởi động 3ds Max tiếp theo sẽ tự động bật Bridge & Chatbot.")
        print("=" * 60)
        return True
    else:
        print("Không tìm thấy cấu hình phiên bản 3ds Max nào có thư mục ENU.")
        return False

if __name__ == "__main__":
    install()

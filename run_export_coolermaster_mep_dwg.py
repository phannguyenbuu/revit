#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_export_coolermaster_mep_dwg.py
Tự động xuất bản vẽ DWG theo từng tầng và từng hạng mục MEP kèm Tag Cos Cao Độ (BOP/BOD/CL)
cho dự án Coolermaster Phase 2 BIM Model.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import subprocess

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DLL_PATH = os.path.join(CURRENT_DIR, "bin", "Release", "net10.0-windows", "DynamicConverter_DoorD7_v16.dll")
OUTPUT_DIR = r"D:\Dropbox\_Documents\_KIEN TRUC 2026\CM Fire Protect\Coolermaster 2 - BIM model\DWG_MEP_Coolermaster_Phase2"

def get_base_url():
    for p_file in [
        os.path.join(CURRENT_DIR, "bridge_port.txt"),
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
    for p in [8090, 8088, 8092]:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{p}/api/status")
            with urllib.request.urlopen(req, timeout=0.4) as res:
                if res.status == 200:
                    return f"http://127.0.0.1:{p}"
        except Exception:
            pass
    return "http://127.0.0.1:8090"

def is_revit_bridge_online(url):
    try:
        req = urllib.request.Request(f"{url}/api/status")
        with urllib.request.urlopen(req, timeout=0.8) as res:
            if res.status == 200:
                data = json.loads(res.read().decode('utf-8'))
                return True, data
    except Exception:
        pass
    return False, {}

def main():
    print("=" * 80)
    print("   XUẤT BẢN VẼ DWG MEP COOLERMASTER PHASE 2 THEO TẦNG & GẮN TAG COS CAO ĐỘ")
    print("=" * 80)
    print(f" Thư mục xuất DWG: {OUTPUT_DIR}")
    print(" Các hạng mục MEP:")
    print("   1. Ống Chữa Cháy (PCCC / Sprinkler Branch & Main)")
    print("   2. Ống Gió Hút Khói Sự Cố (Smoke Exhaust)")
    print("   3. Ống Gió Thông Gió & Bù Khí (HVAC)")
    print("   4. Ống Điện & Máng Cáp (Conduits & Cable Trays)")
    print("   5. Tuyến Busway Trạm Điện (12 Tuyến Busway)")
    print("   6. Thiết Bị Báo Khói / Báo Cháy (Fire Alarm)")
    print(" Yêu cầu đặc biệt: Tự động tính toán & gắn Tag Cos cao độ (BOP/BOD/CL) trên mỗi ống")
    print("-" * 80)

    base_url = get_base_url()
    online, status_info = is_revit_bridge_online(base_url)

    if not online:
        print(f"[THÔNG BÁO] Revit chưa mở hoặc Revit Bridge chưa phản hồi trên cổng 8090.")
        print("Đang khởi động Revit 2025 với file Coolermaster 2 BIM Model...")
        bat_path = os.path.join(CURRENT_DIR, "launch_revit_coolermaster.bat")
        if os.path.exists(bat_path):
            subprocess.Popen([bat_path], shell=True)
            print("Đang chờ Revit mở và nạp Add-in Bridge (khoảng 30-45 giây)...")
            for i in range(45):
                time.sleep(2)
                online, status_info = is_revit_bridge_online(base_url)
                if online:
                    print(f"\n[KẾT NỐI THÀNH CÔNG] Revit Bridge đã online sau { (i+1)*2 }s!")
                    break
                print(".", end="", flush=True)

        if not online:
            print("\n[LỖI] Revit chưa sẵn sàng. Vui lòng mở file Coolermaster 2 trong Revit 2025 rồi chạy lại script này.")
            return

    doc_title = status_info.get("title", "Coolermaster Model")
    print(f"[REVIT ONLINE] Đang kết nối tới mô hình: {doc_title}")

    payload = {
        "action": "execute_dynamic",
        "dllPath": DLL_PATH,
        "typeName": "RevitScript.ExportCoolermasterMepDwg",
        "methodName": "Run",
        "args": {
            "outputDir": OUTPUT_DIR,
            "tagElevation": True,
            "minSegmentLengthMm": 800.0,
            "trades": [
                "chua_chay",
                "hut_khoi",
                "thong_gio",
                "dien_mang_cap",
                "busway",
                "bao_khoi"
            ]
        }
    }

    print(f"\nĐang gửi lệnh xử lý và xuất DWG tới Revit Bridge (timeout: 7200s)...")
    req = urllib.request.Request(
        f"{base_url}/api/execute",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=7200) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = round(time.time() - t0, 1)

            if data.get("success"):
                print("=" * 80)
                print(f" HOÀN TẤT XUẤT BẢN VẼ DWG TRONG {elapsed} GIÂY!")
                print(f" • Tổng số bản vẽ DWG đã xuất: {data.get('totalFiles', 0)}")
                print(f" • Tổng số Tag Cos cao độ đã gắn: {data.get('totalTags', 0)}")
                print(f" • Thư mục lưu trữ: {data.get('outputDirectory', OUTPUT_DIR)}")
                print("-" * 80)

                files = data.get("files", [])
                for f in files:
                    size_kb = round(f.get("sizeBytes", 0) / 1024, 1)
                    print(f"   ✓ [{f.get('trade')}] {f.get('level')} -> {f.get('fileName')} ({size_kb} KB)")

                print("=" * 80)
            else:
                print(f"[THẤT BẠI] Lỗi từ Revit: {data.get('error')}")
                if data.get("log"):
                    print("\nLog chi tiết:\n" + data.get("log")[-1000:])
    except Exception as ex:
        print(f"[LỖI NGOẠI LỆ] {ex}")

if __name__ == "__main__":
    main()

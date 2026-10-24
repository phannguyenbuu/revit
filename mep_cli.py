#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
================================================================================
mep_cli.py - RevitAI MEP Automation Command Line Interface
================================================================================
Chạy tự động hóa toàn diện 6 chức năng MEP & 3D BIM từ Terminal:
✅ 1. Thiết kế hệ thống điện và chiếu sáng
✅ 2. Thiết kế hệ thống cấp thoát nước
✅ 3. Thiết kế điều hòa, thông gió HVAC
✅ 4. Dựng mô hình BIM 3D chuyên nghiệp (IFC 4, 3D Wavefront OBJ, AutoCAD DXF)
✅ 5. Kiểm tra xung đột hệ thống MEP (Clash Detection & Auto-Resolution)
✅ 6. Bóc tách khối lượng (BOQ Schedule) & Xuất bản vẽ kỹ thuật CAD
================================================================================
"""

import os
import sys
import argparse
import subprocess
import json

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mep_bim_engine import run_complete_mep_pipeline, EXPORTS_DIR

def main():
    parser = argparse.ArgumentParser(description="RevitAI MEP 3D BIM Automation CLI")
    parser.add_argument("--width", type=float, default=12.0, help="Chiều rộng công trình (mét), mặc định 12.0m")
    parser.add_argument("--depth", type=float, default=8.0, help="Chiều sâu công trình (mét), mặc định 8.0m")
    parser.add_argument("--height", type=float, default=3.6, help="Chiều cao tầng (mét), mặc định 3.6m")
    parser.add_argument("--floors", type=int, default=2, help="Số tầng công trình, mặc định 2 tầng")
    parser.add_argument("--no-resolve", action="store_true", help="Không tự động nắn tuyến xử lý va chạm")
    parser.add_argument("--open-folder", action="store_true", help="Tự động mở thư mục xuất file trên Windows Explorer")

    args = parser.parse_args()

    print("================================================================================")
    print("        🚀 REVITAI MEP 3D BIM AUTOMATION PIPELINE (CLI) 🚀                      ")
    print("================================================================================")
    print(f"📐 Thông số đầu vào:")
    print(f" - Kích thước mặt bằng: {args.width}m x {args.depth}m (S = {args.width*args.depth:.1f} m² / tầng)")
    print(f" - Số tầng: {args.floors} tầng | Chiều cao tầng: {args.height}m")
    print(f" - Chế độ tự động nắn tuyến va chạm: {'BẬT (Khuyến nghị)' if not args.no_resolve else 'TẮT'}")
    print("--------------------------------------------------------------------------------")
    print("⏳ Đang thực thi tính toán phụ tải, thiết kế tự động & xuất mô hình BIM 3D...")

    w_mm = args.width * 1000.0
    d_mm = args.depth * 1000.0
    h_mm = args.height * 1000.0
    auto_resolve = not args.no_resolve

    result = run_complete_mep_pipeline(
        building_width=w_mm,
        building_depth=d_mm,
        floor_height=h_mm,
        num_floors=args.floors,
        auto_resolve_clashes=auto_resolve
    )

    s = result["summary"]
    boq = result["boq_schedule"]
    clashes = result["clash_detection"]
    files = result["exported_files"]

    print("\n================================================================================")
    print(f"✅ QUY TRÌNH HOÀN TẤT THÀNH CÔNG TRONG {result['elapsed_seconds']} GIÂY!")
    print("================================================================================")
    print(f"📊 1. KẾT QUẢ THIẾT KẾ ĐIỆN & CHIẾU SÁNG:")
    print(f" - Tổng số bộ đèn LED Panel & Downlight: {s['total_lighting_fixtures']} bộ")
    print(f" - Tổng công suất chiếu sáng: {s['total_lighting_power_kw']} kW")
    print(f" - Chiều dài máng cáp điện chính & nhánh: {s['total_cable_trays_linear_meters']} mét")

    print(f"\n🚰 2. KẾT QUẢ THIẾT KẾ CẤP THOÁT NƯỚC:")
    print(f" - Tổng chiều dài ống cấp nước PPR & thoát uPVC: {s['total_pipes_linear_meters']} mét")
    print(f" - Hệ thống thiết bị vệ sinh: Đầy đủ Bồn cầu, Lavabo, Phễu thu sàn bẫy mùi & Bồn nước 2000L")

    print(f"\n❄️ 3. KẾT QUẢ THIẾT KẾ ĐIỀU HÒA, THÔNG GIÓ HVAC:")
    print(f" - Tổng công suất lạnh thiết kế: {s['total_hvac_cooling_kw']} kW")
    print(f" - Tổng chiều dài đường ống gió cấp tole tráng kẽm: {s['total_ducts_linear_meters']} mét")
    print(f" - Thiết bị: FCU giấu trần, Miệng gió khuếch tán 600x600, Quạt hút WC, Cụm dàn nóng VRV")

    print(f"\n🏗️ 4. MÔ HÌNH BIM 3D CHUYÊN NGHIỆP:")
    print(f" - Tổng số cấu kiện BIM tích hợp: {s['total_elements']} phần tử")
    print(f" - Định dạng chuẩn quốc tế: IFC 4, Wavefront 3D OBJ/MTL, AutoCAD 3D DXF")

    print(f"\n💥 5. KIỂM TRA XUNG ĐỘT (CLASH DETECTION):")
    print(f" - Phát hiện ban đầu: {clashes['initial_clashes_count']} điểm xung đột (Ống gió vs Dầm, Máng cáp vs Ống nước)")
    if clashes.get("auto_resolve"):
        print(f" - Tự động nắn tuyến triệt tiêu: {clashes['auto_resolve']['resolved_count']} xung đột thành công!")
        print(f" - Số xung đột còn lại: {clashes['auto_resolve']['remaining_clashes_count']}")

    print(f"\n💰 6. BÓC TÁCH KHỐI LƯỢNG & BẢN VẼ KỸ THUẬT (BOQ SCHEDULE):")
    print(f" - Tổng chi phí vật tư: {boq['total_material_cost_vnd']:,} đ".replace(",", "."))
    print(f" - Tổng chi phí nhân công lắp đặt: {boq['total_labor_cost_vnd']:,} đ".replace(",", "."))
    print(f" - TỔNG DỰ TOÁN MEP (GỒM VAT 10%): {boq['formatted_total']}")

    print(f"\n📁 CÁC FILE ĐÃ XUẤT TỰ ĐỘNG:")
    for k, v in files.items():
        size_kb = os.path.getsize(v) / 1024.0 if os.path.exists(v) else 0
        print(f" - [{k.upper()}]: {v} ({size_kb:.1f} KB)")

    print("================================================================================")

    if args.open_folder:
        subprocess.run(["explorer", EXPORTS_DIR])

if __name__ == "__main__":
    main()

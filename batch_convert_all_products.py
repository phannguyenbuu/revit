#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
batch_convert_all_products.py
Duyệt sâu từng thư mục trong D:\\Dropbox\\_Documents\\Toolx\\output\\san_pham_anh_trang_ruby
Chuyển từng file .rb thành file .obj đặt cùng tên thư mục mẹ.
"""

import os
import sys
import time
from pathlib import Path

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

import sketchup_ruby_engine

ROOT_DIR = r"D:\Dropbox\_Documents\Toolx\output\san_pham_anh_trang_ruby"

def main():
    start_total_time = time.time()
    print("=" * 80)
    print("🚀 BẮT ĐẦU QUY TRÌNH CHUYỂN ĐỔI HÀNG LOẠT: SKETCHUP RUBY (.RB) -> 3D OBJ")
    print(f"📁 Thư mục gốc: {ROOT_DIR}")
    print("=" * 80)

    # 1. Tìm tất cả các file .rb
    tasks = []
    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        for f in filenames:
            if f.lower().endswith('.rb'):
                full_rb = os.path.join(dirpath, f)
                parent_folder_name = os.path.basename(dirpath)
                tasks.append({
                    "rb_path": full_rb,
                    "dirpath": dirpath,
                    "folder_name": parent_folder_name,
                    "file_name": f
                })

    # Sắp xếp theo tên thư mục (001, 002, ...)
    tasks.sort(key=lambda x: x["folder_name"])
    total_count = len(tasks)
    print(f"🔍 Đã phát hiện tổng cộng {total_count} thư mục chứa file .rb cần xử lý.\n")

    success_list = []
    failed_list = []

    # 2. Xử lý từng thư mục
    for idx, item in enumerate(tasks, 1):
        rb_path = item["rb_path"]
        dirpath = item["dirpath"]
        folder_name = item["folder_name"]
        
        t0 = time.time()
        print(f"[{idx:02d}/{total_count:02d}] Đang xử lý: {folder_name} ...", end=" ", flush=True)

        try:
            with open(rb_path, "r", encoding="utf-8", errors="ignore") as fp:
                rb_code = fp.read()

            # Thực thi mã Ruby và tạo đối tượng 3D
            model = sketchup_ruby_engine.execute_ruby_script(rb_code)

            # Xuất sang file .obj và .mtl đặt cùng tên thư mục mẹ
            stats = sketchup_ruby_engine.export_model_to_obj(model, dirpath, base_name=folder_name)
            
            elapsed = round(time.time() - t0, 2)
            print(f"✅ OK ({elapsed}s | {stats['vertices']} đỉnh, {stats['faces']} mặt | {stats['file_size_kb']} KB)")
            
            success_list.append({
                "folder": folder_name,
                "obj_file": stats["obj_filename"],
                "obj_path": stats["obj_path"],
                "vertices": stats["vertices"],
                "faces": stats["faces"],
                "size_kb": stats["file_size_kb"],
                "time_s": elapsed
            })

        except Exception as ex:
            elapsed = round(time.time() - t0, 2)
            err_msg = str(ex).replace("\n", " ")
            if len(err_msg) > 120:
                err_msg = err_msg[:120] + "..."
            print(f"❌ LỖI ({elapsed}s): {err_msg}")
            
            failed_list.append({
                "folder": folder_name,
                "rb_path": rb_path,
                "error": str(ex)
            })

    total_elapsed = round(time.time() - start_total_time, 2)
    print("\n" + "=" * 80)
    print(f"🎉 TỔNG KẾT HOÀN TẤT TRONG {total_elapsed} GIÂY")
    print(f" - Tổng số file xử lý: {total_count}")
    print(f" - Chuyển đổi thành công: {len(success_list)} / {total_count} ({len(success_list)/total_count*100:.1f}%)")
    print(f" - Thất bại: {len(failed_list)} / {total_count}")
    print("=" * 80)

    if failed_list:
        print("\n⚠️ DANH SÁCH CÁC MỤC GẶP LỖI CẦN KIỂM TRA:")
        for idx, f in enumerate(failed_list, 1):
            print(f" {idx}. [{f['folder']}]: {f['error']}")

    return success_list, failed_list

if __name__ == "__main__":
    main()

import os
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import sketchup_ruby_engine

root = r"D:\Dropbox\_Documents\Toolx\output\san_pham_anh_trang_ruby"

# Get all folders containing model.rb or any .rb
rb_tasks = []
for dirpath, dirnames, filenames in os.walk(root):
    for f in filenames:
        if f.lower().endswith('.rb'):
            rb_tasks.append((os.path.join(dirpath, f), dirpath, os.path.basename(dirpath), f))

print(f"Total tasks: {len(rb_tasks)}")

# Test first 5
success = 0
failed = 0

for i, (full_path, dirpath, folder_name, fn) in enumerate(rb_tasks[:5], 1):
    print(f"\n--- [{i}/{len(rb_tasks)}] Processing: {folder_name} ---")
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
            rb_code = fp.read()
        
        model = sketchup_ruby_engine.execute_ruby_script(rb_code)
        stats = sketchup_ruby_engine.export_model_to_obj(model, dirpath, base_name=folder_name)
        print(f"✅ Thành công: {stats['obj_filename']} ({stats['vertices']} đỉnh, {stats['faces']} mặt, {stats['file_size_kb']} KB)")
        success += 1
    except Exception as ex:
        print(f"❌ Thất bại: {ex}")
        failed += 1

print(f"\nKết quả thử nghiệm 5 thư mục đầu: Thành công {success}, Thất bại {failed}")

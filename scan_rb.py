import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

root = r"D:\Dropbox\_Documents\Toolx\output\san_pham_anh_trang_ruby"
rb_files = []

for dirpath, dirnames, filenames in os.walk(root):
    for f in filenames:
        if f.lower().endswith('.rb'):
            full_path = os.path.join(dirpath, f)
            folder_name = os.path.basename(dirpath)
            rb_files.append((full_path, dirpath, folder_name, f))

print(f"Total .rb files found: {len(rb_files)}")
for i, (fp, dp, fn, fnm) in enumerate(rb_files[:10], 1):
    print(f"[{i}] Folder: {fn} | File: {fnm}")

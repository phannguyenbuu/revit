import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import sketchup_ruby_engine

rb_path = r"D:\Dropbox\_Documents\Toolx\output\san_pham_anh_trang_ruby\005_Biển số nhà nền alu chữ nổi đồng\model.rb"
with open(rb_path, "r", encoding="utf-8") as f:
    rb_code = f.read()

try:
    res = sketchup_ruby_engine.convert_rb_code_to_obj(rb_code, base_name="test_005")
    print("SUCCESS 005!")
    print("Result:", res)
except Exception as ex:
    print("FAILED 005:", repr(ex))
    import traceback
    traceback.print_exc()

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import sketchup_ruby_engine

p = r"D:\Dropbox\_Documents\Toolx\output\san_pham_anh_trang_ruby\014_Bảng hiệu bạt lót tôn 2 mặt có trụ 250 x 150\model.rb"
with open(p, 'r', encoding='utf-8') as f:
    code = f.read()

py = sketchup_ruby_engine.transpile_ruby_to_python(code)
for i, l in enumerate(py.split('\n')[:45], 1):
    print(f"{i:02d}: {l}")

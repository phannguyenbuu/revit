import sys

with open('web_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''          <div id="subpane-etabs-3d" class="etabs-subpane hidden space-y-3">



            <div class="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">



              <div class="flex items-center gap-3">



                <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5">



                  <i data-lucide="box" class="w-3.5 h-3.5 text-indigo-600"></i> Điều khiển 3D:



                </span>



                <span class="text-[11px] text-slate-500">Chuột trái: Xoay 360° • Lăn chuột: Phóng to/nhỏ • Chuột phải: Dời hình • Bấm vào dầm: Chọn cốt thép</span>



              </div>



            </div>'''

print("Target found with CRLF:", target.replace('\n', '\r\n') in content)
print("Target found as is:", target in content)

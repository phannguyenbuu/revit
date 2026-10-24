import sys, ctypes, time, os, json
sys.stdout.reconfigure(encoding='utf-8')

u32 = ctypes.windll.user32
hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
u32.SetThreadDesktop(hDesk)

import pythoncom, win32com.client
pythoncom.CoInitialize()

acad = win32com.client.GetActiveObject('AutoCAD.Application')
doc = None
for d in acad.Documents:
    if 'LONG TIÊN' in d.Name:
        doc = d
        break
if not doc:
    doc = acad.ActiveDocument

res_file = 'C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/acad_texts.json'
if os.path.exists(res_file):
    os.remove(res_file)

# Write lisp to search all text/mtext in window: X from -130000 to -95000, Y from -1403000 to -1397000
lsp_path = 'C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/get_texts.lsp'
with open(lsp_path, 'w', encoding='utf-8') as f:
    f.write('''
(defun c:DumpTexts ( / ss i ent el p txt lay res fp)
  (setq ss (ssget "C" '(-130000.0 -1403000.0) '(-95000.0 -1398000.0) '((0 . "*TEXT"))))
  (setq res "[]")
  (if ss
    (progn
      (setq res "[")
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq p (cdr (assoc 10 el)))
        (setq txt (cdr (assoc 1 el)))
        (setq lay (cdr (assoc 8 el)))
        (if (> i 0) (setq res (strcat res ",")))
        (setq res (strcat res (vl-prin1-to-string (list (car p) (cadr p) txt lay))))
        (setq i (1+ i))
      )
      (setq res (strcat res "]"))
    )
  )
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/acad_texts.json" "w"))
  (write-line res fp)
  (close fp)
  (princ "\\nDone dumping texts")
  (princ)
)
(c:DumpTexts)
''')

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/get_texts.lsp")\n')
time.sleep(1.5)

if os.path.exists(res_file):
    with open(res_file, 'r', encoding='latin1', errors='ignore') as f:
        content = f.read()
    print("Read content length:", len(content))
    # Parse lisp list format: [(-112000.0 -1400000.0 "S1" "LAYER")...]
    # Let's replace () with []
    import re
    items = re.findall(r'\(([-0-9\.]+)\s+([-0-9\.]+)\s+"([^"]*)"\s+"([^"]*)"\)', content)
    print(f"Found {len(items)} texts:")
    texts_found = []
    for x_str, y_str, txt, lay in items:
        x_cad = float(x_str)
        y_cad = float(y_str)
        rvt_x = round((x_cad + 132847.0) / 1000.0, 3)
        rvt_y = round((y_cad + 1400405.9) / 1000.0, 3)
        texts_found.append({"text": txt, "layer": lay, "x": rvt_x, "y": rvt_y})
    
    texts_found.sort(key=lambda t: t["x"])
    for t in texts_found:
        if -2.0 <= t["y"] <= 2.0:
            print(f"  X={t['x']:.2f}, Y={t['y']:.2f} | Layer: {t['layer']} | '{t['text']}'")
else:
    print("Output file not found!")

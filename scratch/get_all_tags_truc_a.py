import sys, ctypes, time, os, json, re
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

res_file = 'C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/acad_texts_all.json'
if os.path.exists(res_file):
    os.remove(res_file)

lsp_path = 'C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/get_all_texts.lsp'
with open(lsp_path, 'w', encoding='utf-8') as f:
    f.write('''
(defun c:DumpAllTexts ( / ss i ent el p txt lay res fp)
  (setq ss (ssget "X" '((0 . "*TEXT") (8 . "TBI,0,TEXT,KICH THUOC"))))
  (setq res "[")
  (if ss
    (progn
      (setq i 0)
      (while (< i (sslength ss))
        (setq ent (ssname ss i))
        (setq el (entget ent))
        (setq p (cdr (assoc 10 el)))
        (setq txt (cdr (assoc 1 el)))
        (setq lay (cdr (assoc 8 el)))
        (if (> (car p) -135000.0)
          (if (< (car p) -90000.0)
            (if (> (cadr p) -1402000.0)
              (if (< (cadr p) -1399000.0)
                (progn
                  (if (> (strlen res) 1) (setq res (strcat res ",")))
                  (setq res (strcat res (vl-prin1-to-string (list (rtos (car p) 2 2) (rtos (cadr p) 2 2) txt lay))))
                )
              )
            )
          )
        )
        (setq i (1+ i))
      )
    )
  )
  (setq res (strcat res "]"))
  (setq fp (open "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/acad_texts_all.json" "w"))
  (write-line res fp)
  (close fp)
  (princ "\\nDone dumping all texts")
  (princ)
)
(c:DumpAllTexts)
''')

doc.SendCommand('(load "C:/Users/nguyenbuu.DESKTOP-TOEFTR1/AppData/Local/Temp/get_all_texts.lsp")\n')
time.sleep(2.0)

if os.path.exists(res_file):
    with open(res_file, 'r', encoding='latin1', errors='ignore') as f:
        content = f.read()
    
    items = re.findall(r'\("([^"]+)"\s+"([^"]+)"\s+"([^"]*)"\s+"([^"]*)"\)', content)
    print(f"Found {len(items)} texts near building bottom:")
    tags = []
    for x_str, y_str, txt, lay in items:
        x_cad = float(x_str)
        y_cad = float(y_str)
        rvt_x = round((x_cad + 132847.0) / 1000.0, 3)
        rvt_y = round((y_cad + 1400405.9) / 1000.0, 3)
        tags.append({"text": txt, "layer": lay, "x": rvt_x, "y": rvt_y})
    
    tags.sort(key=lambda t: t["x"])
    for t in tags:
        if "S1" in t["text"] or "K1" in t["text"] or "S" in t["text"]:
            print(f"  TAG: '{t['text']}' at X={t['x']:.3f}, Y={t['y']:.3f} | Layer: {t['layer']}")
else:
    print("Output file not found!")

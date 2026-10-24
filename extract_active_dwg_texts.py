import subprocess
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

scr = r'D:\Dropbox\_Documents\RevitAI\extract_long_tien_texts.scr'
out_txt = r'D:\Dropbox\_Documents\RevitAI\extracted_long_tien_texts.txt'
out_txt_fwd = out_txt.replace('\\', '/')

lisp = f"""(setq f (open "{out_txt_fwd}" "w"))
(setq ss (ssget "X" '((0 . "TEXT,MTEXT"))))
(if ss
  (repeat (setq i (sslength ss))
    (setq ent (entget (ssname ss (setq i (1- i)))))
    (setq str (cdr (assoc 1 ent)))
    (setq pt (cdr (assoc 10 ent)))
    (setq lay (cdr (assoc 8 ent)))
    (setq h (cdr (assoc 40 ent)))
    (if (and str pt)
      (write-line (strcat lay "\t" (rtos (car pt) 2 1) "\t" (rtos (cadr pt) 2 1) "\t" (rtos h 2 1) "\t" str) f)
    )
  )
)
(close f)
_QUIT
"""

with open(scr, 'w', encoding='utf-8') as sf:
    sf.write(lisp)

acad = r'C:\Program Files\Autodesk\AutoCAD 2022\accoreconsole.exe'
dwg = r'C:\Users\nguyenbuu.DESKTOP-TOEFTR1\Downloads\Mẫu 40 CBS LONG TIÊN.dwg'

print("Running accoreconsole...")
proc = subprocess.run([acad, '/i', dwg, '/s', scr], stdout=subprocess.PIPE, text=True, errors='ignore', timeout=60)
print("Done. Return code:", proc.returncode)

if os.path.exists(out_txt):
    with open(out_txt, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [l.strip() for l in f if l.strip()]
    print("Total texts extracted:", len(lines))
    for l in lines[:20]:
        print("  ", l)
else:
    print("out_txt not found")

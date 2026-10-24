import subprocess
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

scr = r'D:\Dropbox\_Documents\RevitAI\extract_blocks.scr'
out_txt = r'D:\Dropbox\_Documents\RevitAI\extracted_blocks.txt'
out_txt_fwd = out_txt.replace('\\', '/')

lisp = f"""(setq f (open "{out_txt_fwd}" "w"))
(setq ss (ssget "X" '((0 . "INSERT"))))
(if ss
  (repeat (setq i (sslength ss))
    (setq blk (ssname ss (setq i (1- i))))
    (setq ent (entget blk))
    (setq bname (cdr (assoc 2 ent)))
    (setq pt (cdr (assoc 10 ent)))
    (setq lay (cdr (assoc 8 ent)))
    (if (and pt (< (car pt) 95000) (> (car pt) 50000) (< (cadr pt) -1375000) (> (cadr pt) -1415000))
      (progn
        (write-line (strcat bname "\t" lay "\t" (rtos (car pt) 2 1) "\t" (rtos (cadr pt) 2 1)) f)
        (setq att (entnext blk))
        (while (and att (/= (cdr (assoc 0 (entget att))) "SEQEND"))
          (if (= (cdr (assoc 0 (entget att))) "ATTRIB")
            (write-line (strcat "  ATTR:\t" (cdr (assoc 2 (entget att))) "\t" (cdr (assoc 1 (entget att)))) f)
          )
          (setq att (entnext att))
        )
      )
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

print("Running accoreconsole to extract blocks...")
proc = subprocess.run([acad, '/i', dwg, '/s', scr], stdout=subprocess.PIPE, text=True, errors='ignore', timeout=60)

if os.path.exists(out_txt):
    with open(out_txt, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    print("Block extraction result:")
    print(content[:3000])
else:
    print("out_txt not found")

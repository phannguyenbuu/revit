import sys
import os
import time

sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

inspect_lsp = """(progn
  (setq ss (ssget "X" '((0 . "LINE") (-3 ("REVITAI_LEADER")))))
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_inspect_leaders.txt" "w"))
  (write-line (strcat "TOTAL_LEADERS=" (itoa (if ss (sslength ss) 0))) f)
  (if ss
    (repeat (min 5 (sslength ss))
      (setq ent (ssname ss (setq i (if i (1- i) (1- (min 5 (sslength ss)))))))
      (setq ed (entget ent))
      (setq p1 (cdr (assoc 10 ed)) p2 (cdr (assoc 11 ed)))
      (write-line (strcat "Start=(" (rtos (car p1) 2 1) ", " (rtos (cadr p1) 2 1) ") -> End=(" (rtos (car p2) 2 1) ", " (rtos (cadr p2) 2 1) ")") f)
    )
  )
  (close f)
  (princ)
)
"""

with open(r"d:\Dropbox\_Documents\RevitAI\scratch\inspect.lsp", "w", encoding="utf-8") as f:
    f.write(inspect_lsp)

send_to_acad.send_acad_command('(load "d:/Dropbox/_Documents/RevitAI/scratch/inspect.lsp")\n')
time.sleep(1.0)

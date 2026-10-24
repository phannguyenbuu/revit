import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

inspect_lsp = """(defun c:InspectRevLeaders ( / ss i ent ed p1 p2 f count )
  (regapp "REVITAI_LEADER")
  (setq ss (ssget "X" '((0 . "LINE") (-3 ("REVITAI_LEADER")))))
  (setq count (if ss (sslength ss) 0))
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_inspect_clean.txt" "w"))
  (write-line (strcat "COUNT=" (itoa count)) f)
  (if ss
    (progn
      (setq i 0)
      (while (and (< i 10) (< i count))
        (setq ent (ssname ss i))
        (setq ed (entget ent))
        (setq p1 (cdr (assoc 10 ed))
              p2 (cdr (assoc 11 ed)))
        (write-line (strcat "Leader #" (itoa (1+ i))
                            ": Start=(" (rtos (car p1) 2 1) "," (rtos (cadr p1) 2 1) ")"
                            " -> End=(" (rtos (car p2) 2 1) "," (rtos (cadr p2) 2 1) ")"
                            " | dY=" (rtos (- (cadr p1) (cadr p2)) 2 1)) f)
        (setq i (1+ i))
      )
    )
  )
  (close f)
  (princ)
)
(c:InspectRevLeaders)
"""

with open(r"d:\Dropbox\_Documents\RevitAI\scratch\clean_inspect.lsp", "w", encoding="utf-8") as f:
    f.write(inspect_lsp)

send_to_acad.send_acad_command('(load "d:/Dropbox/_Documents/RevitAI/scratch/clean_inspect.lsp")\n')
time.sleep(1.0)

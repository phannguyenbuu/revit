import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp = """(progn
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_cntr.txt" "w"))
  (setq ss (ssget "X" '((8 . "P-PIPE-CNTR"))))
  (write-line (strcat "ALL_ENTITIES_ON_P-PIPE-CNTR: " (itoa (if ss (sslength ss) 0))) f)
  (if ss
    (repeat (sslength ss)
      (setq ent (ssname ss (setq i (if i (1- i) (1- (sslength ss))))))
      (write-line (cdr (assoc 0 (entget ent))) f)
    )
  )
  (close f)
)
"""

send_to_acad.send_acad_command(lisp)

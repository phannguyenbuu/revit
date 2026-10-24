import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp = """(progn
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_layer_lines.txt" "w"))
  (setq lay (tblnext "LAYER" T))
  (while lay
    (setq lname (cdr (assoc 2 lay)))
    (setq ss (ssget "X" (list '(0 . "LINE") (cons 8 lname))))
    (if (and ss (> (sslength ss) 0))
      (write-line (strcat lname ": " (itoa (sslength ss))) f)
    )
    (setq lay (tblnext "LAYER"))
  )
  (close f)
)
"""

send_to_acad.send_acad_command(lisp)

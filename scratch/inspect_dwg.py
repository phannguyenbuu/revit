import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp = """(progn
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_entities.txt" "w"))
  
  ;; Dem LINE
  (setq ss1 (ssget "X" '((0 . "LINE"))))
  (write-line (strcat "TOTAL_LINES: " (itoa (if ss1 (sslength ss1) 0))) f)

  ;; Dem LWPOLYLINE
  (setq ss2 (ssget "X" '((0 . "LWPOLYLINE"))))
  (write-line (strcat "TOTAL_LWPOLYLINES: " (itoa (if ss2 (sslength ss2) 0))) f)

  ;; Dem TEXT/MTEXT
  (setq ss3 (ssget "X" '((0 . "TEXT,MTEXT"))))
  (write-line (strcat "TOTAL_TEXTS: " (itoa (if ss3 (sslength ss3) 0))) f)

  ;; Dem layers
  (setq lay (tblnext "LAYER" T))
  (write-line "--- LAYERS ---" f)
  (while lay
    (write-line (cdr (assoc 2 lay)) f)
    (setq lay (tblnext "LAYER"))
  )
  (close f)
)
"""

send_to_acad.send_acad_command(lisp)

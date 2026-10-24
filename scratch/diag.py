import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp = """(defun c:DiagLeaders ( / f ssP ssT i ent ed txt txtPt x0 y0 tagLeft bestDist p1 p2 )
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_diag.txt" "w"))
  
  (setq ssT (ssget "X" '((0 . "TEXT,MTEXT"))))
  (write-line (strcat "TOTAL_TEXTS: " (itoa (if ssT (sslength ssT) 0))) f)
  
  (setq ssP (ssget "X" '((0 . "LINE") (8 . "P-PIPE"))))
  (write-line (strcat "TOTAL_P-PIPE: " (itoa (if ssP (sslength ssP) 0))) f)

  ;; Thu lay 5 text BOP +... va tinh khoang cach den LINE P-PIPE gan nhat
  (setq count 0 i 0)
  (while (and ssT (< i (sslength ssT)) (< count 5))
    (setq ent (ssname ssT i))
    (setq ed (entget ent))
    (setq txt (cdr (assoc 1 ed)))
    (if (and txt (wcmatch txt "*BOP*+*"))
      (progn
        (setq txtPt (cdr (assoc 10 ed)))
        (write-line (strcat "TEXT: '" txt "' at (" (rtos (car txtPt) 2 1) "," (rtos (cadr txtPt) 2 1) ")") f)
        
        ;; Tim line P-PIPE gan nhat
        (setq bestDist 1e12 j 0)
        (while (and ssP (< j (sslength ssP)))
          (setq pent (ssname ssP j))
          (setq ped (entget pent))
          (setq p1 (cdr (assoc 10 ped))
                p2 (cdr (assoc 11 ped)))
          ;; Distance from txtPt to segment
          (setq d (distance txtPt p1))
          (if (< d bestDist) (setq bestDist d))
          (setq j (1+ j))
        )
        (write-line (strcat "   MIN_DIST_TO_P-PIPE_VERTEX: " (rtos bestDist 2 1)) f)
        (setq count (1+ count))
      )
    )
    (setq i (1+ i))
  )
  (close f)
)
(c:DiagLeaders)
"""

send_to_acad.send_acad_command(lisp)

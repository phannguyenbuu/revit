(vl-load-com)
(setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/s4_details.txt" "w"))
(setq p1 '(-45000.0 -1532000.0))
(setq p2 '(-25000.0 -1522000.0))
(vla-ZoomWindow (vlax-get-acad-object) (vlax-3d-point p1) (vlax-3d-point p2))
(setq ss (ssget "C" p1 p2 '((0 . "*TEXT,DIMENSION"))))







(if ss
  (progn
    (setq i 0)
    (while (< i (sslength ss))
      (setq e (ssname ss i))
      (setq ed (entget e))
      (setq typ (cdr (assoc 0 ed)))
      (if (wcmatch typ "*TEXT")
        (progn
          (setq p (cdr (assoc 10 ed)))
          (write-line (strcat typ "|" (cdr (assoc 1 ed)) "|" (rtos (car p) 2 0) "," (rtos (cadr p) 2 0)) f)
        )
      )
      (if (wcmatch typ "DIMENSION")
        (progn
          (setq p (cdr (assoc 10 ed)))
          (write-line (strcat "DIM|" (rtos (cdr (assoc 42 ed)) 2 0) "|" (rtos (car p) 2 0) "," (rtos (cadr p) 2 0)) f)
        )
      )
      (setq i (1+ i))
    )
  )
)

(close f)
(princ)

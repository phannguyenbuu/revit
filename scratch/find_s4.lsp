
(vl-load-com)
(setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/s4_texts.txt" "w"))
(setq ss (ssget "X" '((0 . "*TEXT") (1 . "*S4*,*s4*"))))
(if ss
  (progn
    (setq i 0)
    (while (< i (sslength ss))
      (setq e (ssname ss i))
      (setq ed (entget e))
      (setq txt (cdr (assoc 1 ed)))
      (setq ins (cdr (assoc 10 ed)))
      (write-line (strcat txt "|" (rtos (car ins) 2 2) "," (rtos (cadr ins) 2 2)) f)
      (setq i (1+ i))
    )
  )
)
(close f)
(princ)

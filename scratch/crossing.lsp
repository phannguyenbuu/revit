
(vl-load-com)
(setq pt1 (list -101347.0 -1401205.9))
(setq pt2 (list -94847.0 -1399605.9))
(setq ss (ssget "_C" pt1 pt2))
(setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/k1_crossing_dump.txt" "w"))
(if ss
  (progn
    (write-line (strcat "COUNT=" (itoa (sslength ss))) f)
    (setq i 0)
    (while (< i (sslength ss))
      (setq e (ssname ss i))
      (setq ed (entget e))
      (setq obj (vlax-ename->vla-object e))
      (vla-getboundingbox obj 'minp 'maxp)
      (setq pmin (vlax-safearray->list minp))
      (setq pmax (vlax-safearray->list maxp))
      (write-line (strcat (cdr (assoc 5 ed)) "|" (cdr (assoc 0 ed)) "|" (cdr (assoc 8 ed)) "|" 
                          (rtos (car pmin) 2 3) "," (rtos (cadr pmin) 2 3) "|"
                          (rtos (car pmax) 2 3) "," (rtos (cadr pmax) 2 3)) f)
      (setq i (1+ i))
    )
  )
  (write-line "COUNT=0" f)
)
(close f)
(princ)

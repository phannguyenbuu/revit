(setq f (open "D:/Dropbox/_Documents/RevitAI/scratch/zone_texts_dump.txt" "w"))

(write-line "=== North Chase 8.3 ===" f)
(setq ss (ssget "C" '(-125347.0 -1387405.9) '(-123847.0 -1385905.9) '((0 . "*TEXT"))))
(if ss
  (repeat (setq i (sslength ss))
    (setq e (ssname ss (setq i (1- i))))
    (setq ed (entget e))
    (setq p (cdr (assoc 10 ed)))
    (setq rx (/ (+ (car p) 132847.0) 1000.0))
    (setq ry (/ (+ (cadr p) 1400405.9) 1000.0))
    (write-line (strcat (cdr (assoc 1 ed)) " | (" (rtos rx 2 2) ", " (rtos ry 2 2) ")") f)
  )
)


(write-line "=== North Chase 29.4 ===" f)
(setq ss (ssget "C" '(-104347.0 -1387405.9) '(-102847.0 -1385905.9) '((0 . "*TEXT"))))
(if ss
  (repeat (setq i (sslength ss))
    (setq e (ssname ss (setq i (1- i))))
    (setq ed (entget e))
    (setq p (cdr (assoc 10 ed)))
    (setq rx (/ (+ (car p) 132847.0) 1000.0))
    (setq ry (/ (+ (cadr p) 1400405.9) 1000.0))
    (write-line (strcat (cdr (assoc 1 ed)) " | (" (rtos rx 2 2) ", " (rtos ry 2 2) ")") f)
  )
)


(write-line "=== NW Corner 1-C ===" f)
(setq ss (ssget "C" '(-133347.0 -1388405.9) '(-128847.0 -1385905.9) '((0 . "*TEXT"))))
(if ss
  (repeat (setq i (sslength ss))
    (setq e (ssname ss (setq i (1- i))))
    (setq ed (entget e))
    (setq p (cdr (assoc 10 ed)))
    (setq rx (/ (+ (car p) 132847.0) 1000.0))
    (setq ry (/ (+ (cadr p) 1400405.9) 1000.0))
    (write-line (strcat (cdr (assoc 1 ed)) " | (" (rtos rx 2 2) ", " (rtos ry 2 2) ")") f)
  )
)


(write-line "=== West Wall Top ===" f)
(setq ss (ssget "C" '(-133347.0 -1390905.9) '(-131347.0 -1387905.9) '((0 . "*TEXT"))))
(if ss
  (repeat (setq i (sslength ss))
    (setq e (ssname ss (setq i (1- i))))
    (setq ed (entget e))
    (setq p (cdr (assoc 10 ed)))
    (setq rx (/ (+ (car p) 132847.0) 1000.0))
    (setq ry (/ (+ (cadr p) 1400405.9) 1000.0))
    (write-line (strcat (cdr (assoc 1 ed)) " | (" (rtos rx 2 2) ", " (rtos ry 2 2) ")") f)
  )
)


(write-line "=== West Wall Bottom ===" f)
(setq ss (ssget "C" '(-133347.0 -1399405.9) '(-131347.0 -1396405.9) '((0 . "*TEXT"))))
(if ss
  (repeat (setq i (sslength ss))
    (setq e (ssname ss (setq i (1- i))))
    (setq ed (entget e))
    (setq p (cdr (assoc 10 ed)))
    (setq rx (/ (+ (car p) 132847.0) 1000.0))
    (setq ry (/ (+ (cadr p) 1400405.9) 1000.0))
    (write-line (strcat (cdr (assoc 1 ed)) " | (" (rtos rx 2 2) ", " (rtos ry 2 2) ")") f)
  )
)


(write-line "=== SW Corner 1-A ===" f)
(setq ss (ssget "C" '(-133347.0 -1401405.9) '(-126847.0 -1398905.9) '((0 . "*TEXT"))))
(if ss
  (repeat (setq i (sslength ss))
    (setq e (ssname ss (setq i (1- i))))
    (setq ed (entget e))
    (setq p (cdr (assoc 10 ed)))
    (setq rx (/ (+ (car p) 132847.0) 1000.0))
    (setq ry (/ (+ (cadr p) 1400405.9) 1000.0))
    (write-line (strcat (cdr (assoc 1 ed)) " | (" (rtos rx 2 2) ", " (rtos ry 2 2) ")") f)
  )
)

(close f)
(princ)
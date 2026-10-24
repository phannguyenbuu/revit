import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp_cmd = """(progn
  (setq f (open "D:/Dropbox/_Documents/RevitAI/acad_debug.txt" "w"))
  (setq ssText (ssget "X" '((0 . "TEXT,MTEXT"))))
  (setq found 0 i 0)
  (while (and ssText (< i (sslength ssText)) (< found 3))
    (setq ent (ssname ssText i))
    (setq ed (entget ent))
    (setq txt (cdr (assoc 1 ed)))
    (if (and txt (wcmatch txt "*+*") (not (wcmatch txt "*U+2022*")))
      (progn
        (setq pt (cdr (assoc 10 ed)))
        (write-line (strcat "TEXT: '" txt "' at " (rtos (car pt) 2 1) ", " (rtos (cadr pt) 2 1)) f)
        ;; Tim cac line P-PIPE-CNTR trong ban kinh 3000
        (setq ssP (ssget "X" '((0 . "LINE") (8 . "P-PIPE-CNTR"))))
        (setq j 0 pfound 0)
        (while (and ssP (< j (sslength ssP)) (< pfound 2))
          (setq pent (ssname ssP j))
          (setq ped (entget pent))
          (setq p1 (cdr (assoc 10 ped))
                p2 (cdr (assoc 11 ped)))
          (setq d (distance pt p1))
          (if (< d 2000.0)
            (progn
              (write-line (strcat "   PIPE LINE: (" (rtos (car p1) 2 1) "," (rtos (cadr p1) 2 1) ") to (" (rtos (car p2) 2 1) "," (rtos (cadr p2) 2 1) ")") f)
              (setq pfound (1+ pfound))
            )
          )
          (setq j (1+ j))
        )
        (setq found (1+ found))
      )
    )
    (setq i (1+ i))
  )
  (close f)
)
"""

ok, msg = send_to_acad.send_acad_command(lisp_cmd)
print("Sent:", ok, msg)

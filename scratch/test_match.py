import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp = """(defun c:TestPipesAndTexts ( / f ssP ssT count ent ed txt )
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_test_match.txt" "w"))
  (setq ssP (ssget "X" '((0 . "LINE") (8 . "P-PIPE*"))))
  (write-line (strcat "PIPES MATCHING P-PIPE*: " (itoa (if ssP (sslength ssP) 0))) f)
  
  (setq ssT (ssget "X" '((0 . "TEXT,MTEXT"))))
  (setq count 0)
  (if ssT
    (repeat (sslength ssT)
      (setq ent (ssname ssT (setq count (1+ count))))
      (if ent
        (progn
          (setq ed (entget ent))
          (setq txt (cdr (assoc 1 ed)))
          (if (and txt (wcmatch txt "*+*") (not (wcmatch txt "*U+2022*")))
            (write-line (strcat "TEXT: " txt) f)
          )
        )
      )
    )
  )
  (close f)
)
(c:TestPipesAndTexts)
"""

send_to_acad.send_acad_command(lisp)

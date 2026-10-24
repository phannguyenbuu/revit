import send_to_acad

lisp_cmd = """(progn
  (setq f (open "D:/Dropbox/_Documents/RevitAI/acad_debug.txt" "w"))
  
  ;; Collect all text Y baselines
  (setq ssText (ssget "X" '((0 . "TEXT,MTEXT") (8 . "G-ANNO-TEXT"))))
  (setq yList nil)
  (if ssText
    (repeat (sslength ssText)
      (setq ed (entget (ssname ssText (setq i (if i (1- i) (1- (sslength ssText)))))))
      (setq p (cdr (assoc 10 ed)))
      (setq yList (cons (cadr p) yList))
    )
  )

  ;; Check lines on P-PIPE-CNTR whose p1 or p2 has Y matching a text baseline within 1.0mm
  (setq ssLines (ssget "X" '((0 . "LINE") (8 . "P-PIPE-CNTR"))))
  (setq matchCount 0)
  (if ssLines
    (repeat (sslength ssLines)
      (setq ent (ssname ssLines (setq j (if j (1- j) (1- (sslength ssLines))))))
      (setq ed (entget ent))
      (setq p1 (cdr (assoc 10 ed)))
      (setq p2 (cdr (assoc 11 ed)))
      ;; Check if p1 Y matches any text baseline
      (setq isMatch nil)
      (foreach ty yList
        (if (or (< (abs (- (cadr p1) ty)) 1.0) (< (abs (- (cadr p2) ty)) 1.0))
          (setq isMatch T)
        )
      )
      (if isMatch (setq matchCount (1+ matchCount)))
    )
  )
  (write-line (strcat "MATCHING_LEADERS_TO_REMOVE: " (itoa matchCount)) f)
  (close f)
)
"""

send_to_acad.send_acad_command(lisp_cmd)

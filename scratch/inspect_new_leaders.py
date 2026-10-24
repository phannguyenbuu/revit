import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp = """(defun c:InspectCreatedLeaders ( / f ss i ent ed p1 p2 )
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_inspect_leaders.txt" "w"))
  (setq ss (ssget "X" '((0 . "LINE") (-3 ("REVITAI_LEADER")))))
  (setq count (if ss (sslength ss) 0))
  (write-line (strcat "TOTAL: " (itoa count)) f)
  (if ss
    (repeat (min 10 count)
      (setq ent (ssname ss (setq i (if i (1- i) (1- count)))))
      (setq ed (entget ent))
      (setq p1 (cdr (assoc 10 ed))
            p2 (cdr (assoc 11 ed)))
      (write-line (strcat "LEADER: Start=(" (rtos (car p1) 2 1) ", " (rtos (cadr p1) 2 1) ") -> End=(" (rtos (car p2) 2 1) ", " (rtos (cadr p2) 2 1) ") | dY=" (rtos (- (cadr p2) (cadr p1)) 2 1)) f)
    )
  )
  (close f)
)
(c:InspectCreatedLeaders)
"""

send_to_acad.send_acad_command(lisp)

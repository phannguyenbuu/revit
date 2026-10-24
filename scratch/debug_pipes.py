import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp = """(defun c:DebugFindPipes ( / f ssP pipeList ssT textList i ent ed p1 p2 x1 x2 y1 y2 txtStr txtPt x0 y0 tagLeft bestDist bestPt count )
  (defun ClosestPointOnSegment (p a b / vx vy l2 tval)
    (setq vx (- (car b) (car a))
          vy (- (cadr b) (cadr a))
          l2 (+ (* vx vx) (* vy vy)))
    (if (<= l2 1e-6) a
      (progn
        (setq tval (/ (+ (* (- (car p) (car a)) vx) (* (- (cadr p) (cadr a)) vy)) l2))
        (if (< tval 0.0) (setq tval 0.0) (if (> tval 1.0) (setq tval 1.0)))
        (list (+ (car a) (* tval vx)) (+ (cadr a) (* tval vy)) 0.0)
      )
    )
  )

  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_debug_pipes.txt" "w"))
  
  (setq ssP (ssget "X" '((0 . "LINE") (8 . "P-PIPE,P-PIPE-CNTR"))))
  (setq pipeList nil)
  (if ssP
    (repeat (sslength ssP)
      (setq ent (ssname ssP (setq i (if i (1- i) (1- (sslength ssP))))))
      (setq ed (entget ent))
      (setq p1 (cdr (assoc 10 ed)) p2 (cdr (assoc 11 ed)))
      (setq pipeList (cons (list p1 p2 (min (car p1) (car p2)) (min (cadr p1) (cadr p2)) (max (car p1) (car p2)) (max (cadr p1) (cadr p2))) pipeList))
    )
  )
  (setq i nil)
  (write-line (strcat "PIPES COUNT: " (itoa (length pipeList))) f)

  (setq ssT (ssget "X" '((0 . "TEXT,MTEXT"))))
  (setq count 0 successCount 0 i 0)
  (while (and ssT (< i (sslength ssT)) (< count 20))
    (setq ent (ssname ssT i))
    (setq ed (entget ent))
    (setq txt (cdr (assoc 1 ed)))
    (if (and txt (wcmatch txt "*+*") (not (wcmatch txt "*U+2022*")))
      (progn
        (setq pt (cdr (assoc 10 ed)))
        (setq bestDist 1e12 bestPt nil)
        (foreach p pipeList
          (setq testPt (ClosestPointOnSegment pt (car p) (cadr p)))
          (setq d (distance pt testPt))
          (if (< d bestDist) (setq bestDist d bestPt testPt))
        )
        (write-line (strcat "TEXT: '" txt "' @ (" (rtos (car pt) 2 0) "," (rtos (cadr pt) 2 0) ") -> BestDist=" (rtos bestDist 2 1)) f)
        (if (<= bestDist 5000.0) (setq successCount (1+ successCount)))
        (setq count (1+ count))
      )
    )
    (setq i (1+ i))
  )
  (write-line (strcat "SUCCESS IN FIRST 20: " (itoa successCount)) f)
  (close f)
)
(c:DebugFindPipes)
"""

send_to_acad.send_acad_command(lisp)

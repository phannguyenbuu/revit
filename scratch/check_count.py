import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp = '(progn (setq ss (ssget "X" (list (cons 0 "LINE") (cons 8 "P-PIPE-CNTR")))) (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_line_count.txt" "w")) (write-line (itoa (if ss (sslength ss) 0)) f) (close f))\n'
ok, msg = send_to_acad.send_acad_command(lisp)
print("Send result:", ok, msg)

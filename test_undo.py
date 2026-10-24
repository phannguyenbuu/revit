import send_to_acad
import time

cmd = '(progn (command "_.UNDO" "1") (setq ss (ssget "X" \'((0 . "LINE") (8 . "P-PIPE-CNTR")))) (setq f (open "D:/Dropbox/_Documents/RevitAI/acad_debug.txt" "w")) (write-line (strcat "COUNT_AFTER_UNDO: " (itoa (if ss (sslength ss) 0))) f) (close f))\n'

send_to_acad.send_acad_command("\x1b\x1b\n")
time.sleep(0.2)
ok, msg = send_to_acad.send_acad_command(cmd)
print("Undo sent:", ok, msg)

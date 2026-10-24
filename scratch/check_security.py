import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

# 1. Reset
send_to_acad.send_acad_command('")" ) ) ) ) (princ "\\nRESET\\n")\n')
time.sleep(0.2)

# 2. Check SECURELOAD
cmd = '(progn (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_security.txt" "w")) (write-line (strcat "SECURELOAD=" (itoa (getvar "SECURELOAD"))) f) (write-line (strcat "TRUSTED=" (getvar "TRUSTEDPATHS")) f) (close f))\n'
send_to_acad.send_acad_command(cmd)
time.sleep(0.5)

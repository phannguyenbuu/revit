import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

# Break out of any open paren
send_to_acad.send_acad_command('")" ) ) ) ) (princ "\\nRESET_OK\\n")\n')
time.sleep(0.2)

# Check prompt
send_to_acad.send_acad_command('(progn (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_lastprompt.txt" "w")) (write-line (getvar "LASTPROMPT") f) (close f))\n')

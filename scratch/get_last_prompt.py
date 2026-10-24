import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

# Write LASTPROMPT to a file
cmd = '(progn (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_lastprompt.txt" "w")) (write-line (getvar "LASTPROMPT") f) (close f))\n'
send_to_acad.send_acad_command(cmd, skip_esc=True)
time.sleep(0.5)

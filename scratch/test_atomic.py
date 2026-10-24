import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

# 1. Clear any stuck prompt
send_to_acad.send_acad_command('")" ) ) ) ) (princ "\\nPROMPT_CLEARED\\n")\n')
time.sleep(0.3)

# 2. Single atomic progn command: load and run!
cmd = '(progn (load "d:/Dropbox/_Documents/RevitAI/mep_cleaner_and_leader.lsp") (setq res (RunMepLeaderEx "P-PIPE*" "+" 5000.0 250.0)) (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_atomic_res.txt" "w")) (write-line (strcat "RESULT=" (itoa res)) f) (close f))\n'

ok, msg = send_to_acad.send_acad_command(cmd, timeout_ms=30000)
print("Command sent:", ok, msg)

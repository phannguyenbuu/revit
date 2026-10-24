import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

# 1. Reset
send_to_acad.send_acad_command('")" ) ) ) ) (princ "\\nRESET\\n")\n')
time.sleep(0.2)

# 2. Load mep_cleaner_and_leader.lsp
cmd = '(progn (setq res (load "d:/Dropbox/_Documents/RevitAI/mep_cleaner_and_leader.lsp" "ERR")) (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_load_res.txt" "w")) (write-line (vl-prin1-to-string res) f) (close f))\n'
send_to_acad.send_acad_command(cmd)
time.sleep(0.5)

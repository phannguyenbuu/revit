import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

# 1. Reset
send_to_acad.send_acad_command('")" ) ) ) ) (princ "\\nRESET\\n")\n')
time.sleep(0.2)

# 2. Run leader directly
cmd = '(progn (setq cnt (RunMepLeader "P-PIPE*" "+" 5000.0)) (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_leader_run_res.txt" "w")) (write-line (strcat "COUNT=" (itoa (if cnt cnt -1))) f) (close f) (command "_.REGEN"))\n'
send_to_acad.send_acad_command(cmd)
time.sleep(1.0)

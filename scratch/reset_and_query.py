import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

# Clean command line
send_to_acad.send_acad_command('")" ) ) ) ) (princ "\\nRESET_OK\\n")\n', skip_esc=False)
time.sleep(0.3)

test_lsp = """(progn
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_aca_lastprompt.txt" "w"))
  (write-line (getvar "LASTPROMPT") f)
  (close f)
  (princ)
)
"""
with open(r"d:\Dropbox\_Documents\RevitAI\scratch\get_prompt.lsp", "w") as f:
    f.write(test_lsp)

send_to_acad.send_acad_command('(load "d:/Dropbox/_Documents/RevitAI/scratch/get_prompt.lsp")\n', skip_esc=True)
time.sleep(0.5)

import os
print("File exists:", os.path.exists(r"d:\Dropbox\_Documents\RevitAI\scratch_aca_lastprompt.txt"))
if os.path.exists(r"d:\Dropbox\_Documents\RevitAI\scratch_aca_lastprompt.txt"):
    with open(r"d:\Dropbox\_Documents\RevitAI\scratch_aca_lastprompt.txt") as f:
        print("Prompt:", f.read().strip())

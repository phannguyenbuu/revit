import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

send_to_acad.send_acad_command("\x1b\x1b\n", skip_esc=True)
time.sleep(0.2)

test_lsp = """(progn
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_aca_test.txt" "w"))
  (write-line (vl-prin1-to-string (arx "c")) f)
  (write-line (vl-prin1-to-string (arx "m")) f)
  (close f)
  (princ)
)
"""

send_to_acad.send_acad_command(test_lsp + "\n", skip_esc=True)
time.sleep(0.5)

with open(r"d:\Dropbox\_Documents\RevitAI\scratch_aca_test.txt", "r") as f:
    print(f.read())

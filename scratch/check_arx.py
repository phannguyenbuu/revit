import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

# Clean command line
send_to_acad.send_acad_command("\x1b\x1b\n", skip_esc=True)
time.sleep(0.2)

test_lsp = """(progn
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_aca_info.txt" "w"))
  ;; Check if arx apps are loaded
  (setq arxlist (arx))
  (write-line (strcat "TOTAL_ARX=" (itoa (length arxlist))) f)
  (foreach app arxlist
    (if (wcmatch (strcase app) "*AEC*")
      (write-line (strcat "AEC_ARX=" app) f)
    )
  )
  (close f)
  (princ)
)
"""

send_to_acad.send_acad_command(test_lsp + "\n", skip_esc=True)
time.sleep(0.5)

with open(r"d:\Dropbox\_Documents\RevitAI\scratch_aca_info.txt", "r") as f:
    print(f.read())

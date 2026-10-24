import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp = """(progn
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_lastprompt.txt" "w"))
  (write-line (getvar "LASTPROMPT") f)
  (close f)
)
"""

send_to_acad.send_acad_command(lisp)

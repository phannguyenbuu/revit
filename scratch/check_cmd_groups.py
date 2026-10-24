import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

# Clean command line
send_to_acad.send_acad_command("\x1b\x1b\n", skip_esc=True)
time.sleep(0.2)

test_lsp = """(progn
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_aca_cmds.txt" "w"))
  (setq cmdlist (atoms-family 1))
  ;; Check arx commands
  (foreach grp (acad_strlsort (arx "commands"))
    (if (or (wcmatch (strcase grp) "*AEC*")
            (wcmatch (strcase grp) "*WALL*")
            (wcmatch (strcase grp) "*ARCH*"))
      (write-line (strcat "GRP: " grp) f)
    )
  )
  (close f)
  (princ)
)
"""

send_to_acad.send_acad_command(test_lsp + "\n", skip_esc=True)
time.sleep(0.5)

with open(r"d:\Dropbox\_Documents\RevitAI\scratch_aca_cmds.txt", "r") as f:
    print(f.read())

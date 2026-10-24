import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

send_to_acad.send_acad_command("\x1b\x1b\n", skip_esc=True)
time.sleep(0.2)

test_lsp = """(progn
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_aca_cmds.txt" "w"))
  (setq grps (arx "commands"))
  (write-line (strcat "Total groups: " (itoa (length grps))) f)
  (foreach g grps
    (write-line (strcat "GRP=" g) f)
    (setq cmds (arx "commands" g))
    (foreach c cmds
      (if (or (wcmatch (strcase c) "*WALL*")
              (wcmatch (strcase c) "*DOOR*")
              (wcmatch (strcase c) "*WINDOW*")
              (wcmatch (strcase c) "*SLAB*")
              (wcmatch (strcase c) "*ROOF*"))
        (write-line (strcat "   CMD=" c) f)
      )
    )
  )
  (close f)
  (princ)
)
"""

send_to_acad.send_acad_command(test_lsp + "\n", skip_esc=True)
time.sleep(0.5)

with open(r"d:\Dropbox\_Documents\RevitAI\scratch_aca_cmds.txt", "r") as f:
    print(f.read()[:2000])

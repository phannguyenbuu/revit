import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

err_lsp = """(progn
  (setq err (vl-catch-all-apply '(lambda () (load "d:/Dropbox/_Documents/RevitAI/test_run.lsp"))))
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_err.txt" "w"))
  (if (vl-catch-all-error-p err)
    (write-line (strcat "ERROR: " (vl-catch-all-error-message err)) f)
    (write-line "SUCCESS_LOAD" f)
  )
  (close f)
  (princ)
)
"""

with open(r"d:\Dropbox\_Documents\RevitAI\scratch\check_err.lsp", "w", encoding="utf-8") as f:
    f.write(err_lsp)

send_to_acad.send_acad_command('(load "d:/Dropbox/_Documents/RevitAI/scratch/check_err.lsp")\n')
time.sleep(1.5)

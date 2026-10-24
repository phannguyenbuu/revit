import sys
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

lisp = """(progn
  (load "d:/Dropbox/_Documents/RevitAI/mep_cleaner_and_leader.lsp")
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_run_eval.txt" "w"))
  (write-line "LOADED OK" f)
  (setq res (vl-catch-all-apply 'RunMepLeaderEx (list "P-PIPE*" "+" 5000.0 250.0)))
  (if (vl-catch-all-error-p res)
    (write-line (strcat "ERROR: " (vl-catch-all-error-message res)) f)
    (write-line (strcat "RETURNED: " (vl-princ-to-string res)) f)
  )
  (close f)
)
"""

send_to_acad.send_acad_command(lisp)

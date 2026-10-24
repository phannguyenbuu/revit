(progn
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_aca_lastprompt.txt" "w"))
  (write-line (getvar "LASTPROMPT") f)
  (close f)
  (princ)
)

import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

test_lisp = """(progn
  (regapp "REVITAI_LEADER")
  (setq res1 (entmake (list '(0 . "LINE")
                            '(8 . "P-PIPE")
                            '(10 0.0 0.0 0.0)
                            '(11 100.0 100.0 0.0)
                            (list -3 '("REVITAI_LEADER" (1000 . "PIPE_LEADER"))))))
  (setq res2 (entmake (list '(0 . "LINE")
                            '(8 . "P-PIPE")
                            '(10 100.0 100.0 0.0)
                            '(11 200.0 200.0 0.0))))
  (setq ss1 (ssget "X" '((0 . "LINE") (-3 ("REVITAI_LEADER")))))
  (setq f (open "d:/Dropbox/_Documents/RevitAI/scratch_entmake_test.txt" "w"))
  (write-line (strcat "res1=" (vl-prin1-to-string res1)) f)
  (write-line (strcat "res2=" (vl-prin1-to-string res2)) f)
  (write-line (strcat "ss1=" (vl-prin1-to-string ss1)) f)
  (close f)
  (princ)
)
"""

with open(r"d:\Dropbox\_Documents\RevitAI\scratch\test_entmake.lsp", "w", encoding="utf-8") as f:
    f.write(test_lisp)

send_to_acad.send_acad_command('(load "d:/Dropbox/_Documents/RevitAI/scratch/test_entmake.lsp")\n')
time.sleep(1.0)

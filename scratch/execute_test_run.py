import sys
import time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

send_to_acad.send_acad_command("\x1b\x1b\n")
time.sleep(0.2)
ok, msg = send_to_acad.send_acad_command('(load "d:/Dropbox/_Documents/RevitAI/test_run.lsp")\n', timeout_ms=30000)
print("Load result:", ok, msg)

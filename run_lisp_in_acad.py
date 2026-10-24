import sys
import os
import time

sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

def run_lisp(lsp_path, wait_s=1.0):
    lsp_forward = lsp_path.replace("\\", "/")
    cmd = f'(load "{lsp_forward}")\n'
    ok, msg = send_to_acad.send_acad_command(cmd, skip_esc=True)
    time.sleep(wait_s)
    return ok, msg

if __name__ == "__main__":
    lsp = sys.argv[1] if len(sys.argv) > 1 else r"d:\Dropbox\_Documents\RevitAI\scratch\test_aca.lsp"
    ok, msg = run_lisp(lsp)
    print("Run result:", ok, msg)

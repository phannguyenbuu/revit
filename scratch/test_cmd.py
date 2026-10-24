import sys, os, time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

test_f = "d:/Dropbox/_Documents/RevitAI/scratch_ping_test.txt"
if os.path.exists(test_f):
    os.remove(test_f)

cmd = f'(progn (setq f (open "{test_f}" "w")) (write-line "PONG" f) (close f))\n'
ok, msg = send_to_acad.send_acad_command(cmd, skip_esc=True)
print("Send:", ok, msg)
time.sleep(1.0)
print("File exists:", os.path.exists(test_f))
if os.path.exists(test_f):
    with open(test_f) as f:
        print("Content:", f.read().strip())

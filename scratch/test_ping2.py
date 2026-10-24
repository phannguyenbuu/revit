import sys, os, time, ctypes
from ctypes import wintypes
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

user32 = ctypes.windll.user32
test_f = "d:/Dropbox/_Documents/RevitAI/scratch_ping_test.txt"
if os.path.exists(test_f):
    os.remove(test_f)

# Send esc sequence first
send_to_acad.send_acad_command('")" ) ) ) ) (princ)\n', skip_esc=False)
time.sleep(0.3)

cmd = f'(progn (setq f (open "{test_f}" "w")) (write-line "HELLO_FROM_ACAD" f) (close f))\n'
ok, msg = send_to_acad.send_acad_command(cmd, skip_esc=True)
print("Send result:", ok, msg)

for i in range(10):
    time.sleep(0.5)
    if os.path.exists(test_f):
        with open(test_f) as f:
            print(f"Success at {i*0.5}s: {f.read().strip()}")
        break
else:
    print("Failed to receive output file")

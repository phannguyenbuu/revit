import sys, os, time
sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

test_f = "d:/Dropbox/_Documents/RevitAI/scratch_sel_now.txt"
if os.path.exists(test_f):
    os.remove(test_f)

cmd = f'(progn (setq f (open "{test_f}" "w")) (write-line (strcat "SS_I: " (itoa (if (ssget "_I") (sslength (ssget "_I")) 0))) f) (write-line (strcat "SS_P: " (itoa (if (ssget "_P") (sslength (ssget "_P")) 0))) f) (close f))\n'
send_to_acad.send_acad_command(cmd, skip_esc=True)

time.sleep(0.5)
if os.path.exists(test_f):
    with open(test_f) as f:
        print(f.read())
else:
    print("File not created!")

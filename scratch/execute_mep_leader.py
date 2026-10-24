import os
import sys
import time

sys.path.insert(0, r"d:\Dropbox\_Documents\RevitAI")
import send_to_acad

res_file = r"d:/Dropbox/_Documents/RevitAI/_action_result.txt"
if os.path.exists(res_file):
    os.remove(res_file)

# 1. Reset prompt cleanly
send_to_acad.send_acad_command('")" ) ) ) ) (princ "\\nRESET_PROMPT\\n")\n', skip_esc=False)
time.sleep(0.3)

# 2. Send load command
ok, msg = send_to_acad.send_acad_command('(load "d:/Dropbox/_Documents/RevitAI/_run_action.lsp")\n', timeout_ms=30000, skip_esc=True)
print("Send result:", ok, msg)

# 3. Wait and read log
for i in range(60):
    time.sleep(1.0)
    if os.path.exists(res_file):
        with open(res_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"[{i+1}s] Current content ({len(lines)} lines):")
        for line in lines:
            print("  ", line.strip())
        if any("STEP 3" in l for l in lines) or any("FATAL_ERROR" in l for l in lines):
            print("FINISHED!")
            break
else:
    print("Execution did not reach STEP 3 within timeout.")

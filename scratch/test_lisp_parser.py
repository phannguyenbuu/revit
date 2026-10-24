import os, sys, re, glob, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

lisp_dir = r"D:\Dropbox\CADLib\lisp"
lsp_files = glob.glob(os.path.join(lisp_dir, "**", "*.lsp"), recursive=True)

print(f"Total LSP files found: {len(lsp_files)}")

results = []
for p in lsp_files[:20]:
    fname = os.path.basename(p)
    content = ""
    for enc in ["utf-8", "cp1252", "cp1258", "latin-1"]:
        try:
            with open(p, "r", encoding=enc, errors="ignore") as f:
                content = f.read()
            break
        except:
            pass

    # Find c: commands
    cmds = re.findall(r'\(defun\s+(?:c:|C:)([a-zA-Z0-9_\-\+]+)', content)
    
    # Extract first 5 comment lines
    lines = content.splitlines()
    comments = []
    for l in lines[:20]:
        l_str = l.strip()
        if l_str.startswith(";"):
            c_clean = re.sub(r'^[;\s\*\=\-]+', '', l_str).strip()
            if c_clean:
                comments.append(c_clean)
        elif l_str.startswith("(") and len(comments) > 0:
            break
            
    results.append({
        "file": fname,
        "cmds": list(set(cmds)),
        "comments": " | ".join(comments[:3])
    })

for r in results:
    print(f"File: {r['file']} -> Cmds: {r['cmds']} | Desc: {r['comments'][:80]}")

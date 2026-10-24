import os, sys, re, glob, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

lisp_dir = r"D:\Dropbox\CADLib\lisp"
lsp_files = glob.glob(os.path.join(lisp_dir, "**", "*.lsp"), recursive=True)

def parse_lsp(file_path):
    rel_path = os.path.relpath(file_path, lisp_dir)
    fname = os.path.basename(file_path)
    content = ""
    for enc in ["utf-8", "cp1258", "cp1252", "latin-1"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except:
            pass
    if not content:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            pass

    # Extract commands: (defun c:XYZ or (defun C:XYZ
    raw_cmds = re.findall(r'\(defun\s+(?:c:|C:)([a-zA-Z0-9_\-\+]+)', content)
    cmds = []
    for c in raw_cmds:
        if c not in cmds:
            cmds.append(c)

    # Extract block comments ;| ... |;
    block_comments = re.findall(r';\|(.*?)\|;', content, re.DOTALL)
    
    # Extract line comments
    lines = content.splitlines()
    desc_lines = []
    
    # First look at header comments
    for l in lines[:35]:
        l_str = l.strip()
        if l_str.startswith(";"):
            c = re.sub(r'^[;\s\*\=\-\#\/]+', '', l_str).strip()
            # Skip empty or meaningless lines
            if c and not c.startswith("---") and not c.startswith("===") and len(c) > 3:
                desc_lines.append(c)
        elif l_str and not l_str.startswith(";") and len(desc_lines) >= 1:
            # Stop if we hit actual code after having found some comments
            break

    # If block comment exists, add it
    if block_comments:
        for bc in block_comments:
            clean_bc = [line.strip() for line in bc.splitlines() if line.strip()]
            desc_lines.extend(clean_bc[:4])

    # Clean description
    clean_desc = []
    for d in desc_lines:
        if d not in clean_desc and not d.startswith("vl-load-com") and not d.startswith("(vl-load"):
            clean_desc.append(d)

    summary = " • ".join(clean_desc[:4])
    if not summary:
        # Fallback description based on file name and commands
        name_no_ext = os.path.splitext(fname)[0]
        summary = f"Lisp tiện ích {name_no_ext}. Lệnh thực thi: {', '.join(cmds) if cmds else 'Nạp tự động'}"

    return {
        "file": fname,
        "relPath": rel_path.replace("\\", "/"),
        "fullPath": file_path.replace("\\", "/"),
        "commands": cmds,
        "description": summary
    }

all_data = [parse_lsp(p) for p in lsp_files]
print(f"Parsed {len(all_data)} lisp files successfully.")

# Count files with commands
with_cmds = [d for d in all_data if d["commands"]]
print(f"Files with c: commands: {len(with_cmds)} / {len(all_data)}")
total_cmds = sum(len(d["commands"]) for d in all_data)
print(f"Total commands discovered: {total_cmds}")

# Print first 15 entries
for d in all_data[:15]:
    print(f"[{d['file']}] Commands: {d['commands']}")
    print(f"    Desc: {d['description'][:100]}")

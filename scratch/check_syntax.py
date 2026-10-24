with open(r"d:\Dropbox\_Documents\RevitAI\mep_cleaner_and_leader.lsp", "r", encoding="utf-8") as f:
    lines = f.readlines()

in_str = False
paren = 0
for idx, line in enumerate(lines, 1):
    i = 0
    while i < len(line):
        c = line[i]
        if c == ';' and not in_str:
            break
        elif c == '"' and (i == 0 or line[i-1] != '\\'):
            in_str = not in_str
        elif not in_str:
            if c == '(':
                paren += 1
            elif c == ')':
                paren -= 1
                if paren < 0:
                    print(f"Line {idx}: Negative paren! {line.strip()}")
        i += 1
print(f"Final in_str: {in_str} | Final paren: {paren}")

import os
import re

root = r"D:\Dropbox\_Documents\Toolx\output\san_pham_anh_trang_ruby"

classes = set()
methods = set()
blocks = set()

for dirpath, dirnames, filenames in os.walk(root):
    for f in filenames:
        if f.lower().endswith('.rb'):
            p = os.path.join(dirpath, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
                # find :: classes
                for m in re.finditer(r'\b([A-Z]\w*(?:::[A-Z]\w*)+)', content):
                    classes.add(m.group(1))
                # find inline blocks { |x| ... }
                for m in re.finditer(r'\.\w+\s*\{[^}]*\}', content):
                    blocks.add(m.group(0))

print("Classes with ::", sorted(list(classes)))
print("\nInline blocks with {}:")
for b in sorted(list(blocks)):
    print(" -", b)

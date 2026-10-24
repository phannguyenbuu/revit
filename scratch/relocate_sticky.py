with open('web_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

marker = 'id="btnStickyExpandLeft"'
start_idx = content.find('<!-- Floating Sticky Expand Button')
if start_idx == -1:
    start_idx = content.find(marker)

end_idx = content.find('</button>', start_idx) + 9

button_block = content[start_idx:end_idx]
content = content[:start_idx] + content[end_idx:]

header_idx = content.find('</header>') + 9
content = content[:header_idx] + '\n\n' + button_block + '\n' + content[header_idx:]

with open('web_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: Relocated button block right after </header>")

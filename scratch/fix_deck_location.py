with open('web_dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

deck_marker = '<!-- CỤM ĐIỀU HƯỚNG & THAO TÁC 2 CỘT GỌN GÀNG (ĐƯA XUỐNG DƯỚI CANVAS 3D)'
deck_start = content.find(deck_marker)
if deck_start == -1:
    print("ERROR: deck_marker not found")
    sys.exit(1)

# Find the end of this deck
# The deck ends with </div>\n          </div>
deck_close_marker = '<!-- Action Buttons Grid -->'
idx_act = content.find(deck_close_marker, deck_start)
# After idx_act, find </div> (Action buttons grid), then </div> (col 2), then </div> (main deck)
d1 = content.find('</div>', idx_act)
d2 = content.find('</div>', d1 + 6)
d3 = content.find('</div>', d2 + 6)
deck_end = d3 + 6

deck_html = content[deck_start:deck_end]

# Remove deck from wrong position
content = content[:deck_start] + content[deck_end:]

# Now find the true closing </div> of tab-etabs-hub
hub_marker = '<div id="tab-etabs-hub"'
start_idx = content.find(hub_marker)

pos = start_idx + len(hub_marker)
depth = 1

while depth > 0 and pos < len(content):
    next_open = content.find('<div', pos)
    next_close = content.find('</div>', pos)
    
    if next_close == -1:
        break
        
    if next_open != -1 and next_open < next_close:
        depth += 1
        pos = next_open + 4
    else:
        depth -= 1
        pos = next_close + 6
        if depth == 0:
            true_close_idx = next_close
            break

print("True closing </div> of tab-etabs-hub found at index:", true_close_idx)
# Insert deck_html before true_close_idx
content = content[:true_close_idx] + '\n\n' + deck_html + '\n\n        ' + content[true_close_idx:]

with open('web_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: Relocated 2-column control deck right before closing of tab-etabs-hub!")

content = open('web_dashboard.py', encoding='utf-8').read()

hub_marker = '<div id="tab-etabs-hub"'
start_idx = content.find(hub_marker)
print("Start idx of tab-etabs-hub:", start_idx)

# Let's count open <div> and close </div> from start_idx
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
            print("Matching closing </div> found at index:", next_close)
            # Print lines around next_close
            line_no = content[:next_close].count('\n') + 1
            print("Line number of closing </div>:", line_no)
            lines = content[next_close-300:next_close+300]
            print("Context:\n", lines)

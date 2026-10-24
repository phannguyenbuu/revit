import json

with open(r'scratch/current_cad_selection.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f'Total items: {len(items)}')
for item in items:
    t = item.get('type')
    layer = item.get('layer')
    handle = item.get('handle')
    b_rvt = item.get('bbox_rvt')
    extra = ''
    if 'text' in item:
        extra = f'text="{item["text"]}"'
    elif 'block_name' in item:
        extra = f'block="{item["block_name"]}"'
    elif 'points_rvt' in item:
        extra = f'pts_rvt={item["points_rvt"]} closed={item.get("closed")}'
    elif 'start_rvt' in item:
        extra = f'line from {item["start_rvt"]} to {item["end_rvt"]}'
    
    min_x = round(b_rvt['min'][0], 3) if b_rvt else 0
    min_y = round(b_rvt['min'][1], 3) if b_rvt else 0
    max_x = round(b_rvt['max'][0], 3) if b_rvt else 0
    max_y = round(b_rvt['max'][1], 3) if b_rvt else 0
    print(f'[{handle}] {t:16} layer={layer:12} bbox_rvt=[({min_x}, {min_y}) to ({max_x}, {max_y})] {extra}')

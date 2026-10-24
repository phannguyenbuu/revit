import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\Dropbox\_Documents\RevitAI\bim_models_info.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total files: {data.get('count')}\n")
for item in data.get('files', []):
    fn = item['fileName']
    sz = item['sizeMB']
    dir_name = item.get('directory')
    bf = item.get('basicInfo') or {}
    fmt = bf.get('Format', 'Unknown')
    cw = bf.get('IsWorkshared', False)
    cp = bf.get('CentralPath', '')
    links = item.get('externalLinks') or []
    print(f"=== File: {fn} ({sz} MB) ===")
    print(f"  Folder: {dir_name}")
    print(f"  Format: {fmt} | Workshared: {cw}")
    if cp:
        print(f"  Central Path: {cp}")
    print(f"  Links count: {len(links)}")
    for lk in links[:8]:
        print(f"    -> [{lk.get('ExtType')}] {lk.get('Path')}")
    if len(links) > 8:
        print(f"    ... and {len(links)-8} more links")
    print()

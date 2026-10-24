import urllib.request
import json
import revit_cli

base_url = revit_cli.get_base_url()
payload = {
    'action': 'execute_dynamic',
    'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
    'typeName': 'RevitScript.GetProjectBrowserGroups',
    'methodName': 'Run',
    'args': {}
}
req = urllib.request.Request(f'{base_url}/api/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read().decode('utf-8'))
    groups = data.get('groups') or data.get('Groups') or []
    print(f"Total groups found: {len(groups)}")
    for i, g in enumerate(groups, 1):
        gname = g.get('groupName') or g.get('GroupName')
        vlist = g.get('views') or g.get('Views') or []
        print(f"[{i}] '{gname}' - {len(vlist)} views")
        for v in vlist[:4]:
            vid = v.get('id') or v.get('Id')
            vname = v.get('name') or v.get('Name')
            print(f"      - ID {vid}: {vname}")
        if len(vlist) > 4:
            print(f"      ... and {len(vlist)-4} more")

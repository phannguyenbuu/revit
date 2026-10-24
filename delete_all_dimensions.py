import sys
import argparse
import urllib.request
import json
import revit_cli

sys.stdout.reconfigure(encoding='utf-8')

def delete_dimensions(scope="file", view_id=None):
    """
    Xóa toàn bộ Dimension trong file Revit (hoặc theo View cụ thể).
    """
    payload = {
        'action': 'execute_dynamic',
        'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
        'typeName': 'RevitScript.DeleteDimensions',
        'methodName': 'Run',
        'args': {
            'scope': scope
        }
    }
    if view_id is not None:
        payload['args']['scope'] = 'view'
        payload['args']['viewId'] = int(view_id)

    base_url = revit_cli.get_base_url()
    req = urllib.request.Request(
        f'{base_url}/api/execute',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            data = json.loads(res.read().decode('utf-8'))
            print("==================================================")
            print(" KẾT QUẢ XÓA DIMENSION TRONG REVIT")
            print("==================================================")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
    except urllib.error.HTTPError as he:
        print(f"HTTPError: {he.code}")
        print(he.read().decode('utf-8'))
    except Exception as ex:
        print(f"Error calling bridge server: {ex}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Delete dimensions in Revit project file or specific views")
    parser.add_argument('--scope', default='file', choices=['file', 'active', 'view'], help="Scope to delete: 'file' (toàn bộ file), 'active' (view hiện tại), 'view' (theo view ID)")
    parser.add_argument('--view', default=None, help="View ID cụ thể (khi scope là view)")
    args = parser.parse_args()

    delete_dimensions(scope=args.scope, view_id=args.view)

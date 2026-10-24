import sys
import argparse
import urllib.request
import json
import revit_cli

sys.stdout.reconfigure(encoding='utf-8')

def clean_dimensions(target_view="all", remove_zeros=True, remove_broken_chains=True, preview_only=False):
    """
    Gọi server trung gian (bridge server) điều khiển Revit:
    - Loại bỏ các dim có giá trị bằng 0 (hoặc rebuild bỏ segment 0 trùng reference)
    - Loại bỏ các chuỗi dim bị ngắt khúc / gián đoạn ở giữa
    """
    payload = {
        'action': 'execute_dynamic',
        'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
        'typeName': 'RevitScript.CleanDimensionsBridge',
        'methodName': 'Run',
        'args': {
            'targetView': target_view,
            'removeZeros': remove_zeros,
            'removeBrokenChains': remove_broken_chains,
            'previewOnly': preview_only
        }
    }

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
            print(" KẾT QUẢ ĐIỀU KHIỂN REVIT TỪ SERVER TRUNG GIAN")
            print("==================================================")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
    except urllib.error.HTTPError as he:
        print(f"HTTPError: {he.code}")
        print(he.read().decode('utf-8'))
    except Exception as ex:
        print(f"Error calling bridge server: {ex}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Clean zero dimensions and broken chains via Revit Bridge Server")
    parser.add_argument('--view', default='all', help="View to clean: 'all', 'active', or view ID")
    parser.add_argument('--preview', action='store_true', help="Preview actions without modifying Revit")
    parser.add_argument('--keep-broken', action='store_true', help="Keep broken chains, only clean zeros")
    args = parser.parse_args()

    clean_dimensions(
        target_view=args.view,
        remove_zeros=True,
        remove_broken_chains=not args.keep_broken,
        preview_only=args.preview
    )

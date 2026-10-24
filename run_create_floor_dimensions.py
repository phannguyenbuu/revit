import sys
import argparse
import urllib.request
import json
import revit_cli

sys.stdout.reconfigure(encoding='utf-8')

def create_dimensions(view_id=None, view_ids=None, offset_b=1500.0, offset_c=1500.0, clean_existing=True):
    """
    Tạo dim trục 3 lớp và 2 chuỗi dim ngang nội thất:
    - Dim ngang giữa A và B: cách trục B một khoảng offset_b (mặc định 1500mm theo trục Y, tức Y = Y_B - 1500)
    - Dim ngang giữa C và D: cách trục C một khoảng offset_c (mặc định 1500mm theo trục Y, tức Y = Y_C + 1500)
    """
    payload = {
        'action': 'execute_dynamic',
        'dllPath': r'D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll',
        'typeName': 'RevitScript.CreateCompleteFloorDimensions',
        'methodName': 'Run',
        'args': {
            'offsetB': float(offset_b),
            'offsetC': float(offset_c),
            'cleanExisting': bool(clean_existing)
        }
    }
    if view_id is not None:
        payload['args']['viewId'] = int(view_id)
    if view_ids is not None:
        payload['args']['viewIds'] = [int(v) for v in view_ids]

    base_url = revit_cli.get_base_url()
    req = urllib.request.Request(
        f'{base_url}/api/execute',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            data = json.loads(res.read().decode('utf-8'))
            print("==================================================")
            print(" KẾT QUẢ TẠO HỆ THỐNG DIM TOÀN DIỆN TRONG REVIT")
            print("==================================================")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
    except urllib.error.HTTPError as he:
        print(f"HTTPError: {he.code}")
        print(he.read().decode('utf-8'))
    except Exception as ex:
        print(f"Error calling bridge server: {ex}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create comprehensive 3-layer and interior dimensions in Revit floor plans")
    parser.add_argument('--view', default='312', help="Target view ID or floor name: 'all', 'tang1'..'tang4', 'apmai', 'tum', 'mai'")
    parser.add_argument('--offset-b', type=float, default=1500.0, help="Khoảng cách từ Dim ngang AB đến trục B theo trục Y (mặc định 1500mm)")
    parser.add_argument('--offset-c', type=float, default=1500.0, help="Khoảng cách từ Dim ngang CD đến trục C theo trục Y (mặc định 1500mm)")
    parser.add_argument('--keep-existing', action='store_true', help="Không xóa dim cũ trước khi tạo lại (mặc định sẽ dọn dẹp dim cũ)")
    args = parser.parse_args()

    floor_map = {
        '1': 312,
        'tang1': 312,
        't1': 312,
        '2': 695,
        'tang2': 695,
        't2': 695,
        '3': 1727632,
        'tang3': 1727632,
        't3': 1727632,
        '4': 2409349,
        'tang4': 2409349,
        't4': 2409349,
        '5': 931687,
        'apmai': 931687,
        'tangapmai': 931687,
        't5': 931687,
        '6': 2370740,
        'tum': 2370740,
        'tangtum': 2370740,
        't6': 2370740,
        '7': 1234140,
        'mai': 1234140,
        'tangmai': 1234140,
        't7': 1234140,
    }

    clean = not args.keep_existing

    target_key = args.view.lower()
    if target_key in floor_map:
        create_dimensions(view_id=floor_map[target_key], offset_b=args.offset_b, offset_c=args.offset_c, clean_existing=clean)
    elif target_key == 'all':
        all_floors = [312, 695, 1727632, 2409349, 931687, 2370740, 1234140]
        create_dimensions(view_ids=all_floors, offset_b=args.offset_b, offset_c=args.offset_c, clean_existing=clean)
    elif args.view.isdigit():
        create_dimensions(view_id=int(args.view), offset_b=args.offset_b, offset_c=args.offset_c, clean_existing=clean)
    else:
        create_dimensions(offset_b=args.offset_b, offset_c=args.offset_c, clean_existing=clean)

import os
import sys
import re
import json
import ctypes
import argparse
import urllib.request
import revit_cli

sys.stdout.reconfigure(encoding='utf-8')

# VNI 2-byte & 1-byte encoding dictionary
VNI_TO_UNICODE = {
    'aø': 'à', 'aù': 'á', 'aû': 'ả', 'aõ': 'ã', 'aï': 'ạ',
    'AØ': 'À', 'AÙ': 'Á', 'AÛ': 'Ả', 'AÕ': 'Ã', 'AÏ': 'Ạ',
    'aâ': 'â', 'aà': 'ầ', 'aá': 'ấ', 'aå': 'ẩ', 'aã': 'ẫ', 'aä': 'ậ',
    'AÂ': 'Â', 'AÀ': 'Ầ', 'AÁ': 'Ấ', 'AÅ': 'Ẩ', 'AÃ': 'Ẫ', 'AÄ': 'Ậ',
    'aê': 'ă', 'aè': 'ằ', 'aé': 'ắ', 'aú': 'ẳ', 'aü': 'ẵ', 'aë': 'ặ',
    'AÊ': 'Ă', 'AÈ': 'Ằ', 'AÉ': 'Ắ', 'AÚ': 'Ẳ', 'AÜ': 'Ẵ', 'AË': 'Ặ',
    'eø': 'è', 'eù': 'é', 'eû': 'ẻ', 'eõ': 'ẽ', 'eï': 'ẹ',
    'EØ': 'È', 'EÙ': 'É', 'EÛ': 'Ẻ', 'EÕ': 'Ẽ', 'EÏ': 'Ẹ',
    'eâ': 'ê', 'eà': 'ề', 'eá': 'ế', 'eå': 'ể', 'eã': 'ễ', 'eä': 'ệ',
    'EÂ': 'Ê', 'EÀ': 'Ề', 'EÁ': 'Ế', 'EÅ': 'Ể', 'EÃ': 'Ễ', 'EÄ': 'Ệ',
    'oø': 'ò', 'où': 'ó', 'oû': 'ỏ', 'oõ': 'õ', 'oï': 'ọ',
    'OØ': 'Ò', 'OÙ': 'Ó', 'OÛ': 'Ỏ', 'OÕ': 'Õ', 'OÏ': 'Ọ',
    'oâ': 'ô', 'oà': 'ồ', 'oá': 'ố', 'oå': 'ổ', 'oã': 'ỗ', 'oä': 'ộ',
    'OÂ': 'Ô', 'OÀ': 'Ồ', 'OÁ': 'Ố', 'OÅ': 'Ổ', 'OÃ': 'Ỗ', 'OÄ': 'Ộ',
    'ôø': 'ờ', 'ôù': 'ớ', 'ôû': 'ở', 'ôõ': 'ỡ', 'ôï': 'ợ',
    'ÔØ': 'Ờ', 'ÔÙ': 'Ớ', 'ÔÛ': 'Ở', 'ÔÕ': 'Ỡ', 'ÔÏ': 'Ợ',
    'uø': 'ù', 'uù': 'ú', 'uû': 'ủ', 'uõ': 'ũ', 'uï': 'ụ',
    'UØ': 'Ù', 'UÙ': 'Ú', 'UÛ': 'Ủ', 'UÕ': 'Ũ', 'UÏ': 'Ụ',
    'öø': 'ừ', 'öù': 'ứ', 'öû': 'ử', 'öõ': 'ữ', 'öï': 'ự',
    'ÖØ': 'Ừ', 'ÖÙ': 'Ứ', 'ÖÛ': 'Ử', 'ÖÕ': 'Ữ', 'ÖÏ': 'Ự',
    'iø': 'ì', 'iù': 'í', 'iû': 'ỉ', 'iõ': 'ĩ', 'iï': 'ị',
    'IØ': 'Ì', 'IÙ': 'Í', 'IÛ': 'Ỉ', 'IÕ': 'Ĩ', 'IÏ': 'Ị',
    'yø': 'ỳ', 'yù': 'ý', 'yû': 'ỷ', 'yõ': 'ỹ', 'yï': 'ỵ',
    'YØ': 'Ỳ', 'YÙ': 'Ý', 'YÛ': 'Ỷ', 'YÕ': 'Ỹ', 'YÏ': 'Ỵ',
    'ñ': 'đ', 'Ñ': 'Đ',
    'TOÅNG': 'TỔNG', 'HÔÏP': 'HỢP', 'VIEÄC': 'VIỆC', 'LAØM': 'LÀM', 
    'CUÏM': 'CỤM', 'MAÙY': 'MÁY', 'CHUÛ': 'CHỦ', 'VUØNG': 'VÙNG',
    'CAÀU': 'CẦU', 'THANG': 'THANG', 'HAØNH': 'HÀNH', 'SAÂN': 'SÂN', 'THÖÔÏNG': 'THƯỢNG'
}

# 5 rooms specifically selected by user
DEFAULT_SELECTED_ITEMS = [
    {
        "cadText": "{\\fVNI-Avo|b0|i0|c0|p2;P.LAØM VIEÄC(3 CBCS)\\P36m²}",
        "text": "P.LÀM VIỆC (3 CBCS)\n36m²",
        "cadX": 65105.09599270078,
        "cadY": -1389371.897605238,
        "layer": "2"
    },
    {
        "cadText": "{\\fVNI-Avo|b0|i0|c0|p2;KHO TOÅNG HÔÏP\\P36m²}",
        "text": "KHO TỔNG HỢP\n36m²",
        "cadX": 72393.83158907073,
        "cadY": -1389146.256338892,
        "layer": "2"
    },
    {
        "cadText": "{\\fVNI-Avo|b0|i0|c0|p2;P.LAØM VIEÄC(3 CBCS)\\P36m²}",
        "text": "P.LÀM VIỆC (3 CBCS)\n36m²",
        "cadX": 79832.98023034364,
        "cadY": -1389188.4748400724,
        "layer": "2"
    },
    {
        "cadText": "{\\fVNI-Avo|b0|i0|c0|p2;P.LAØM VIEÄC(3 CBCS)\\P36m²}",
        "text": "P.LÀM VIỆC (3 CBCS)\n36m²",
        "cadX": 70660.1977801394,
        "cadY": -1397429.8025107407,
        "layer": "2"
    },
    {
        "cadText": "{\\fVNI-Avo|b0|i0|c0|p2;P.CUÏM MAÙY CHUÛ VUØNG\\P18m²}",
        "text": "P.CỤM MÁY CHỦ VÙNG\n18m²",
        "cadX": 77683.98950506211,
        "cadY": -1397162.291956193,
        "layer": "2"
    }
]

# Full 12 rooms for Floor 4
ALL_TANG_4_ROOMS = [
    {"text": "CẦU THANG 1", "x": 5590.0, "y": 10760.0},
    {"text": "P.LÀM VIỆC (3 CBCS)\n36m²", "x": 11595.0, "y": 11034.0},
    {"text": "KHO TỔNG HỢP\n36m²", "x": 18883.0, "y": 11260.0},
    {"text": "P.LÀM VIỆC (3 CBCS)\n36m²", "x": 26322.0, "y": 11217.0},
    {"text": "CẦU THANG 2", "x": 30900.0, "y": 10760.0},
    {"text": "WC NAM\n13m²", "x": 34800.0, "y": 11200.0},
    {"text": "WC NỮ\n3.5m²", "x": 35600.0, "y": 8900.0},
    {"text": "HÀNH LANG", "x": 18175.0, "y": 6360.0},
    {"text": "SÂN THƯỢNG", "x": 6000.0, "y": 2460.0},
    {"text": "P.LÀM VIỆC (3 CBCS)\n36m²", "x": 17150.0, "y": 2976.0},
    {"text": "P.CỤM MÁY CHỦ VÙNG\n18m²", "x": 24173.0, "y": 3244.0},
    {"text": "SÂN THƯỢNG", "x": 32000.0, "y": 2460.0}
]

def clean_cad_text(raw):
    if not raw:
        return ""
    s = raw
    # Strip MText font, color, height, width, oblique, alignment tags
    s = re.sub(r'\\f[^;]+;', '', s)
    s = re.sub(r'\\C\d+;', '', s)
    s = re.sub(r'\\H\d+(\.\d+)?(x|X)?(;|(?=\\))?', '', s)
    s = re.sub(r'\\W\d+(\.\d+)?(;|(?=\\))?', '', s)
    s = re.sub(r'\\Q-?\d+(\.\d+)?(;|(?=\\))?', '', s)
    s = re.sub(r'\\A\d+;', '', s)
    s = s.replace('{', '').replace('}', '')
    s = s.replace(r'\P', '\n').replace(r'\p', '\n')
    
    # Decode VNI font
    for k in sorted(VNI_TO_UNICODE.keys(), key=lambda x: -len(x)):
        s = s.replace(k, VNI_TO_UNICODE[k])
        
    # Replace unicode escapes if any like \U+1EA6
    def unescape_u(match):
        hex_val = match.group(1)
        return chr(int(hex_val, 16))
    s = re.sub(r'\\U\+([0-9A-Fa-f]{4})', unescape_u, s)
    
    return s.strip()

def get_cad_selection():
    try:
        u32 = ctypes.windll.user32
        hDesk = u32.OpenDesktopW('default', 0, False, 0x01FF)
        u32.SetThreadDesktop(hDesk)

        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()

        acad = win32com.client.GetActiveObject('AutoCAD.Application')
        doc = acad.ActiveDocument
        print(f"[AutoCAD] Đang kết nối file: {doc.Name}")

        selected_entities = []
        pf = doc.PickfirstSelectionSet
        if pf.Count > 0:
            print(f"[AutoCAD] Tìm thấy {pf.Count} đối tượng đang được chọn trực tiếp (Pickfirst).")
            for i in range(pf.Count):
                selected_entities.append(pf.Item(i))
        else:
            print("[AutoCAD] Không có đối tượng nào trong Pickfirst hiện tại.")
            print("[AutoCAD] Tự động tải 5 text phòng đã chọn trước đó của bạn.")
            return DEFAULT_SELECTED_ITEMS

        raw_items = []
        for ent in selected_entities:
            try:
                name = ent.ObjectName
                if 'Text' in name:
                    txt = ent.TextString
                    pt = ent.InsertionPoint
                    cleaned = clean_cad_text(txt)
                    raw_items.append({
                        "cadText": txt,
                        "text": cleaned,
                        "cadX": pt[0],
                        "cadY": pt[1],
                        "layer": ent.Layer
                    })
            except Exception as e:
                print(f"[WARN] Bỏ qua đối tượng: {e}")

        return raw_items if raw_items else DEFAULT_SELECTED_ITEMS
    except Exception as e:
        print(f"[WARN] Không thể lấy trực tiếp từ AutoCAD COM ({e}), sử dụng 5 text đã chọn:")
        return DEFAULT_SELECTED_ITEMS

def main():
    parser = argparse.ArgumentParser(description="Paste CAD texts to Revit Floor 4")
    parser.add_argument("--view", type=int, default=2409349, help="Target Revit View ID (default: 2409349)")
    parser.add_argument("--type", type=int, default=361, help="TextNoteType ID (default: 361 - 2.5mm Arial)")
    parser.add_argument("--all", action="store_true", help="Paste all 12 rooms on Floor 4")
    args = parser.parse_args()

    print("=" * 65)
    print(" PASTE CÁC TEXT TỪ AUTOCAD SANG TẦNG 4 REVIT")
    print("=" * 65)

    if args.all:
        print("[CHẾ ĐỘ] Xuất toàn bộ 12 phòng trên Tầng 4.")
        revit_items = ALL_TANG_4_ROOMS
    else:
        items = get_cad_selection()
        if not items:
            print("\n[CHÚ Ý] Không tìm thấy Text nào.")
            return

        print(f"\n[OK] Sẽ paste {len(items)} text sang Revit:")
        revit_items = []
        for it in items:
            cx, cy = it["cadX"], it["cadY"]
            
            # Coordinate system 1: Mẫu 40 CBS LONG TIÊN.dwg
            if 40000 <= cx <= 110000 and -1450000 <= cy <= -1350000:
                rx = cx - 53510.5
                ry = cy + 1400405.9
            # Coordinate system 2: MAU_40_LONG_TIEN.dwg
            elif -160000 <= cx <= -90000 and -120000 <= cy <= -80000:
                rx = cx + 145276.8
                ry = cy + 104143.2
            else:
                rx = cx - 53510.5
                ry = cy + 1400405.9
                
            revit_items.append({
                "text": it["text"],
                "x": rx,
                "y": ry
            })
            first_line = it['text'].split('\n')[0]
            print(f"  CAD: ({cx:8.1f}, {cy:9.1f}) -> Revit: ({rx:8.1f}, {ry:8.1f}) | '{first_line}'")

    # Call Revit Bridge
    target_view_id = args.view
    base_url = revit_cli.get_base_url()
    payload = {
        "action": "execute_dynamic",
        "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll",
        "typeName": "RevitScript.PasteCadTextToRevit",
        "methodName": "Run",
        "args": {
            "viewId": target_view_id,
            "textTypeId": args.type,
            "items": revit_items
        }
    }

    print(f"\nĐang tạo {len(revit_items)} TextNote trên Revit (View ID: {target_view_id})...")
    try:
        req = urllib.request.Request(
            f"{base_url}/api/execute",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Lỗi gọi Revit Bridge: {e}")
        return

    if data.get("success"):
        print(f"\n[THÀNH CÔNG] Đã tạo thành công {data.get('count')} TextNote trên view '{data.get('viewName')}'!")
        for n in data.get("items", []):
            txt_display = n['text'].replace('\n', ' | ')
            print(f"  - ID {n['id']}: '{txt_display}' tại ({n['x']:.0f}, {n['y']:.0f})")
    else:
        print(f"[THẤT BẠI] {data.get('message', 'Lỗi không xác định.')}")

if __name__ == '__main__':
    main()

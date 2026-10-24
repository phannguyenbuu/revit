import argparse
import json
import urllib.request
import sys
import revit_cli

def main():
    parser = argparse.ArgumentParser(description="Auto dimension selected wall(s) with all openings and intersections (like AutoCAD Architecture Entire Walls)")
    parser.add_argument("--offset", type=float, default=1200.0, help="Offset from wall line in mm (default 1200)")
    parser.add_argument("--wall", type=int, nargs="*", help="Optional wall Element ID(s). If omitted, uses currently selected walls in Revit.")
    args = parser.parse_args()

    base_url = revit_cli.get_base_url()
    payload = {
        "action": "execute_dynamic",
        "dllPath": r"D:\Dropbox\_Documents\RevitAI\bin\Release\net10.0-windows\DynamicConverter_DoorD7_v16.dll",
        "typeName": "RevitScript.DimSelectedWall",
        "methodName": "Run",
        "args": {
            "offsetMm": args.offset,
            "wallIds": args.wall if args.wall else None
        }
    }

    try:
        req = urllib.request.Request(
            base_url + "/api/execute",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("success"):
                print(f"[SUCCESS] Processed {data.get('wallsProcessed')} wall(s), created {data.get('dimensionsCreated')} dimension chain(s)!")
                print(f"Shifted {data.get('shiftedCount')} small text segments (<= 200mm) for legibility.")
                for d in data.get("dimensions", []):
                    print(f" - Dimension ID {d.get('id')}: {d.get('numSegments')} segments")
            else:
                print(f"[FAILED] {data.get('message', data.get('error', 'Unknown error'))}")
    except Exception as e:
        print(f"[ERROR] Failed to execute: {e}")

if __name__ == "__main__":
    main()

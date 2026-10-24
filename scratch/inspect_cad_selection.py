import win32com.client
import sys
import json

def get_cad_selection():
    try:
        acad = win32com.client.GetActiveObject("AutoCAD.Application")
    except Exception as e:
        print(f"Error connecting to AutoCAD: {e}")
        return

    doc = acad.ActiveDocument
    print(f"Active Document: {doc.Name}")

    # Try PickfirstSelectionSet first
    try:
        ss = doc.PickfirstSelectionSet
        count = ss.Count
        print(f"PickfirstSelectionSet Count: {count}")
    except Exception as e:
        print(f"PickfirstSelectionSet error: {e}")
        ss = None

    if ss is None or count == 0:
        try:
            ss = doc.ActiveSelectionSet
            count = ss.Count
            print(f"ActiveSelectionSet Count: {count}")
        except Exception as e:
            print(f"ActiveSelectionSet error: {e}")
            return

    entities = []
    for i in range(count):
        ent = ss.Item(i)
        obj_name = ent.ObjectName
        layer = ent.Layer
        handle = ent.Handle
        info = {
            "index": i,
            "type": obj_name,
            "layer": layer,
            "handle": handle
        }

        if obj_name == "AcDbPolyline":
            coords = list(ent.Coordinates)
            pts = []
            for j in range(0, len(coords), 2):
                pts.append([coords[j], coords[j+1]])
            info["points"] = pts
            info["closed"] = ent.Closed
            try:
                min_pt, max_pt = ent.GetBoundingBox()
                info["bbox"] = {
                    "min": [min_pt[0], min_pt[1], min_pt[2]],
                    "max": [max_pt[0], max_pt[1], max_pt[2]]
                }
            except:
                pass
        elif obj_name == "AcDbLine":
            sp = ent.StartPoint
            ep = ent.EndPoint
            info["start"] = [sp[0], sp[1], sp[2]]
            info["end"] = [ep[0], ep[1], ep[2]]
        elif obj_name == "AcDbBlockReference":
            info["name"] = ent.EffectiveName if hasattr(ent, "EffectiveName") else ent.Name
            ip = ent.InsertionPoint
            info["insertion"] = [ip[0], ip[1], ip[2]]
            info["rotation"] = ent.Rotation
            try:
                min_pt, max_pt = ent.GetBoundingBox()
                info["bbox"] = {
                    "min": [min_pt[0], min_pt[1], min_pt[2]],
                    "max": [max_pt[0], max_pt[1], max_pt[2]]
                }
            except:
                pass
            # Check attributes
            if ent.HasAttributes:
                attrs = {}
                for att in ent.GetAttributes():
                    attrs[att.TagString] = att.TextString
                info["attributes"] = attrs
        elif obj_name in ["AcDbText", "AcDbMText"]:
            info["text"] = ent.TextString
            ip = ent.InsertionPoint
            info["insertion"] = [ip[0], ip[1], ip[2]]
        else:
            try:
                min_pt, max_pt = ent.GetBoundingBox()
                info["bbox"] = {
                    "min": [min_pt[0], min_pt[1], min_pt[2]],
                    "max": [max_pt[0], max_pt[1], max_pt[2]]
                }
            except:
                pass
        entities.append(info)

    with open(r"scratch\cad_selection_dump.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    print(f"Dumped {len(entities)} entities to scratch\\cad_selection_dump.json")

if __name__ == "__main__":
    get_cad_selection()

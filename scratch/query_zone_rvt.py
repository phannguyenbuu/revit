import urllib.request
import json

code = """using System;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

public class QueryZone : IExternalScript {
    public string Execute(UIApplication app) {
        var doc = app.ActiveUIDocument.Document;
        var cols = new FilteredElementCollector(doc)
            .OfCategory(BuiltInCategory.OST_StructuralColumns)
            .WhereElementIsNotElementType()
            .Cast<FamilyInstance>()
            .Where(c => {
                var loc = (c.Location as LocationPoint)?.Point;
                return loc != null && loc.X > 32 * 3.28084 && loc.X < 39 * 3.28084 && loc.Y > 11 * 3.28084 && loc.Y < 15 * 3.28084;
            })
            .Select(c => {
                var loc = (c.Location as LocationPoint).Point;
                return $"Col {c.Id}: {c.Symbol.Name} at ({loc.X/3.28084:F3}, {loc.Y/3.28084:F3})";
            });

        var walls = new FilteredElementCollector(doc)
            .OfCategory(BuiltInCategory.OST_Walls)
            .WhereElementIsNotElementType()
            .Cast<Wall>()
            .Where(w => {
                var crv = (w.Location as LocationCurve)?.Curve;
                if (crv == null) return false;
                var p0 = crv.GetEndPoint(0);
                var p1 = crv.GetEndPoint(1);
                double minX = Math.Min(p0.X, p1.X)/3.28084;
                double maxX = Math.Max(p0.X, p1.X)/3.28084;
                double minY = Math.Min(p0.Y, p1.Y)/3.28084;
                double maxY = Math.Max(p0.Y, p1.Y)/3.28084;
                return maxX > 32 && minX < 39 && maxY > 11 && minY < 15;
            })
            .Select(w => {
                var crv = (w.Location as LocationCurve).Curve;
                var p0 = crv.GetEndPoint(0);
                var p1 = crv.GetEndPoint(1);
                return $"Wall {w.Id}: {w.WallType.Name} from ({p0.X/3.28084:F3}, {p0.Y/3.28084:F3}) to ({p1.X/3.28084:F3}, {p1.Y/3.28084:F3})";
            });

        var wins = new FilteredElementCollector(doc)
            .OfCategory(BuiltInCategory.OST_Windows)
            .WhereElementIsNotElementType()
            .Cast<FamilyInstance>()
            .Select(w => {
                var loc = (w.Location as LocationPoint)?.Point;
                return $"Win {w.Id}: {w.Symbol.Family.Name} - {w.Symbol.Name} at ({loc.X/3.28084:F3}, {loc.Y/3.28084:F3})";
            });

        return string.Join("\\n", cols.Concat(walls).Concat(wins));
    }
}
"""

req = urllib.request.Request('http://127.0.0.1:8090/api/execute', data=json.dumps({'code': code}).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(res.get('result', res))
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code)
    print(e.read().decode('utf-8'))


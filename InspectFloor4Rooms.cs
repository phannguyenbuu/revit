using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloor4Rooms
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "no doc" };

            var view = doc.GetElement(new ElementId(2409349L)) as View;
            if (view == null) return new { error = "no view" };

            var walls = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Select(w => {
                    var loc = w.Location as LocationCurve;
                    var c = loc?.Curve;
                    var p0 = c != null ? c.GetEndPoint(0) : XYZ.Zero;
                    var p1 = c != null ? c.GetEndPoint(1) : XYZ.Zero;
                    return new {
                        id = w.Id.Value,
                        x0 = p0.X * 304.8,
                        y0 = p0.Y * 304.8,
                        x1 = p1.X * 304.8,
                        y1 = p1.Y * 304.8
                    };
                })
                .ToList();

            var rooms = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .WherePasses(new ElementLevelFilter(view.GenLevel.Id))
                .Cast<SpatialElement>()
                .Select(r => new {
                    id = r.Id.Value,
                    name = r.Name,
                    area = r.Area * 0.092903,
                    locX = (r.Location as LocationPoint)?.Point.X * 304.8,
                    locY = (r.Location as LocationPoint)?.Point.Y * 304.8
                })
                .ToList();

            return new { wallCount = walls.Count, roomCount = rooms.Count, rooms };
        }
    }
}

using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWestCubicleWalls
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => w.LevelId.Value == 311)
                .Select(w => {
                    var loc = w.Location as LocationCurve;
                    if (loc == null) return null;
                    var c = loc.Curve;
                    var p1 = c.GetEndPoint(0);
                    var p2 = c.GetEndPoint(1);
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        p1 = new { x = p1.X * 304.8, y = p1.Y * 304.8 },
                        p2 = new { x = p2.X * 304.8, y = p2.Y * 304.8 }
                    };
                })
                .Where(w => w != null && (Math.Min(w.p1.x, w.p2.x) >= 19000 && Math.Max(w.p1.x, w.p2.x) <= 24000) 
                                      && (Math.Min(w.p1.y, w.p2.y) >= 11500 && Math.Max(w.p1.y, w.p2.y) <= 13500))
                .ToList();

            return walls;
        }
    }
}

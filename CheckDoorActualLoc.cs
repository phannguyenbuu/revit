using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckDoorActualLoc
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(d =>
                {
                    var lp = d.Location as LocationPoint;
                    var bb = d.get_BoundingBox(null);
                    return new
                    {
                        id = d.Id.Value,
                        name = d.Name,
                        fam = d.Symbol?.FamilyName,
                        sym = d.Symbol?.Name,
                        host = d.Host != null ? $"{d.Host.Id.Value} ({d.Host.Name})" : "none",
                        hasLoc = d.Location != null,
                        pt = lp != null ? new { x = lp.Point.X * 0.3048, y = lp.Point.Y * 0.3048 } : null,
                        bbMin = bb != null ? new { x = bb.Min.X * 0.3048, y = bb.Min.Y * 0.3048 } : null,
                        bbMax = bb != null ? new { x = bb.Max.X * 0.3048, y = bb.Max.Y * 0.3048 } : null
                    };
                })
                .ToList();

            return new { count = doors.Count, doors };
        }
    }
}

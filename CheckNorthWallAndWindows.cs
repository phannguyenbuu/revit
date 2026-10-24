using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckNorthWallAndWindows
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var wins = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Windows)
                .Cast<FamilyInstance>()
                .Where(w => (w.Location as LocationPoint)?.Point.Y * FT_TO_MM > 13000)
                .Select(w => {
                    var pt = (w.Location as LocationPoint)?.Point;
                    var host = w.Host;
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        symName = w.Symbol.Name,
                        x = pt != null ? Math.Round(pt.X * FT_TO_MM, 0) : 0,
                        y = pt != null ? Math.Round(pt.Y * FT_TO_MM, 0) : 0,
                        hostId = host?.Id.Value,
                        hostName = host?.Name
                    };
                })
                .OrderBy(w => w.x)
                .ToList();

            return wins;
        }
    }
}

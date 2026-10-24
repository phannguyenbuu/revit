using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowsToModify
    {
        private static double ToM(double ft) => ft * 0.3048;
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find Grids
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Select(g =>
                {
                    Line line = g.Curve as Line;
                    return new
                    {
                        name = g.Name,
                        p1 = line != null ? new { x = ToM(line.GetEndPoint(0).X), y = ToM(line.GetEndPoint(0).Y) } : null,
                        p2 = line != null ? new { x = ToM(line.GetEndPoint(1).X), y = ToM(line.GetEndPoint(1).Y) } : null
                    };
                })
                .ToList();

            // Collect all windows
            var windows = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            var winDetails = new List<object>();

            foreach (var win in windows)
            {
                var locPoint = (win.Location as LocationPoint)?.Point;
                double x = locPoint != null ? ToM(locPoint.X) : 0;
                double y = locPoint != null ? ToM(locPoint.Y) : 0;
                double z = locPoint != null ? ToM(locPoint.Z) : 0;

                var level = doc.GetElement(win.LevelId) as Level;
                var host = win.Host as Wall;

                // Parameters: Sill Height
                var sillParam = win.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM);
                double sill_mm = sillParam != null ? ToMm(sillParam.AsDouble()) : 0;

                // Height: Check instance or symbol parameter
                var heightParam = win.get_Parameter(BuiltInParameter.WINDOW_HEIGHT) 
                    ?? win.Symbol.get_Parameter(BuiltInParameter.WINDOW_HEIGHT)
                    ?? win.LookupParameter("Height")
                    ?? win.Symbol.LookupParameter("Height")
                    ?? win.LookupParameter("Chiều cao")
                    ?? win.Symbol.LookupParameter("Chiều cao");

                double height_mm = heightParam != null ? ToMm(heightParam.AsDouble()) : 0;
                bool heightIsType = heightParam != null && heightParam.Element is ElementType;

                winDetails.Add(new
                {
                    id = win.Id.Value,
                    symbolName = win.Symbol.Name,
                    familyName = win.Symbol.FamilyName,
                    x = Math.Round(x, 3),
                    y = Math.Round(y, 3),
                    z = Math.Round(z, 3),
                    level = level?.Name,
                    levelElev_m = level != null ? ToM(level.Elevation) : 0,
                    sill_mm = Math.Round(sill_mm, 1),
                    height_mm = Math.Round(height_mm, 1),
                    heightIsType,
                    heightParamName = heightParam?.Definition.Name,
                    hostName = host?.Name
                });
            }

            return new
            {
                totalWindows = windows.Count,
                grids,
                windows = winDetails
            };
        }
    }
}

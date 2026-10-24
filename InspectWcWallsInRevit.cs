using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWcWallsInRevit
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            Level level2 = doc.GetElement(new ElementId(694L)) as Level;
            if (level2 == null) return new { error = "Level 2 not found" };

            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => w.LevelId == level2.Id)
                .ToList();

            var wcWalls = new List<object>();
            foreach (var w in walls)
            {
                var locCurve = w.Location as LocationCurve;
                if (locCurve == null) continue;
                var p1 = locCurve.Curve.GetEndPoint(0);
                var p2 = locCurve.Curve.GetEndPoint(1);

                double x1 = p1.X * FT2M;
                double y1 = p1.Y * FT2M;
                double x2 = p2.X * FT2M;
                double y2 = p2.Y * FT2M;

                double minX = Math.Min(x1, x2);
                double maxX = Math.Max(x1, x2);
                double minY = Math.Min(y1, y2);
                double maxY = Math.Max(y1, y2);

                if (maxX >= 33.0 && minX <= 37.2 && maxY >= 7.5 && minY <= 10.0)
                {
                    var comment = w.LookupParameter("Comments")?.AsString() ?? "";
                    wcWalls.Add(new
                    {
                        id = w.Id.Value,
                        type = w.WallType.Name,
                        comment,
                        p1 = new double[] { Math.Round(x1, 3), Math.Round(y1, 3) },
                        p2 = new double[] { Math.Round(x2, 3), Math.Round(y2, 3) },
                        length = Math.Round(locCurve.Curve.Length * FT2M, 3)
                    });
                }
            }

            // Also check doors in this area
            var doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(d => d.LevelId == level2.Id)
                .ToList();

            var wcDoors = new List<object>();
            foreach (var d in doors)
            {
                var pt = (d.Location as LocationPoint)?.Point;
                if (pt != null)
                {
                    double x = pt.X * FT2M;
                    double y = pt.Y * FT2M;
                    if (x >= 33.0 && x <= 37.2 && y >= 7.5 && y <= 10.0)
                    {
                        wcDoors.Add(new
                        {
                            id = d.Id.Value,
                            name = d.Name,
                            mark = d.LookupParameter("Mark")?.AsString(),
                            pos = new double[] { Math.Round(x, 3), Math.Round(y, 3) },
                            hostId = d.Host?.Id.Value
                        });
                    }
                }
            }

            return new
            {
                wcWallsCount = wcWalls.Count,
                wcWalls,
                wcDoorsCount = wcDoors.Count,
                wcDoors
            };
        }
    }
}

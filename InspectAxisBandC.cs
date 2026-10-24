using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAxisBandC
    {
        private static double ToM(double ft) => ft * 0.3048;
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Grids
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Select(g =>
                {
                    Line line = g.Curve as Line;
                    return new
                    {
                        name = g.Name,
                        p1 = line != null ? new { x = Math.Round(ToM(line.GetEndPoint(0).X), 2), y = Math.Round(ToM(line.GetEndPoint(0).Y), 2) } : null,
                        p2 = line != null ? new { x = Math.Round(ToM(line.GetEndPoint(1).X), 2), y = Math.Round(ToM(line.GetEndPoint(1).Y), 2) } : null
                    };
                })
                .ToList();

            // 2. All Windows in model
            var allWindows = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            var winList = new List<object>();
            foreach (var w in allWindows)
            {
                var lp = (w.Location as LocationPoint)?.Point;
                if (lp == null) continue;

                double x = ToM(lp.X);
                double y = ToM(lp.Y);
                double z = ToM(lp.Z);

                var lvl = doc.GetElement(w.LevelId) as Level;
                var sillParam = w.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM);
                var headParam = w.get_Parameter(BuiltInParameter.INSTANCE_HEAD_HEIGHT_PARAM);

                winList.Add(new
                {
                    id = w.Id.Value,
                    symbol = w.Symbol.Name,
                    family = w.Symbol.FamilyName,
                    level = lvl?.Name,
                    x = Math.Round(x, 2),
                    y = Math.Round(y, 2),
                    z = Math.Round(z, 2),
                    sill_mm = sillParam != null ? Math.Round(ToMm(sillParam.AsDouble()), 1) : 0,
                    head_mm = headParam != null ? Math.Round(ToMm(headParam.AsDouble()), 1) : 0,
                    isNearB = Math.Abs(y - 5.40) < 0.6,
                    isNearC = Math.Abs(y - 7.80) < 0.6
                });
            }

            // 3. All Walls near Grid B (Y ~ 5.4) and Grid C (Y ~ 7.8)
            var allWalls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .WhereElementIsNotElementType()
                .Cast<Wall>()
                .ToList();

            var wallsNearB = new List<object>();
            var wallsNearC = new List<object>();

            foreach (var wall in allWalls)
            {
                var lc = wall.Location as LocationCurve;
                if (lc == null) continue;
                var p0 = lc.Curve.GetEndPoint(0);
                var p1 = lc.Curve.GetEndPoint(1);

                double y0 = ToM(p0.Y);
                double y1 = ToM(p1.Y);
                double avgY = (y0 + y1) / 2.0;

                var lvl = doc.GetElement(wall.LevelId) as Level;

                var wallInfo = new
                {
                    id = wall.Id.Value,
                    name = wall.WallType.Name,
                    level = lvl?.Name,
                    start = new { x = Math.Round(ToM(p0.X), 2), y = Math.Round(y0, 2) },
                    end = new { x = Math.Round(ToM(p1.X), 2), y = Math.Round(y1, 2) }
                };

                if (Math.Abs(avgY - 5.40) < 0.3)
                {
                    wallsNearB.Add(wallInfo);
                }
                else if (Math.Abs(avgY - 7.80) < 0.3)
                {
                    wallsNearC.Add(wallInfo);
                }
            }

            return new
            {
                grids,
                totalWindows = allWindows.Count,
                windows = winList,
                wallsNearB,
                wallsNearC
            };
        }
    }
}

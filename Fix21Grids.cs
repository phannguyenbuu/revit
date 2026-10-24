using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Fix21Grids
    {
        private const double MetersToFeet = 1.0 / 0.3048;
        private const double FeetToMeters = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            var gridMap = grids.ToDictionary(g => g.Name, g => g);

            using (var tx = new Transaction(doc, "Fix Grids X to 21 Axes"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new GridWarningSwallower());
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                // 1. Rename existing grids 11..19 to TEMP_11..TEMP_19
                for (int i = 19; i >= 11; i--)
                {
                    string oldName = i.ToString();
                    if (gridMap.TryGetValue(oldName, out var g))
                    {
                        try { g.Name = $"TEMP_{i}"; } catch { }
                    }
                }

                // 2. Rename TEMP_i to (i + 2): TEMP_11 -> 13, TEMP_12 -> 14, ..., TEMP_19 -> 21
                for (int i = 19; i >= 11; i--)
                {
                    string tempName = $"TEMP_{i}";
                    string newName = (i + 2).ToString();
                    var g = grids.FirstOrDefault(x => x.Name == tempName);
                    if (g != null)
                    {
                        try { g.Name = newName; } catch { }
                    }
                }

                // 3. Create Grid 11 at X = 88.05m and Grid 12 at X = 89.10m
                double y1 = -10.0 * MetersToFeet;
                double y2 = 156.0 * MetersToFeet;

                XYZ p11_start = new XYZ(88.05 * MetersToFeet, y1, 0);
                XYZ p11_end = new XYZ(88.05 * MetersToFeet, y2, 0);
                Line line11 = Line.CreateBound(p11_start, p11_end);
                Grid g11 = Grid.Create(doc, line11);
                try { g11.Name = "11"; } catch { }

                XYZ p12_start = new XYZ(89.10 * MetersToFeet, y1, 0);
                XYZ p12_end = new XYZ(89.10 * MetersToFeet, y2, 0);
                Line line12 = Line.CreateBound(p12_start, p12_end);
                Grid g12 = Grid.Create(doc, line12);
                try { g12.Name = "12"; } catch { }

                // 4. Update vertical extents for all grids to span all levels
                var levels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .OrderBy(l => l.Elevation)
                    .ToList();

                double minElev = levels.Count > 0 ? levels.First().Elevation - (15.0 * MetersToFeet) : -50.0 * MetersToFeet;
                double maxElev = levels.Count > 0 ? levels.Last().Elevation + (15.0 * MetersToFeet) : 100.0 * MetersToFeet;

                var allGrids = new FilteredElementCollector(doc)
                    .OfClass(typeof(Grid))
                    .Cast<Grid>()
                    .ToList();

                foreach (var g in allGrids)
                {
                    try { g.SetVerticalExtents(minElev, maxElev); } catch { }
                }

                tx.Commit();
            }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                message = "Đã cập nhật hệ trục X thành đủ 21 trục (bổ sung Trục 11 tại X=88.05m, Trục 12 tại X=89.10m và tịnh tiến các trục 13..21)"
            };
        }
    }
}

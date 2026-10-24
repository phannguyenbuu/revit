using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckStairCornerWalls
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find all walls near X in [29.0, 30.0], Y in [13.0, 15.0]
            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w =>
                {
                    var bb = w.get_BoundingBox(null);
                    if (bb == null) return false;
                    double minX = bb.Min.X * FT2M;
                    double maxX = bb.Max.X * FT2M;
                    double minY = bb.Min.Y * FT2M;
                    double maxY = bb.Max.Y * FT2M;
                    return maxX >= 29.0 && minX <= 30.5 && maxY >= 13.0 && minY <= 15.0;
                })
                .Select(w =>
                {
                    var lc = w.Location as LocationCurve;
                    var c = lc?.Curve;
                    var p0 = c?.GetEndPoint(0);
                    var p1 = c?.GetEndPoint(1);
                    return new
                    {
                        id = w.Id.Value,
                        name = w.WallType.Name,
                        widthMm = w.WallType.Width * FT2M * 1000.0,
                        p0 = p0 != null ? new { x = p0.X * FT2M, y = p0.Y * FT2M, z = p0.Z * FT2M } : null,
                        p1 = p1 != null ? new { x = p1.X * FT2M, y = p1.Y * FT2M, z = p1.Z * FT2M } : null
                    };
                })
                .ToList();

            // Find all WallTypes in doc, especially 100mm
            var types100 = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .Select(wt => new
                {
                    id = wt.Id.Value,
                    name = wt.Name,
                    kind = wt.Kind.ToString(),
                    widthMm = wt.Width * FT2M * 1000.0
                })
                .ToList();

            return new
            {
                nearbyWalls = walls,
                allWallTypes = types100
            };
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWall2362083
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var wall = doc.GetElement(new ElementId(2362083L)) as Wall;
            if (wall == null) return new { error = "Wall 2362083 not found" };

            var lc = wall.Location as LocationCurve;
            var c = lc?.Curve;
            var p0 = c?.GetEndPoint(0);
            var p1 = c?.GetEndPoint(1);

            var geom = wall.get_Geometry(new Options { DetailLevel = ViewDetailLevel.Fine });
            int solidCount = 0;
            double totalVolume = 0;
            if (geom != null)
            {
                foreach (var g in geom)
                {
                    if (g is Solid s && s.Volume > 0)
                    {
                        solidCount++;
                        totalVolume += s.Volume;
                    }
                }
            }

            var inserts = wall.FindInserts(true, true, true, true);
            var insertIds = new List<long>();
            foreach (var id in inserts)
            {
                insertIds.Add(id.Value);
            }

            return new
            {
                wallId = wall.Id.Value,
                p0 = p0 != null ? new { x = p0.X * 0.3048, y = p0.Y * 0.3048, z = p0.Z * 0.3048 } : null,
                p1 = p1 != null ? new { x = p1.X * 0.3048, y = p1.Y * 0.3048, z = p1.Z * 0.3048 } : null,
                length = c != null ? c.Length * 0.3048 : 0,
                solidCount = solidCount,
                volumeM3 = totalVolume * 0.028316846592,
                findInserts = insertIds
            };
        }
    }
}

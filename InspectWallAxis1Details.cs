using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWallAxis1Details
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var d1 = doc.GetElement(new ElementId(2364731L)) as FamilyInstance;
            var host = d1?.Host as Wall;
            if (host == null) return new { error = "Host wall not found" };

            var lc = host.Location as LocationCurve;
            var c = lc?.Curve;
            var bb = host.get_BoundingBox(null);
            double ft2mm = 304.8;
            return new {
                wallId = host.Id.Value,
                wallType = host.WallType.Name,
                widthMm = host.Width * ft2mm,
                p0 = c != null ? new { x = c.GetEndPoint(0).X * ft2mm, y = c.GetEndPoint(0).Y * ft2mm } : null,
                p1 = c != null ? new { x = c.GetEndPoint(1).X * ft2mm, y = c.GetEndPoint(1).Y * ft2mm } : null,
                bbMin = bb != null ? new { x = bb.Min.X * ft2mm, y = bb.Min.Y * ft2mm, z = bb.Min.Z * ft2mm } : null,
                bbMax = bb != null ? new { x = bb.Max.X * ft2mm, y = bb.Max.Y * ft2mm, z = bb.Max.Z * ft2mm } : null,
                orientation = new { x = host.Orientation.X, y = host.Orientation.Y, z = host.Orientation.Z }
            };
        }
    }
}

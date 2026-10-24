using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectD1ZoneElements
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find all elements whose bounding box intersects X in [-1, 2], Y in [4, 9]
            var elements = new FilteredElementCollector(doc)
                .WhereElementIsNotElementType()
                .Where(e =>
                {
                    var bb = e.get_BoundingBox(null);
                    if (bb == null) return false;
                    double minX = bb.Min.X * 0.3048, maxX = bb.Max.X * 0.3048;
                    double minY = bb.Min.Y * 0.3048, maxY = bb.Max.Y * 0.3048;

                    // overlap with [0, 1.5] x [5, 8]
                    bool overlapX = minX <= 1.5 && maxX >= 0.0;
                    bool overlapY = minY <= 8.0 && maxY >= 5.0;
                    return overlapX && overlapY;
                })
                .Select(e => new
                {
                    id = e.Id.Value,
                    cat = e.Category?.Name,
                    name = e.Name,
                    type = doc.GetElement(e.GetTypeId())?.Name,
                    bbMin = new { x = e.get_BoundingBox(null).Min.X * 0.3048, y = e.get_BoundingBox(null).Min.Y * 0.3048, z = e.get_BoundingBox(null).Min.Z * 0.3048 },
                    bbMax = new { x = e.get_BoundingBox(null).Max.X * 0.3048, y = e.get_BoundingBox(null).Max.Y * 0.3048, z = e.get_BoundingBox(null).Max.Z * 0.3048 }
                })
                .ToList();

            // Also check door 2363710 specifically
            var d2363710 = doc.GetElement(new ElementId(2363710L));
            object dInfo = null;
            if (d2363710 != null)
            {
                var fi = d2363710 as FamilyInstance;
                var bb = d2363710.get_BoundingBox(null);
                dInfo = new
                {
                    id = d2363710.Id.Value,
                    cat = d2363710.Category?.Name,
                    name = d2363710.Name,
                    host = fi?.Host?.Id.Value,
                    hostName = fi?.Host?.Name,
                    loc = fi?.Location != null ? fi.Location.GetType().FullName : "null",
                    facing = fi != null ? new { x = fi.FacingOrientation.X, y = fi.FacingOrientation.Y, z = fi.FacingOrientation.Z } : null,
                    hand = fi != null ? new { x = fi.HandOrientation.X, y = fi.HandOrientation.Y, z = fi.HandOrientation.Z } : null,
                    bbMin = bb != null ? new { x = bb.Min.X * 0.3048, y = bb.Min.Y * 0.3048, z = bb.Min.Z * 0.3048 } : null,
                    bbMax = bb != null ? new { x = bb.Max.X * 0.3048, y = bb.Max.Y * 0.3048, z = bb.Max.Z * 0.3048 } : null
                };
            }

            return new { dInfo, elements };
        }
    }
}

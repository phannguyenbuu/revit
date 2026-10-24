using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectColumn2361422
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var col = doc.GetElement(new ElementId(2361422)) as FamilyInstance;
            if (col == null) return new { error = "Col not found" };

            var bb = col.get_BoundingBox(null);
            var loc = col.Location as LocationPoint;

            return new
            {
                minX = bb.Min.X * 0.3048,
                minY = bb.Min.Y * 0.3048,
                maxX = bb.Max.X * 0.3048,
                maxY = bb.Max.Y * 0.3048,
                rotation = loc?.Rotation ?? 0,
                x = loc.Point.X * 0.3048,
                y = loc.Point.Y * 0.3048
            };
        }
    }
}

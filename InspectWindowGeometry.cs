using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowGeometry
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find a window instance
            var win = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .OfCategory(BuiltInCategory.OST_Windows)
                .Cast<FamilyInstance>()
                .FirstOrDefault();

            if (win == null) return new { error = "No window" };

            var hostWall = win.Host as Wall;
            var wbb = win.get_BoundingBox(null);
            var hostbb = hostWall?.get_BoundingBox(null);

            // Check parameters of window
            var pInfo = new List<object>();
            foreach (Parameter p in win.Symbol.Parameters)
            {
                if (p.HasValue && p.StorageType == StorageType.Double)
                {
                    pInfo.Add(new { name = p.Definition.Name, valMm = p.AsDouble() * 304.8 });
                }
            }

            // Check instance parameters
            var instInfo = new List<object>();
            foreach (Parameter p in win.Parameters)
            {
                if (p.HasValue && p.StorageType == StorageType.Double)
                {
                    instInfo.Add(new { name = p.Definition.Name, valMm = p.AsDouble() * 304.8 });
                }
            }

            return new
            {
                windowId = win.Id.Value,
                familyName = win.Symbol.FamilyName,
                typeName = win.Name,
                hostWallThickMm = (hostWall?.Width ?? 0) * 304.8,
                windowBB = wbb != null ? $"Min: [{wbb.Min.X*304.8:F1}, {wbb.Min.Y*304.8:F1}, {wbb.Min.Z*304.8:F1}] Max: [{wbb.Max.X*304.8:F1}, {wbb.Max.Y*304.8:F1}, {wbb.Max.Z*304.8:F1}]" : "null",
                typeParams = pInfo,
                instParams = instInfo
            };
        }
    }
}

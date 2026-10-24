using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectInst2363716
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var elem = doc.GetElement(new ElementId(2363716L));
            if (elem == null) return new { error = "Not found" };

            var fi = elem as FamilyInstance;
            var bb = elem.get_BoundingBox(null);

            return new
            {
                id = elem.Id.Value,
                locType = elem.Location?.GetType().FullName,
                bbMin = bb != null ? new { x = bb.Min.X * 0.3048, y = bb.Min.Y * 0.3048, z = bb.Min.Z * 0.3048 } : null,
                bbMax = bb != null ? new { x = bb.Max.X * 0.3048, y = bb.Max.Y * 0.3048, z = bb.Max.Z * 0.3048 } : null
            };
        }
    }
}

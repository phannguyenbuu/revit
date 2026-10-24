using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectViewFraming
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var viewIds = new List<long> { 312L, 695L, 1727632L, 2409349L };
            var results = new List<object>();

            var catElev = doc.Settings.Categories.get_Item(BuiltInCategory.OST_ElevationMarks);

            foreach (var id in viewIds)
            {
                var v = doc.GetElement(new ElementId(id)) as ViewPlan;
                if (v == null) continue;

                var bb = v.CropBox;
                bool isElevHidden = catElev != null ? v.GetCategoryHidden(catElev.Id) : false;

                results.Add(new
                {
                    id = id,
                    name = v.Name,
                    cropActive = v.CropBoxActive,
                    cropVisible = v.CropBoxVisible,
                    bbMin = bb != null ? new { x = bb.Min.X * 304.8, y = bb.Min.Y * 304.8, z = bb.Min.Z * 304.8 } : null,
                    bbMax = bb != null ? new { x = bb.Max.X * 304.8, y = bb.Max.Y * 304.8, z = bb.Max.Z * 304.8 } : null,
                    elevHidden = isElevHidden
                });
            }

            return new { success = true, results };
        }
    }
}

using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllMatTienInstances
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var instances = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Where(fi => {
                    var fn = fi.Symbol?.Family?.Name ?? "";
                    return fn.Contains("Mat_Tien", StringComparison.OrdinalIgnoreCase)
                        || fn.Contains("Sanh", StringComparison.OrdinalIgnoreCase);
                })
                .Select(fi => {
                    var lp = fi.Location as LocationPoint;
                    var bb = fi.get_BoundingBox(null);
                    return new {
                        id = fi.Id.Value,
                        name = fi.Name,
                        familyName = fi.Symbol.Family.Name,
                        point = lp != null ? $"({lp.Point.X * FT2MM:F1}, {lp.Point.Y * FT2MM:F1}, {lp.Point.Z * FT2MM:F1})" : "None",
                        bboxMin = bb != null ? $"({bb.Min.X * FT2MM:F1}, {bb.Min.Y * FT2MM:F1}, {bb.Min.Z * FT2MM:F1})" : "None",
                        bboxMax = bb != null ? $"({bb.Max.X * FT2MM:F1}, {bb.Max.Y * FT2MM:F1}, {bb.Max.Z * FT2MM:F1})" : "None"
                    };
                })
                .ToList();

            // Also check all Generic Model families and instances
            var allGenericModels = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_GenericModel)
                .WhereElementIsNotElementType()
                .Select(e => new {
                    id = e.Id.Value,
                    name = e.Name,
                    type = e.GetType().Name
                })
                .ToList();

            return new { count = instances.Count, instances, allGenericModelsCount = allGenericModels.Count, allGenericModels };
        }
    }
}

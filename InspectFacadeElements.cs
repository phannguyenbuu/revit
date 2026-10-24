using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFacadeElements
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active project document" };

            // Find all Generic Models and FamilyInstances near Axis 1 (X between -2000 and 3000 mm)
            var genericModels = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Where(fi => fi.Category != null && fi.Category.Id.Value == (long)BuiltInCategory.OST_GenericModel)
                .Select(fi => {
                    var bb = fi.get_BoundingBox(null);
                    return new {
                        id = fi.Id.Value,
                        fam = fi.Symbol?.Family?.Name,
                        sym = fi.Symbol?.Name,
                        min = bb != null ? $"({bb.Min.X * FT2MM:F1}, {bb.Min.Y * FT2MM:F1}, {bb.Min.Z * FT2MM:F1})" : "None",
                        max = bb != null ? $"({bb.Max.X * FT2MM:F1}, {bb.Max.Y * FT2MM:F1}, {bb.Max.Z * FT2MM:F1})" : "None"
                    };
                })
                .ToList();

            // Find all CAD imports in project
            var imports = new FilteredElementCollector(doc)
                .OfClass(typeof(ImportInstance))
                .Cast<ImportInstance>()
                .Select(ii => {
                    var bb = ii.get_BoundingBox(null);
                    return new {
                        id = ii.Id.Value,
                        isLinked = ii.IsLinked,
                        min = bb != null ? $"({bb.Min.X * FT2MM:F1}, {bb.Min.Y * FT2MM:F1}, {bb.Min.Z * FT2MM:F1})" : "None",
                        max = bb != null ? $"({bb.Max.X * FT2MM:F1}, {bb.Max.Y * FT2MM:F1}, {bb.Max.Z * FT2MM:F1})" : "None"
                    };
                })
                .ToList();

            return new { genericModels, imports };
        }
    }
}

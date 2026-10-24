using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSampleColumn
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var col = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .FirstOrDefault();

            if (col == null) return new { error = "No column found" };

            var loc = col.Location as LocationPoint;
            var pt = loc?.Point;
            var bb = col.get_BoundingBox(null);

            var pBase = col.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)?.AsValueString();
            var pTop = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)?.AsValueString();

            return new
            {
                id = col.Id.Value,
                symbol = col.Symbol.Name,
                family = col.Symbol.FamilyName,
                locationMeters = pt != null ? new double[] { pt.X * 0.3048, pt.Y * 0.3048, pt.Z * 0.3048 } : null,
                baseLevel = pBase,
                topLevel = pTop,
                bbMinMeters = bb != null ? new double[] { bb.Min.X * 0.3048, bb.Min.Y * 0.3048, bb.Min.Z * 0.3048 } : null,
                bbMaxMeters = bb != null ? new double[] { bb.Max.X * 0.3048, bb.Max.Y * 0.3048, bb.Max.Z * 0.3048 } : null,
                heightMeters = bb != null ? (bb.Max.Z - bb.Min.Z) * 0.3048 : 0
            };
        }
    }
}

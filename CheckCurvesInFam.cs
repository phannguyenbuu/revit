using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckCurvesInFam
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name.Equals("CUA SO 2 CANH NHOM KINH O O THOANG", StringComparison.OrdinalIgnoreCase));

            if (fam == null) return new { error = "Family not found" };

            var famDoc = doc.EditFamily(fam);
            if (famDoc == null) return new { error = "Cannot edit family" };

            var curves = new FilteredElementCollector(famDoc)
                .OfClass(typeof(CurveElement))
                .Cast<CurveElement>()
                .Select(c => new
                {
                    id = c.Id.Value,
                    type = c.GetType().Name,
                    lineStyle = c.LineStyle?.Name
                })
                .ToList();

            famDoc.Close(false);

            return new
            {
                totalCurves = curves.Count,
                curves
            };
        }
    }
}

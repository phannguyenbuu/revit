using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectErowdDetails
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active doc" };
            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name.Contains("EROWD (KO)"));
            if (fam == null) return new { error = "Family not found" };

            var famDoc = doc.EditFamily(fam);
            var curves = new FilteredElementCollector(famDoc)
                .OfClass(typeof(CurveElement))
                .Cast<CurveElement>()
                .Select(c => new {
                    type = c.GetType().Name,
                    subCat = c.LineStyle?.Name,
                    geom = c.GeometryCurve.GetType().Name,
                    p0 = c.GeometryCurve.IsBound ? $"({c.GeometryCurve.GetEndPoint(0).X * 304.8:F1}, {c.GeometryCurve.GetEndPoint(0).Y * 304.8:F1})" : "",
                    p1 = c.GeometryCurve.IsBound ? $"({c.GeometryCurve.GetEndPoint(1).X * 304.8:F1}, {c.GeometryCurve.GetEndPoint(1).Y * 304.8:F1})" : ""
                }).ToList();

            var forms = new FilteredElementCollector(famDoc)
                .OfClass(typeof(GenericForm))
                .Cast<GenericForm>()
                .Select(f => new { name = f.Name, type = f.GetType().Name, isSolid = f.IsSolid }).ToList();

            famDoc.Close(false);
            return new { famName = fam.Name, curveCount = curves.Count, curves = curves, forms = forms };
        }
    }
}

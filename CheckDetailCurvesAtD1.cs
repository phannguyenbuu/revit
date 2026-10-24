using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckDetailCurvesAtD1
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc.Document;
            var view = uidoc.ActiveView;

            var curves = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(CurveElement))
                .Cast<CurveElement>()
                .Where(c => c is DetailCurve || c is ModelCurve)
                .Select(c => new
                {
                    id = c.Id.Value,
                    type = c.GetType().Name,
                    lineStyle = c.LineStyle?.Name,
                    length = c.GeometryCurve.Length * 0.3048,
                    p0 = c.GeometryCurve.GetEndPoint(0).ToString(),
                    p1 = c.GeometryCurve.GetEndPoint(1).ToString()
                })
                .ToList();

            return new { count = curves.Count, curves = curves };
        }
    }
}

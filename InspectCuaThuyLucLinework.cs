using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCuaThuyLucLinework
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var sym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (sym == null) return new { error = "Symbol 104895 not found" };

            var fam = sym.Family;
            Document famDoc = null;
            try
            {
                famDoc = doc.EditFamily(fam);
                if (famDoc == null) return new { error = "Cannot edit family" };

                var curves = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(CurveElement))
                    .Cast<CurveElement>()
                    .Select(c =>
                    {
                        var gc = c.GeometryCurve;
                        string p0 = "unbound", p1 = "unbound";
                        if (gc.IsBound)
                        {
                            p0 = $"({gc.GetEndPoint(0).X * 304.8:F1}, {gc.GetEndPoint(0).Y * 304.8:F1}, {gc.GetEndPoint(0).Z * 304.8:F1})";
                            p1 = $"({gc.GetEndPoint(1).X * 304.8:F1}, {gc.GetEndPoint(1).Y * 304.8:F1}, {gc.GetEndPoint(1).Z * 304.8:F1})";
                        }
                        return new
                        {
                            id = c.Id.Value,
                            type = c.GetType().Name,
                            subCat = c.LineStyle?.Name,
                            geom = gc.GetType().Name,
                            len = gc.IsBound ? gc.Length * 304.8 : 0,
                            p0 = p0,
                            p1 = p1
                        };
                    })
                    .ToList();

                var forms = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(GenericForm))
                    .Cast<GenericForm>()
                    .Select(f => new { id = f.Id.Value, name = f.Name, type = f.GetType().Name, isSolid = f.IsSolid })
                    .ToList();

                famDoc.Close(false);

                return new
                {
                    familyName = fam.Name,
                    curveCount = curves.Count,
                    curves = curves,
                    forms = forms
                };
            }
            catch (Exception ex)
            {
                if (famDoc != null) try { famDoc.Close(false); } catch { }
                return new { error = ex.ToString() };
            }
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DeepInspectWindowFamily
    {
        private static double ToMm(double ft) => ft * 304.8;

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

            // 1. All GenericForms
            var forms = new FilteredElementCollector(famDoc)
                .OfClass(typeof(GenericForm))
                .Cast<GenericForm>()
                .Select(f =>
                {
                    var bb = f.get_BoundingBox(null);
                    return new
                    {
                        id = f.Id.Value,
                        name = f.Name,
                        type = f.GetType().Name,
                        subCat = f.Subcategory?.Name,
                        dx = bb != null ? ToMm(bb.Max.X - bb.Min.X) : 0,
                        dy = bb != null ? ToMm(bb.Max.Y - bb.Min.Y) : 0,
                        dz = bb != null ? ToMm(bb.Max.Z - bb.Min.Z) : 0,
                        zMin = bb != null ? ToMm(bb.Min.Z) : 0,
                        zMax = bb != null ? ToMm(bb.Max.Z) : 0
                    };
                })
                .ToList();

            // 2. All Model Curves
            var modelCurves = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ModelCurve))
                .Cast<ModelCurve>()
                .Select(c =>
                {
                    var l = c.GeometryCurve as Line;
                    return new
                    {
                        id = c.Id.Value,
                        subCat = c.Subcategory?.Name,
                        p0 = l != null ? new { x = ToMm(l.GetEndPoint(0).X), y = ToMm(l.GetEndPoint(0).Y), z = ToMm(l.GetEndPoint(0).Z) } : null,
                        p1 = l != null ? new { x = ToMm(l.GetEndPoint(1).X), y = ToMm(l.GetEndPoint(1).Y), z = ToMm(l.GetEndPoint(1).Z) } : null
                    };
                })
                .ToList();

            // 3. All Symbolic Curves
            var symCurves = new FilteredElementCollector(famDoc)
                .OfClass(typeof(SymbolicCurve))
                .Cast<SymbolicCurve>()
                .Select(c =>
                {
                    var l = c.GeometryCurve as Line;
                    return new
                    {
                        id = c.Id.Value,
                        subCat = c.Subcategory?.Name,
                        p0 = l != null ? new { x = ToMm(l.GetEndPoint(0).X), y = ToMm(l.GetEndPoint(0).Y), z = ToMm(l.GetEndPoint(0).Z) } : null,
                        p1 = l != null ? new { x = ToMm(l.GetEndPoint(1).X), y = ToMm(l.GetEndPoint(1).Y), z = ToMm(l.GetEndPoint(1).Z) } : null
                    };
                })
                .ToList();

            famDoc.Close(false);

            return new
            {
                familyName = fam.Name,
                forms,
                modelCurves,
                symCurves
            };
        }
    }
}

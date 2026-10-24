using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowFamilyElements
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find family CUA SO 2 CANH NHOM KINH O O THOANG
            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name.Equals("CUA SO 2 CANH NHOM KINH O O THOANG", StringComparison.OrdinalIgnoreCase));

            if (fam == null) return new { error = "Family not found" };

            var famDoc = doc.EditFamily(fam);
            if (famDoc == null) return new { error = "Cannot edit family" };

            var elements = new List<object>();

            // 1. Extrusions / Sweeps / Forms
            var forms = new FilteredElementCollector(famDoc)
                .OfClass(typeof(GenericForm))
                .Cast<GenericForm>()
                .ToList();

            foreach (var f in forms)
            {
                var bb = f.get_BoundingBox(null);
                string bbStr = bb != null 
                    ? $"min=({ToMm(bb.Min.X):F0}, {ToMm(bb.Min.Y):F0}, {ToMm(bb.Min.Z):F0}), max=({ToMm(bb.Max.X):F0}, {ToMm(bb.Max.Y):F0}, {ToMm(bb.Max.Z):F0}), dx={ToMm(bb.Max.X - bb.Min.X):F0}, dy={ToMm(bb.Max.Y - bb.Min.Y):F0}, dz={ToMm(bb.Max.Z - bb.Min.Z):F0}"
                    : "no bb";

                // Subcategory
                var subCat = f.Subcategory;
                var visParam = f.get_Parameter(BuiltInParameter.IS_VISIBLE_PARAM);

                elements.Add(new
                {
                    id = f.Id.Value,
                    type = f.GetType().Name,
                    name = f.Name,
                    isSolid = f.IsSolid,
                    subCat = subCat?.Name,
                    bb = bbStr,
                    dx = bb != null ? ToMm(bb.Max.X - bb.Min.X) : 0,
                    dy = bb != null ? ToMm(bb.Max.Y - bb.Min.Y) : 0,
                    dz = bb != null ? ToMm(bb.Max.Z - bb.Min.Z) : 0,
                    zMin = bb != null ? ToMm(bb.Min.Z) : 0,
                    zMax = bb != null ? ToMm(bb.Max.Z) : 0
                });
            }

            // 2. Nested FamilyInstances
            var nested = new FilteredElementCollector(famDoc)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Select(fi => new
                {
                    id = fi.Id.Value,
                    name = fi.Name,
                    family = fi.Symbol.FamilyName,
                    symbol = fi.Symbol.Name
                })
                .ToList();

            famDoc.Close(false);

            return new
            {
                familyName = fam.Name,
                formsCount = forms.Count,
                forms = elements,
                nested
            };
        }
    }
}

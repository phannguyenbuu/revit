using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckCurrentFamForms
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

            famDoc.Close(false);

            return new
            {
                familyName = fam.Name,
                formsCount = forms.Count,
                forms
            };
        }
    }
}

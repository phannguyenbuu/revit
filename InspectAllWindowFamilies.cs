using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllWindowFamilies
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var windowFams = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .Where(f => f.FamilyCategory != null && f.FamilyCategory.Id.Value == (long)BuiltInCategory.OST_Windows)
                .ToList();

            var famDetails = new List<object>();

            foreach (var fam in windowFams)
            {
                if (!fam.IsEditable) continue;

                Document famDoc = null;
                try
                {
                    famDoc = doc.EditFamily(fam);
                }
                catch
                {
                    continue;
                }

                if (famDoc == null) continue;

                var forms = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(GenericForm))
                    .Cast<GenericForm>()
                    .ToList();

                var formList = new List<object>();
                foreach (var f in forms)
                {
                    var bb = f.get_BoundingBox(null);
                    string bbStr = bb != null
                        ? $"dx={ToMm(bb.Max.X - bb.Min.X):F0}, dy={ToMm(bb.Max.Y - bb.Min.Y):F0}, dz={ToMm(bb.Max.Z - bb.Min.Z):F0}, zMin={ToMm(bb.Min.Z):F0}, zMax={ToMm(bb.Max.Z):F0}"
                        : "no bb";

                    formList.Add(new
                    {
                        id = f.Id.Value,
                        name = f.Name,
                        type = f.GetType().Name,
                        subCat = f.Subcategory?.Name,
                        bb = bbStr,
                        dz = bb != null ? ToMm(bb.Max.Z - bb.Min.Z) : 0,
                        dy = bb != null ? ToMm(bb.Max.Y - bb.Min.Y) : 0
                    });
                }

                famDoc.Close(false);

                famDetails.Add(new
                {
                    name = fam.Name,
                    forms = formList
                });
            }

            return new
            {
                families = famDetails
            };
        }
    }
}

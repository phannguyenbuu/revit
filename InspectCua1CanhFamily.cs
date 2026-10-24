using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCua1CanhFamily
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name == "cua 1 canh");

            if (fam == null) return new { error = "Family cua 1 canh not found" };

            var famDoc = doc.EditFamily(fam);
            if (famDoc == null) return new { error = "Cannot edit family" };

            var famParams = famDoc.FamilyManager.Parameters.Cast<FamilyParameter>()
                .Select(p => new {
                    name = p.Definition.Name,
                    isInstance = p.IsInstance,
                    storageType = p.StorageType.ToString()
                }).ToList();

            var types = famDoc.FamilyManager.Types.Cast<FamilyType>()
                .Select(t => {
                    var dict = new System.Collections.Generic.Dictionary<string, string>();
                    foreach (var p in famDoc.FamilyManager.Parameters.Cast<FamilyParameter>())
                    {
                        var val = t.AsValueString(p) ?? t.AsString(p) ?? (t.AsDouble(p).HasValue ? t.AsDouble(p).Value.ToString() : null);
                        if (!string.IsNullOrEmpty(val)) dict[p.Definition.Name] = val;
                    }
                    return new { name = t.Name, values = dict };
                }).ToList();

            famDoc.Close(false);

            return new { famParams, types };
        }
    }
}

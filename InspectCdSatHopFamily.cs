using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCdSatHopFamily
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name == "CD SAT HOP1 CANH");

            if (fam == null) return new { error = "Family CD SAT HOP1 CANH not found" };

            var famDoc = doc.EditFamily(fam);
            if (famDoc == null) return new { error = "Cannot edit family" };

            var famParams = famDoc.FamilyManager.Parameters.Cast<FamilyParameter>()
                .Select(p => new { name = p.Definition.Name, isInstance = p.IsInstance, storage = p.StorageType.ToString() })
                .ToList();

            var types = famDoc.FamilyManager.Types.Cast<FamilyType>()
                .Select(t => {
                    var dict = new Dictionary<string, string>();
                    foreach (var p in famDoc.FamilyManager.Parameters.Cast<FamilyParameter>())
                    {
                        var val = t.AsValueString(p) ?? t.AsString(p) ?? (t.AsDouble(p).HasValue ? t.AsDouble(p).Value.ToString() : null);
                        if (!string.IsNullOrEmpty(val)) dict[p.Definition.Name] = val;
                    }
                    return new { name = t.Name, values = dict };
                }).ToList();

            // Check symbolic lines in family
            var symLines = new FilteredElementCollector(famDoc)
                .OfClass(typeof(CurveElement))
                .Cast<CurveElement>()
                .Select(c => c.GetType().Name + " : " + c.LineStyle.Name)
                .Take(20)
                .ToList();

            famDoc.Close(false);

            return new { famParams, types, symLines };
        }
    }
}

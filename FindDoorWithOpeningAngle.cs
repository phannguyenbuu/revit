using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FindDoorWithOpeningAngle
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var fams = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .Where(f => f.FamilyCategory?.BuiltInCategory == BuiltInCategory.OST_Doors)
                .ToList();

            var matches = new List<object>();

            foreach (var fam in fams)
            {
                var famDoc = doc.EditFamily(fam);
                if (famDoc == null) continue;

                var interestingParams = famDoc.FamilyManager.Parameters.Cast<FamilyParameter>()
                    .Where(p => {
                        var n = p.Definition.Name.ToLower();
                        return n.Contains("mở") || n.Contains("mo") || n.Contains("angle") || n.Contains("goc") 
                            || n.Contains("gốc") || n.Contains("swing") || n.Contains("open") || n.Contains("%")
                            || n.Contains("cháy") || n.Contains("chay") || n.Contains("d7");
                    })
                    .Select(p => new {
                        name = p.Definition.Name,
                        isInstance = p.IsInstance,
                        type = p.StorageType.ToString()
                    })
                    .ToList();

                if (interestingParams.Count > 0)
                {
                    matches.Add(new {
                        familyName = fam.Name,
                        paramsFound = interestingParams
                    });
                }

                famDoc.Close(false);
            }

            return matches;
        }
    }
}

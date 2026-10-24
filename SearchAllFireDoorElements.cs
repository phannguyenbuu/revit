using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SearchAllFireDoorElements
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var fams = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .Where(f => {
                    var n = f.Name.ToLower();
                    return n.Contains("d7") || n.Contains("chay") || n.Contains("cháy") || n.Contains("fire") || n.Contains("sat") || n.Contains("sắt");
                })
                .Select(f => new { id = f.Id.Value, name = f.Name, cat = f.FamilyCategory?.Name })
                .ToList();

            var types = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .Where(s => {
                    var n = (s.FamilyName + " " + s.Name).ToLower();
                    return n.Contains("d7") || n.Contains("chay") || n.Contains("cháy") || n.Contains("fire") || n.Contains("sat") || n.Contains("sắt");
                })
                .Select(s => new { id = s.Id.Value, fam = s.FamilyName, sym = s.Name })
                .ToList();

            return new { fams, types };
        }
    }
}

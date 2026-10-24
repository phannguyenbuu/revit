using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectPlumbingFixtures
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active document" };

            // 1. Placed instances of PlumbingFixtures & SpecialityEquipment
            var placedPlumbing = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .WherePasses(new ElementMulticategoryFilter(new BuiltInCategory[] {
                    BuiltInCategory.OST_PlumbingFixtures,
                    BuiltInCategory.OST_SpecialityEquipment,
                    BuiltInCategory.OST_GenericModel
                }))
                .Cast<FamilyInstance>()
                .Where(fi => IsSanitary(fi.Symbol?.FamilyName, fi.Symbol?.Name, fi.Category?.Name))
                .Select(fi => new
                {
                    id = fi.Id.Value,
                    category = fi.Category?.Name,
                    familyName = fi.Symbol?.FamilyName,
                    symbolName = fi.Symbol?.Name,
                    level = doc.GetElement(fi.LevelId)?.Name ?? "none",
                    location = (fi.Location as LocationPoint)?.Point is XYZ p ? $"[{p.X * 304.8:F1}, {p.Y * 304.8:F1}, {p.Z * 304.8:F1}]" : "none"
                })
                .ToList();

            // 2. All loaded Family Symbols in project (even if 0 instances placed)
            var loadedSymbols = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilySymbol))
                .WherePasses(new ElementMulticategoryFilter(new BuiltInCategory[] {
                    BuiltInCategory.OST_PlumbingFixtures,
                    BuiltInCategory.OST_SpecialityEquipment
                }))
                .Cast<FamilySymbol>()
                .Select(fs => new
                {
                    id = fs.Id.Value,
                    category = fs.Category?.Name,
                    familyName = fs.FamilyName,
                    symbolName = fs.Name
                })
                .ToList();

            // Also check ANY family with sanitary keywords
            var allFamilies = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .Where(f => IsSanitary(f.Name, "", f.FamilyCategory?.Name))
                .Select(f => new
                {
                    id = f.Id.Value,
                    category = f.FamilyCategory?.Name,
                    name = f.Name
                })
                .ToList();

            return new
            {
                placedCount = placedPlumbing.Count,
                placed = placedPlumbing,
                loadedSymbolCount = loadedSymbols.Count,
                loadedSymbols = loadedSymbols,
                matchingFamilies = allFamilies
            };
        }

        private static bool IsSanitary(string famName, string symName, string catName)
        {
            string s = $"{famName} {symName} {catName}".ToLower();
            string[] keywords = new string[] {
                "plumbing", "toilet", "wc", "bệt", "xí", "bồn", "chậu", "lavabo", "sink", "tiểu", "urinal", "vệ sinh", "sanitary"
            };
            return keywords.Any(k => s.Contains(k));
        }
    }
}

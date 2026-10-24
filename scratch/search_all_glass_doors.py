import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

cs = """
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SearchAllGlassDoors
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var fams = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .Where(f =>
                {
                    string n = f.Name.ToLower();
                    return n.Contains("cua") || n.Contains("cửa") || n.Contains("door") || n.Contains("kinh") || n.Contains("kính") || n.Contains("thuy luc") || n.Contains("thủy lực") || n.Contains("hinge");
                })
                .Select(f => new
                {
                    id = f.Id.Value,
                    name = f.Name,
                    category = f.FamilyCategory?.Name,
                    placementType = f.FamilyPlacementType.ToString(),
                    symbols = f.GetFamilySymbolIds().Select(sid =>
                    {
                        var s = doc.GetElement(sid) as FamilySymbol;
                        return new { id = sid.Value, name = s?.Name };
                    }).ToList()
                })
                .ToList();

            return new { families = fams };
        }
    }
}
"""
print("CS defined")

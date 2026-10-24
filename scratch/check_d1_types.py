import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# We can query door symbols and their parameters via C#
cs_code = """
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectD1DoorTypes
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var symbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Where(s => s.Name.Contains("1") || s.FamilyName.Contains("thuy luc") || s.FamilyName.Contains("D1") || s.FamilyName.Contains("Đ1"))
                .Select(s => new
                {
                    id = s.Id.Value,
                    name = s.Name,
                    familyName = s.FamilyName,
                    parameters = s.Parameters.Cast<Parameter>()
                        .Where(p => p.Definition.Name.Contains("Width") || p.Definition.Name.Contains("Rộng") || p.Definition.Name.Contains("Height") || p.Definition.Name.Contains("Cao") || p.Definition.Name.Contains("b") || p.Definition.Name.Contains("h"))
                        .Select(p => new { name = p.Definition.Name, val = p.AsValueString() ?? p.AsDouble().ToString() })
                        .ToList()
                })
                .ToList();

            return new { symbols = symbols };
        }
    }
}
"""
print("Script defined")

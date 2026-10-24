import sys, urllib.request, json
sys.stdout.reconfigure(encoding='utf-8')

code = '''
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckColumnOrientation
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // Look at symbol 220X350
            var sym = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .FirstOrDefault(s => s.Name == "220X350");

            if (sym == null) return new { error = "Symbol 220X350 not found" };

            var pB = sym.LookupParameter("b");
            var pH = sym.LookupParameter("h");

            return new
            {
                symName = sym.Name,
                b_ft = pB?.AsDouble(),
                b_mm = pB?.AsDouble() * 304.8,
                h_ft = pH?.AsDouble(),
                h_mm = pH?.AsDouble() * 304.8
            };
        }
    }
}
'''
with open("CheckColumnOrientation.cs", "w", encoding="utf-8") as f:
    f.write(code)
print("Wrote CheckColumnOrientation.cs")

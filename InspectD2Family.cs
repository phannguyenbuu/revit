using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectD2Family
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var doorSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Select(s => new
                {
                    id = s.Id.Value,
                    name = s.Name,
                    familyName = s.FamilyName
                })
                .ToList();

            var winSymbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Select(s => new
                {
                    id = s.Id.Value,
                    name = s.Name,
                    familyName = s.FamilyName
                })
                .ToList();

            return new { doorSymbols, winSymbols };
        }
    }
}

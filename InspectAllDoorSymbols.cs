using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllDoorSymbols
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var symbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .Select(s => new {
                    id = s.Id.Value,
                    familyName = s.FamilyName,
                    symbolName = s.Name,
                    isActive = s.IsActive
                })
                .OrderBy(s => s.familyName)
                .ThenBy(s => s.symbolName)
                .ToList();

            // Also inspect the 2 selected doors parameters
            var selIds = new long[] { 2360900, 2360910 };
            var selectedDoors = selIds.Select(id => {
                var el = doc.GetElement(new ElementId(id)) as FamilyInstance;
                if (el == null) return null;
                var sym = el.Symbol;
                var instParams = el.Parameters.Cast<Parameter>().Select(p => new {
                    name = p.Definition.Name,
                    val = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString()
                }).Where(p => !string.IsNullOrEmpty(p.val)).ToList();

                var typeParams = sym.Parameters.Cast<Parameter>().Select(p => new {
                    name = p.Definition.Name,
                    val = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString()
                }).Where(p => !string.IsNullOrEmpty(p.val)).ToList();

                return new {
                    id = el.Id.Value,
                    family = sym.FamilyName,
                    symbol = sym.Name,
                    instParams,
                    typeParams
                };
            }).Where(x => x != null).ToList();

            return new { symbols, selectedDoors };
        }
    }
}

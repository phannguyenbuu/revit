using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DumpWindowParams
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var win = doc.GetElement(new ElementId(2361246L)) as FamilyInstance;
            if (win == null) return new { error = "Window 2361246 not found" };

            var instParams = win.Parameters.Cast<Parameter>()
                .Select(p => new
                {
                    name = p.Definition.Name,
                    val = p.StorageType == StorageType.Double ? ToMm(p.AsDouble()).ToString("F1") : p.AsValueString() ?? p.AsString(),
                    isReadOnly = p.IsReadOnly,
                    storage = p.StorageType.ToString()
                })
                .ToList();

            var symParams = win.Symbol.Parameters.Cast<Parameter>()
                .Select(p => new
                {
                    name = p.Definition.Name,
                    val = p.StorageType == StorageType.Double ? ToMm(p.AsDouble()).ToString("F1") : p.AsValueString() ?? p.AsString(),
                    isReadOnly = p.IsReadOnly,
                    storage = p.StorageType.ToString()
                })
                .ToList();

            // All types in this family
            var allTypes = win.Symbol.Family.GetFamilySymbolIds()
                .Select(id => doc.GetElement(id) as FamilySymbol)
                .Where(s => s != null)
                .Select(s => new
                {
                    id = s.Id.Value,
                    name = s.Name
                })
                .ToList();

            return new
            {
                symbolName = win.Symbol.Name,
                familyName = win.Symbol.FamilyName,
                allTypes,
                instParams,
                symParams
            };
        }
    }
}

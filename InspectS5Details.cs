using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectS5Details
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var win = doc.GetElement(new ElementId(2360987L)) as FamilyInstance;
            if (win == null) return new { error = "Not found" };

            var sym = win.Symbol;
            var symParams = sym.Parameters.Cast<Parameter>()
                .Select(p => new
                {
                    name = p.Definition.Name,
                    val = p.StorageType == StorageType.Double ? ToMm(p.AsDouble()).ToString("F1") : p.AsString(),
                    isReadOnly = p.IsReadOnly
                })
                .ToList();

            var types = sym.Family.GetFamilySymbolIds()
                .Select(id => doc.GetElement(id)?.Name)
                .ToList();

            return new { symName = sym.Name, famName = sym.FamilyName, types, symParams };
        }
    }
}

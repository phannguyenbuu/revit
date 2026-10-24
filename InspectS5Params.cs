using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectS5Params
    {
        private static double ToMm(double ft) => ft * 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var win = doc.GetElement(new ElementId(2360987L)) as FamilyInstance;
            if (win == null) return new { error = "Window 2360987 not found" };

            var symParams = win.Symbol.Parameters.Cast<Parameter>()
                .Where(p => anyKey(p.Definition.Name))
                .Select(p => new { name = p.Definition.Name, val = p.StorageType == StorageType.Double ? ToMm(p.AsDouble()).ToString("F1") : p.AsString() })
                .ToList();

            var instParams = win.Parameters.Cast<Parameter>()
                .Where(p => anyKey(p.Definition.Name))
                .Select(p => new { name = p.Definition.Name, val = p.StorageType == StorageType.Double ? ToMm(p.AsDouble()).ToString("F1") : p.AsString() })
                .ToList();

            return new { symName = win.Symbol.Name, famName = win.Symbol.FamilyName, symParams, instParams };
        }

        private static bool anyKey(string name)
        {
            string l = name.ToLower();
            return l.Contains("height") || l.Contains("cao") || l.Contains("width") || l.Contains("rộng") || l.Contains("sill");
        }
    }
}

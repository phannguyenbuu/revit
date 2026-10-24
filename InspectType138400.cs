using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectType138400
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var sym = doc.GetElement(new ElementId(138400L)) as FamilySymbol;
            if (sym == null) return new { error = "Symbol 138400 not found" };

            var pars = sym.Parameters.Cast<Parameter>()
                .Select(p => new
                {
                    name = p.Definition.Name,
                    valStr = p.AsValueString(),
                    valDbl = p.StorageType == StorageType.Double ? p.AsDouble() * 304.8 : 0
                })
                .Where(p => p.valStr != null || p.valDbl != 0)
                .ToList();

            return new
            {
                familyName = sym.FamilyName,
                name = sym.Name,
                parameters = pars
            };
        }
    }
}

using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCuaThuyLucDetails
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var sym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (sym == null) return new { error = "Symbol 104895 not found" };

            var pars = sym.Parameters.Cast<Parameter>()
                .Select(p => new
                {
                    name = p.Definition.Name,
                    storage = p.StorageType.ToString(),
                    val = p.StorageType == StorageType.Double ? p.AsDouble() * 304.8 : (p.StorageType == StorageType.String ? (object)p.AsString() : (object)p.AsInteger())
                })
                .ToList();

            // Also check Family itself
            var fam = sym.Family;
            var famPars = fam.Parameters.Cast<Parameter>()
                .Select(p => new { name = p.Definition.Name, val = p.AsValueString() })
                .ToList();

            return new
            {
                symName = sym.Name,
                familyName = fam.Name,
                symParams = pars,
                famParams = famPars
            };
        }
    }
}

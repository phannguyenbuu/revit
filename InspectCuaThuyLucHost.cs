using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCuaThuyLucHost
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var sym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (sym == null) return new { error = "Symbol 104895 not found" };

            var fam = sym.Family;

            return new
            {
                familyName = fam.Name,
                familyCategory = fam.FamilyCategory?.Name,
                placementType = fam.FamilyPlacementType.ToString(),
                isInPlace = fam.IsInPlace,
                isParametric = fam.IsParametric
            };
        }
    }
}

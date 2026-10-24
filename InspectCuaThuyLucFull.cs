using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCuaThuyLucFull
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var fam = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name.Equals("cua thuy luc 2 canh", StringComparison.OrdinalIgnoreCase));

            if (fam == null) return new { error = "cua thuy luc 2 canh not found" };

            var symbols = fam.GetFamilySymbolIds().Select(id =>
            {
                var s = doc.GetElement(id) as FamilySymbol;
                return new { id = id.Value, name = s.Name };
            }).ToList();

            var instances = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Where(fi => fi.Symbol != null && fi.Symbol.Family.Id == fam.Id)
                .Select(fi => new
                {
                    id = fi.Id.Value,
                    name = fi.Name,
                    mark = fi.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)?.AsString(),
                    level = fi.LevelId.Value,
                    host = fi.Host?.Id?.Value,
                    loc = fi.Location != null ? (fi.Location as LocationPoint)?.Point.ToString() : "none"
                })
                .ToList();

            return new
            {
                familyName = fam.Name,
                category = fam.FamilyCategory?.Name,
                placementType = fam.FamilyPlacementType.ToString(),
                symbols = symbols,
                instances = instances
            };
        }
    }
}

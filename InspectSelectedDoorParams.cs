using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSelectedDoorParams
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var doors = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .ToList();

            var angleDoors = new List<object>();

            foreach (var fs in doors)
            {
                var pars = fs.Parameters.Cast<Parameter>()
                    .Where(p => {
                        var n = p.Definition.Name.ToLower();
                        return n.Contains("angle") || n.Contains("goc") || n.Contains("góc") || n.Contains("mở") || n.Contains("mo") || n.Contains("swing") || n.Contains("open");
                    })
                    .Select(p => new { name = p.Definition.Name, val = p.AsValueString() ?? p.AsString() })
                    .ToList();

                if (pars.Count > 0)
                {
                    angleDoors.Add(new {
                        id = fs.Id.Value,
                        family = fs.FamilyName,
                        symbol = fs.Name,
                        paramsFound = pars
                    });
                }
            }

            return angleDoors;
        }
    }
}

using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCandidateFamilies
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var famNames = new string[] { "cua 1 canh", "CD SAT HOP1 CANH", "CD SAT HOP", "CD1C-EW-900X2200" };

            var result = new List<object>();
            foreach (var fn in famNames)
            {
                var fam = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .FirstOrDefault(f => f.Name == fn);

                if (fam == null)
                {
                    result.Add(new { name = fn, found = false, symbols = new List<object>() });
                    continue;
                }

                var symbols = new List<object>();
                foreach (var sid in fam.GetFamilySymbolIds())
                {
                    var s = doc.GetElement(sid) as FamilySymbol;
                    if (s == null) continue;

                    var typeParams = s.Parameters.Cast<Parameter>()
                        .Select(p => new { name = p.Definition.Name, val = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString() })
                        .Where(p => !string.IsNullOrEmpty(p.val))
                        .ToList();

                    symbols.Add(new
                    {
                        id = s.Id.Value,
                        name = s.Name,
                        width = s.get_Parameter(BuiltInParameter.DOOR_WIDTH)?.AsDouble() * 304.8,
                        height = s.get_Parameter(BuiltInParameter.DOOR_HEIGHT)?.AsDouble() * 304.8,
                        typeParams
                    });
                }

                result.Add(new { name = fn, found = true, symbols });
            }

            return result;
        }
    }
}

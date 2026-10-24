using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DumpAllDoorFamiliesParams
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var fams = new FilteredElementCollector(doc)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .Where(f => f.FamilyCategory?.BuiltInCategory == BuiltInCategory.OST_Doors)
                .ToList();

            var result = new List<object>();

            foreach (var fam in fams)
            {
                var symIds = fam.GetFamilySymbolIds();
                var sym = symIds.Count > 0 ? doc.GetElement(symIds.First()) as FamilySymbol : null;
                var paramNames = new List<string>();
                if (sym != null)
                {
                    foreach (Parameter p in sym.Parameters)
                    {
                        paramNames.Add(p.Definition.Name);
                    }
                }

                result.Add(new {
                    familyName = fam.Name,
                    symbolCount = symIds.Count,
                    parameters = paramNames
                });
            }

            return result;
        }
    }
}

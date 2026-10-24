using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllDoorWindowParameters
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var symbols = new FilteredElementCollector(doc)
                .WherePasses(new ElementMulticategoryFilter(new List<BuiltInCategory> { BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows }))
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .ToList();

            var list = new List<object>();
            foreach (var s in symbols)
            {
                var pMap = new Dictionary<string, string>();
                foreach (Parameter p in s.Parameters)
                {
                    if (p.HasValue)
                    {
                        string val = "";
                        switch (p.StorageType)
                        {
                            case StorageType.Double:
                                val = $"{p.AsDouble() * 304.8:F1} mm";
                                break;
                            case StorageType.Integer:
                                val = p.AsInteger().ToString();
                                break;
                            case StorageType.String:
                                val = p.AsString();
                                break;
                            case StorageType.ElementId:
                                val = p.AsElementId().Value.ToString();
                                break;
                        }
                        pMap[p.Definition.Name] = val;
                    }
                }

                list.Add(new
                {
                    cat = s.Category.Name,
                    family = s.FamilyName,
                    symbol = s.Name,
                    parameters = pMap
                });
            }

            return list;
        }
    }
}

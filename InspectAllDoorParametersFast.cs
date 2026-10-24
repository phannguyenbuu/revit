using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllDoorParametersFast
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var symbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilySymbol))
                .Cast<FamilySymbol>()
                .ToList();

            var famsDict = new Dictionary<string, List<string>>();

            foreach (var s in symbols)
            {
                var famName = s.FamilyName;
                if (!famsDict.ContainsKey(famName))
                {
                    famsDict[famName] = new List<string>();
                    foreach (Parameter p in s.Parameters)
                    {
                        var n = p.Definition.Name;
                        famsDict[famName].Add(n);
                    }
                }
            }

            var instances = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .ToList();

            var instParamDict = new Dictionary<string, List<string>>();
            foreach (var inst in instances)
            {
                var famName = inst.Symbol.FamilyName;
                if (!instParamDict.ContainsKey(famName))
                {
                    instParamDict[famName] = new List<string>();
                    foreach (Parameter p in inst.Parameters)
                    {
                        var n = p.Definition.Name;
                        instParamDict[famName].Add(n);
                    }
                }
            }

            return new { famsDict, instParamDict };
        }
    }
}

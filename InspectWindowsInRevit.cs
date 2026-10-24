using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindowsInRevit
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var symbols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsElementType()
                .Cast<FamilySymbol>()
                .Select(s =>
                {
                    double w = 0, h = 0;
                    var pW = s.get_Parameter(BuiltInParameter.WINDOW_WIDTH);
                    var pH = s.get_Parameter(BuiltInParameter.WINDOW_HEIGHT);
                    if (pW != null) w = pW.AsDouble() * 304.8;
                    if (pH != null) h = pH.AsDouble() * 304.8;

                    var tm = s.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString() ?? "";

                    return new
                    {
                        id = s.Id.Value,
                        family = s.FamilyName,
                        name = s.Name,
                        typeMark = tm,
                        widthMm = Math.Round(w, 1),
                        heightMm = Math.Round(h, 1)
                    };
                })
                .OrderBy(s => s.family).ThenBy(s => s.name)
                .ToList();

            var instances = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(i => new { id = i.Id.Value, name = i.Name, family = i.Symbol.FamilyName })
                .ToList();

            return new { symbols = symbols, existingCount = instances.Count };
        }
    }
}

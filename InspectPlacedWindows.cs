using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectPlacedWindows
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var wins = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(w =>
                {
                    var lp = (w.Location as LocationPoint)?.Point;
                    double sill = w.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.AsDouble() * 304.8 ?? 0;
                    double head = w.get_Parameter(BuiltInParameter.INSTANCE_HEAD_HEIGHT_PARAM)?.AsDouble() * 304.8 ?? 0;
                    var lvl = doc.GetElement(w.LevelId)?.Name ?? "";

                    return new
                    {
                        id = w.Id.Value,
                        symbolId = w.Symbol.Id.Value,
                        symbolName = w.Symbol.Name,
                        familyName = w.Symbol.FamilyName,
                        typeMark = w.Symbol.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)?.AsString() ?? "",
                        x = lp != null ? Math.Round(lp.X * 0.3048, 3) : 0,
                        y = lp != null ? Math.Round(lp.Y * 0.3048, 3) : 0,
                        z = lp != null ? Math.Round(lp.Z * 0.3048, 3) : 0,
                        level = lvl,
                        sillMm = Math.Round(sill, 0),
                        headMm = Math.Round(head, 0)
                    };
                })
                .ToList();

            return new { count = wins.Count, windows = wins };
        }
    }
}

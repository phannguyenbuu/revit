using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTop1500Cols
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active doc" };

            var cols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(c => {
                    var pTopOff = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                    return pTopOff != null && Math.Abs(pTopOff.AsDouble() * FT2MM - 1500) < 50;
                })
                .Select(c => {
                    var lp = c.Location as LocationPoint;
                    var pBase = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                    var pTop = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                    return new {
                        id = c.Id.Value,
                        name = c.Name,
                        baseLvl = pBase != null ? doc.GetElement(pBase.AsElementId())?.Name : "N/A",
                        topLvl = pTop != null ? doc.GetElement(pTop.AsElementId())?.Name : "N/A",
                        point = lp != null ? $"({lp.Point.X * FT2MM:F1}, {lp.Point.Y * FT2MM:F1}, {lp.Point.Z * FT2MM:F1})" : "None"
                    };
                })
                .ToList();

            return new { count = cols.Count, cols };
        }
    }
}

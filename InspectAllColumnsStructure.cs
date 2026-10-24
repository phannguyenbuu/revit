using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAllColumnsStructure
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var cols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(c => {
                    var bLvl = doc.GetElement(c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)?.AsElementId()) as Level;
                    var tLvl = doc.GetElement(c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)?.AsElementId()) as Level;
                    var bOff = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM)?.AsDouble() * FT2M * 1000 ?? 0;
                    var tOff = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)?.AsDouble() * FT2M * 1000 ?? 0;
                    var lp = c.Location as LocationPoint;
                    return new {
                        id = c.Id.Value,
                        name = c.Name,
                        baseLevel = bLvl?.Name,
                        topLevel = tLvl?.Name,
                        topElevM = (tLvl?.Elevation ?? 0) * FT2M,
                        topOffsetMm = Math.Round(tOff, 1),
                        x = Math.Round(lp.Point.X * FT2M * 1000, 1),
                        y = Math.Round(lp.Point.Y * FT2M * 1000, 1)
                    };
                })
                .OrderBy(c => c.x).ThenBy(c => c.y).ThenBy(c => c.id)
                .ToList();

            return new { count = cols.Count, cols };
        }
    }
}

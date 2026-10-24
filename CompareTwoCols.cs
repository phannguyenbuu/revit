using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CompareTwoCols
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var c1 = doc.GetElement(new ElementId(2361390L)) as FamilyInstance;
            var c2 = doc.GetElement(new ElementId(2379835L)) as FamilyInstance;

            var getInfo = new Func<FamilyInstance, object>(c => {
                if (c == null) return null;
                var bLvl = doc.GetElement(c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)?.AsElementId()) as Level;
                var tLvl = doc.GetElement(c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)?.AsElementId()) as Level;
                var bOff = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM)?.AsDouble() * FT2M * 1000 ?? 0;
                var tOff = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)?.AsDouble() * FT2M * 1000 ?? 0;
                var lp = c.Location as LocationPoint;

                return new {
                    id = c.Id.Value,
                    cat = c.Category?.Name,
                    name = c.Name,
                    family = c.Symbol?.FamilyName,
                    baseLevel = bLvl?.Name,
                    baseElevM = (bLvl?.Elevation ?? 0) * FT2M,
                    baseOffsetMm = Math.Round(bOff, 1),
                    topLevel = tLvl?.Name,
                    topElevM = (tLvl?.Elevation ?? 0) * FT2M,
                    topOffsetMm = Math.Round(tOff, 1),
                    x = Math.Round(lp.Point.X * FT2M * 1000, 1),
                    y = Math.Round(lp.Point.Y * FT2M * 1000, 1),
                    z = Math.Round(lp.Point.Z * FT2M * 1000, 1)
                };
            });

            return new { col1 = getInfo(c1), col2 = getInfo(c2) };
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTumWallsHeight
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var w = doc.GetElement(new ElementId(2370733L)) as Wall;
            var topLvlId = w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsElementId();
            var topLvl = topLvlId != null && topLvlId != ElementId.InvalidElementId ? doc.GetElement(topLvlId) as Level : null;
            var topOffset = w.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.AsDouble() * FT2M * 1000 ?? 0;
            var unconnectedHeight = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() * FT2M * 1000 ?? 0;

            var baseLvlId = w.LevelId;
            var baseLvl = doc.GetElement(baseLvlId) as Level;
            var baseOffset = w.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)?.AsDouble() * FT2M * 1000 ?? 0;

            var lvlMai = doc.GetElement(new ElementId(1209118L)) as Level;

            var plans = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate)
                .Select(v => new { id = v.Id.Value, name = v.Name, level = v.GenLevel?.Name })
                .ToList();

            return new
            {
                wallBaseLevel = baseLvl?.Name,
                wallBaseElevM = (baseLvl?.Elevation ?? 0) * FT2M,
                baseOffsetMm = baseOffset,
                wallTopLevel = topLvl?.Name,
                wallTopElevM = (topLvl?.Elevation ?? 0) * FT2M,
                topOffsetMm = topOffset,
                unconnectedHeightMm = unconnectedHeight,
                lvlMaiName = lvlMai?.Name,
                lvlMaiElevM = (lvlMai?.Elevation ?? 0) * FT2M,
                plans
            };
        }
    }
}

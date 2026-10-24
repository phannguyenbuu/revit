using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWallsByLevel
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Select(w => {
                    var bLvl = doc.GetElement(w.LevelId) as Level;
                    var tLvlId = w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsElementId();
                    var tLvl = tLvlId != null && tLvlId != ElementId.InvalidElementId ? doc.GetElement(tLvlId) as Level : null;
                    var topOff = w.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.AsDouble() * FT2M * 1000 ?? 0;
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        baseLevel = bLvl?.Name,
                        baseElevM = (bLvl?.Elevation ?? 0) * FT2M,
                        topLevel = tLvl?.Name,
                        topElevM = (tLvl?.Elevation ?? 0) * FT2M,
                        topOffsetMm = Math.Round(topOff, 1)
                    };
                })
                .ToList();

            var grouped = walls
                .GroupBy(w => w.baseLevel ?? "None")
                .Select(g => new {
                    baseLevel = g.Key,
                    count = g.Count(),
                    topOffsets = g.Select(w => w.topOffsetMm).Distinct().ToList()
                })
                .ToList();

            return new { totalWalls = walls.Count, grouped };
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSelectedColumn
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var selIds = uidoc.Selection.GetElementIds();
            if (selIds.Count == 0) return new { error = "No element selected" };

            var allLevels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new { id = l.Id.Value, name = l.Name, elevM = Math.Round(l.Elevation * FT2M, 3) })
                .ToList();

            var list = new List<object>();
            foreach (var id in selIds)
            {
                var elem = doc.GetElement(id);
                if (elem == null) continue;

                // Base level
                var baseLvlParam = elem.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)
                                ?? elem.get_Parameter(BuiltInParameter.COLUMN_LOCATION_MARK); // check also standard
                var baseLvlId = elem.LevelId;
                if (elem is FamilyInstance fi)
                {
                    // For structural columns
                    var bLvl = elem.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM)?.AsElementId();
                    var tLvl = elem.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)?.AsElementId();
                    var bOff = elem.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM)?.AsDouble() * FT2M * 1000 ?? 0;
                    var tOff = elem.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)?.AsDouble() * FT2M * 1000 ?? 0;

                    var bElem = bLvl != null && bLvl != ElementId.InvalidElementId ? doc.GetElement(bLvl) as Level : null;
                    var tElem = tLvl != null && tLvl != ElementId.InvalidElementId ? doc.GetElement(tLvl) as Level : null;

                    var lp = fi.Location as LocationPoint;

                    list.Add(new
                    {
                        id = id.Value,
                        cat = elem.Category?.Name,
                        name = elem.Name,
                        symbol = fi.Symbol?.Name,
                        family = fi.Symbol?.FamilyName,
                        baseLevel = bElem?.Name,
                        baseLevelId = bElem?.Id.Value,
                        baseElevM = (bElem?.Elevation ?? 0) * FT2M,
                        baseOffsetMm = Math.Round(bOff, 1),
                        topLevel = tElem?.Name,
                        topLevelId = tElem?.Id.Value,
                        topElevM = (tElem?.Elevation ?? 0) * FT2M,
                        topOffsetMm = Math.Round(tOff, 1),
                        loc = lp != null ? new { xMm = Math.Round(lp.Point.X * FT2M * 1000, 1), yMm = Math.Round(lp.Point.Y * FT2M * 1000, 1), zMm = Math.Round(lp.Point.Z * FT2M * 1000, 1) } : null
                    });
                }
                else
                {
                    list.Add(new
                    {
                        id = id.Value,
                        cat = elem.Category?.Name,
                        name = elem.Name,
                        type = elem.GetType().Name
                    });
                }
            }

            return new { selectedCount = selIds.Count, elements = list, allLevels };
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectColumnLevelsAll
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var cols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            var list = cols.Select(c =>
            {
                var pBase = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                var pTop = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                var pBaseOff = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM);
                var pTopOff = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);

                var baseElem = pBase != null && pBase.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pBase.AsElementId()) : null;
                var topElem = pTop != null && pTop.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pTop.AsElementId()) : null;

                var lp = c.Location as LocationPoint;

                return new
                {
                    id = c.Id.Value,
                    name = c.Name,
                    baseLevel = baseElem?.Name,
                    baseLevelId = baseElem?.Id.Value,
                    topLevel = topElem?.Name,
                    topLevelId = topElem?.Id.Value,
                    baseOffset = pBaseOff?.AsDouble() * 304.8,
                    topOffset = pTopOff?.AsDouble() * 304.8,
                    x = lp != null ? Math.Round(lp.Point.X * 0.3048, 3) : 0,
                    y = lp != null ? Math.Round(lp.Point.Y * 0.3048, 3) : 0,
                    z = lp != null ? Math.Round(lp.Point.Z * 0.3048, 3) : 0
                };
            }).ToList();

            // Group by base/top
            var groups = list.GroupBy(c => $"{c.baseLevel} -> {c.topLevel} (topOff={c.topOffset})")
                .Select(g => new { key = g.Key, count = g.Count() })
                .ToList();

            return new
            {
                total = cols.Count,
                groups,
                firstThree = list.Take(3).ToList()
            };
        }
    }
}

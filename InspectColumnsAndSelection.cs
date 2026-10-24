using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectColumnsAndSelection
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // 1. Inspect selection
            var selIds = uidoc.Selection.GetElementIds();
            var selInfo = new List<object>();
            foreach (var id in selIds)
            {
                var elem = doc.GetElement(id);
                if (elem == null) continue;
                var bb = elem.get_BoundingBox(null);
                var lp = elem.Location as LocationPoint;

                var pLevel = elem.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM)
                          ?? elem.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)
                          ?? elem.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                var pOffset = elem.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
                           ?? elem.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM);

                selInfo.Add(new
                {
                    id = id.Value,
                    name = elem.Name,
                    category = elem.Category?.Name,
                    level = pLevel != null ? doc.GetElement(pLevel.AsElementId())?.Name : "N/A",
                    offset = pOffset != null ? Math.Round(pOffset.AsDouble() * FT2MM, 1) : 0.0,
                    point = lp != null ? $"({lp.Point.X * FT2MM:F1}, {lp.Point.Y * FT2MM:F1}, {lp.Point.Z * FT2MM:F1})" : "None",
                    bboxMin = bb != null ? $"({bb.Min.X * FT2MM:F1}, {bb.Min.Y * FT2MM:F1}, {bb.Min.Z * FT2MM:F1})" : "None",
                    bboxMax = bb != null ? $"({bb.Max.X * FT2MM:F1}, {bb.Max.Y * FT2MM:F1}, {bb.Max.Z * FT2MM:F1})" : "None"
                });
            }

            // 2. Inspect Structural Columns
            var structCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            // 3. Inspect Architectural Columns
            var archCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Columns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            var structColSummary = structCols.GroupBy(c => {
                var pTop = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                var topName = pTop != null && pTop.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pTop.AsElementId())?.Name : "NoTop";
                var pTopOff = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                var topOff = pTopOff != null ? Math.Round(pTopOff.AsDouble() * FT2MM, 1) : 0.0;
                var pBase = c.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                var baseName = pBase != null && pBase.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pBase.AsElementId())?.Name : "NoBase";
                return $"{baseName} -> {topName} (TopOffset={topOff}mm)";
            }).Select(g => new { config = g.Key, count = g.Count() }).ToList();

            var archColSummary = archCols.GroupBy(c => {
                var pTop = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                var topName = pTop != null && pTop.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pTop.AsElementId())?.Name : "NoTop";
                var pTopOff = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                var topOff = pTopOff != null ? Math.Round(pTopOff.AsDouble() * FT2MM, 1) : 0.0;
                return $"{topName} (TopOffset={topOff}mm)";
            }).Select(g => new { config = g.Key, count = g.Count() }).ToList();

            return new
            {
                selection = selInfo,
                totalStructuralColumns = structCols.Count,
                structColSummary,
                totalArchitecturalColumns = archCols.Count,
                archColSummary
            };
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectElementsForHeight12300
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // 1. Current selection
            var selIds = uidoc.Selection.GetElementIds().Select(id => id.Value).ToList();

            // 2. All levels in the project
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new
                {
                    id = l.Id.Value,
                    name = l.Name,
                    elevM = Math.Round(l.Elevation * FT2M, 3)
                })
                .ToList();

            // 3. Inspect specific candidate IDs
            long[] candidateIds = new long[]
            {
                2361516L, 2361585L, 2361586L, 2361587L,
                2368948L, 2360649L, 2368959L, 2360646L
            };

            var inspectedCandidates = new List<object>();
            foreach (var cid in candidateIds)
            {
                var elem = doc.GetElement(new ElementId(cid));
                if (elem == null) continue;
                inspectedCandidates.Add(InspectElement(doc, elem));
            }

            // 4. Also inspect any columns near Axis 11 or near these walls
            var allCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(c => InspectElement(doc, c))
                .ToList();

            var allArchCols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Columns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(c => InspectElement(doc, c))
                .ToList();

            return new
            {
                selectedIds = selIds,
                levels,
                inspectedCandidates,
                structuralColumnsCount = allCols.Count,
                architecturalColumnsCount = allArchCols.Count,
                structuralColumns = allCols,
                architecturalColumns = allArchCols
            };
        }

        private static object InspectElement(Document doc, Element elem)
        {
            var pBase = elem.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM) 
                     ?? elem.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT);
            var pBaseOff = elem.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM)
                        ?? elem.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
            var pTop = elem.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM)
                    ?? elem.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
            var pTopOff = elem.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM)
                       ?? elem.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET);
            var pHeight = elem.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);

            var baseLvl = pBase != null && pBase.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pBase.AsElementId()) as Level : null;
            var topLvl = pTop != null && pTop.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pTop.AsElementId()) as Level : null;

            XYZ locationPt = null;
            if (elem.Location is LocationPoint lp) locationPt = lp.Point;
            else if (elem.Location is LocationCurve lc) locationPt = lc.Curve.GetEndPoint(0);

            var allParams = new Dictionary<string, string>();
            foreach (Parameter p in elem.Parameters)
            {
                if (p.Definition.Name.Contains("Height", StringComparison.OrdinalIgnoreCase) ||
                    p.Definition.Name.Contains("Cao", StringComparison.OrdinalIgnoreCase) ||
                    p.Definition.Name.Contains("Level", StringComparison.OrdinalIgnoreCase) ||
                    p.Definition.Name.Contains("Offset", StringComparison.OrdinalIgnoreCase) ||
                    p.Definition.Name.Contains("Length", StringComparison.OrdinalIgnoreCase))
                {
                    allParams[p.Definition.Name] = p.AsValueString() ?? p.AsString() ?? p.AsDouble().ToString();
                }
            }

            return new
            {
                id = elem.Id.Value,
                name = elem.Name,
                category = elem.Category?.Name,
                baseLevel = baseLvl?.Name,
                baseElevM = baseLvl != null ? Math.Round(baseLvl.Elevation * FT2M, 3) : 0,
                baseOffsetMm = pBaseOff != null ? Math.Round(pBaseOff.AsDouble() * FT2M * 1000, 1) : 0,
                topLevel = topLvl?.Name,
                topElevM = topLvl != null ? Math.Round(topLvl.Elevation * FT2M, 3) : 0,
                topOffsetMm = pTopOff != null ? Math.Round(pTopOff.AsDouble() * FT2M * 1000, 1) : 0,
                unconnectedHeightMm = pHeight != null ? Math.Round(pHeight.AsDouble() * FT2M * 1000, 1) : 0,
                loc = locationPt != null ? new { x = Math.Round(locationPt.X * FT2M * 1000, 1), y = Math.Round(locationPt.Y * FT2M * 1000, 1), z = Math.Round(locationPt.Z * FT2M * 1000, 1) } : null,
                relevantParams = allParams
            };
        }
    }
}

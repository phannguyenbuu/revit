using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectAndAdjustSelectedWalls
    {
        private const double FT2M = 0.3048;
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            var selIds = uidoc.Selection.GetElementIds().ToList();
            if (selIds.Count == 0) return new { error = "No selection in Revit" };

            var items = new List<object>();

            foreach (var id in selIds)
            {
                var elem = doc.GetElement(id);
                if (elem == null) continue;

                var wall = elem as Wall;
                var pBase = elem.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT);
                var pBaseOff = elem.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
                var pTop = elem.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                var pTopOff = elem.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET);
                var pUnconnected = elem.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);

                var baseLvl = pBase != null && pBase.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pBase.AsElementId()) as Level : null;
                var topLvl = pTop != null && pTop.AsElementId() != ElementId.InvalidElementId ? doc.GetElement(pTop.AsElementId()) as Level : null;

                var locCurve = wall?.Location as LocationCurve;
                XYZ ptStart = locCurve?.Curve.GetEndPoint(0);
                XYZ ptEnd = locCurve?.Curve.GetEndPoint(1);

                items.Add(new
                {
                    id = id.Value,
                    category = elem.Category?.Name,
                    wallType = wall?.WallType.Name,
                    baseConstraint = baseLvl?.Name,
                    baseConstraintId = baseLvl?.Id.Value,
                    baseElevM = baseLvl != null ? Math.Round(baseLvl.Elevation * FT2M, 3) : 0,
                    baseOffsetMm = pBaseOff != null ? Math.Round(pBaseOff.AsDouble() * FT2M * 1000, 1) : 0,
                    topConstraint = topLvl?.Name,
                    topConstraintId = topLvl?.Id.Value,
                    topElevM = topLvl != null ? Math.Round(topLvl.Elevation * FT2M, 3) : 0,
                    topOffsetMm = pTopOff != null ? Math.Round(pTopOff.AsDouble() * FT2M * 1000, 1) : 0,
                    unconnectedHeightMm = pUnconnected != null ? Math.Round(pUnconnected.AsDouble() * FT2M * 1000, 1) : 0,
                    startPt = ptStart != null ? new { x = Math.Round(ptStart.X * FT2M * 1000, 1), y = Math.Round(ptStart.Y * FT2M * 1000, 1), z = Math.Round(ptStart.Z * FT2M * 1000, 1) } : null,
                    endPt = ptEnd != null ? new { x = Math.Round(ptEnd.X * FT2M * 1000, 1), y = Math.Round(ptEnd.Y * FT2M * 1000, 1), z = Math.Round(ptEnd.Z * FT2M * 1000, 1) } : null
                });
            }

            return new
            {
                selectedCount = selIds.Count,
                elements = items
            };
        }
    }
}

using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSelectedWallAndHosted
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var selIds = uidoc.Selection.GetElementIds();
            var wallId = selIds.FirstOrDefault();
            if (wallId == null) wallId = new ElementId(2369928L);

            var wall = doc.GetElement(wallId) as Wall;
            if (wall == null) return new { error = "Wall not found: " + wallId.Value };

            var lc = wall.Location as LocationCurve;
            var curve = lc?.Curve;
            var p0 = curve?.GetEndPoint(0);
            var p1 = curve?.GetEndPoint(1);

            // Hosted elements (Windows, Doors, Openings)
            var hostedInserts = wall.FindInserts(true, true, true, true);
            var inserts = new List<object>();
            foreach (var insId in hostedInserts)
            {
                var elem = doc.GetElement(insId);
                var bb = elem.get_BoundingBox(null);
                var lp = elem.Location as LocationPoint;
                var sym = (elem as FamilyInstance)?.Symbol;
                inserts.Add(new
                {
                    id = insId.Value,
                    name = elem.Name,
                    category = elem.Category?.Name,
                    type = elem.GetType().Name,
                    familyName = sym?.Family?.Name,
                    symbolName = sym?.Name,
                    point = lp != null ? $"({lp.Point.X * FT2MM:F1}, {lp.Point.Y * FT2MM:F1}, {lp.Point.Z * FT2MM:F1})" : "None",
                    bboxMin = bb != null ? $"({bb.Min.X * FT2MM:F1}, {bb.Min.Y * FT2MM:F1}, {bb.Min.Z * FT2MM:F1})" : "None",
                    bboxMax = bb != null ? $"({bb.Max.X * FT2MM:F1}, {bb.Max.Y * FT2MM:F1}, {bb.Max.Z * FT2MM:F1})" : "None"
                });
            }

            // Also check dependent elements
            var depIds = wall.GetDependentElements(new ElementClassFilter(typeof(FamilyInstance)));
            var deps = new List<object>();
            foreach (var dId in depIds)
            {
                var elem = doc.GetElement(dId);
                deps.Add(new { id = dId.Value, name = elem?.Name, cat = elem?.Category?.Name });
            }

            // Parameters
            var pBase = doc.GetElement(wall.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsElementId())?.Name;
            var pBaseOff = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)?.AsDouble() * FT2MM;
            var pTopId = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsElementId();
            var pTop = pTopId != null && pTopId != ElementId.InvalidElementId ? doc.GetElement(pTopId)?.Name : "Unconnected";
            var pTopOff = wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.AsDouble() * FT2MM;
            var pHeight = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() * FT2MM;

            // Check walls along same axis across all levels
            // X is around 550, Y is around 5400 to 7900
            var allLevels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new { id = l.Id.Value, name = l.Name, elevMm = l.Elevation * FT2MM })
                .ToList();

            var similarWalls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => {
                    var wlc = w.Location as LocationCurve;
                    if (wlc == null) return false;
                    var c = wlc.Curve;
                    var pt0 = c.GetEndPoint(0) * FT2MM;
                    var pt1 = c.GetEndPoint(1) * FT2MM;
                    double midX = (pt0.X + pt1.X) * 0.5;
                    double midY = (pt0.Y + pt1.Y) * 0.5;
                    return Math.Abs(midX - 550.0) < 200.0 && Math.Abs(midY - 6650.0) < 1500.0;
                })
                .Select(w => {
                    var wbb = w.get_BoundingBox(null);
                    var bName = doc.GetElement(w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsElementId())?.Name;
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        baseLevel = bName,
                        bboxMinZ = wbb != null ? wbb.Min.Z * FT2MM : 0,
                        bboxMaxZ = wbb != null ? wbb.Max.Z * FT2MM : 0,
                        height = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() * FT2MM
                    };
                })
                .ToList();

            // Check beams along this bay
            var beams = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralFraming)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Where(b => {
                    var blc = b.Location as LocationCurve;
                    if (blc == null) return false;
                    var bc = blc.Curve;
                    var b0 = bc.GetEndPoint(0) * FT2MM;
                    var b1 = bc.GetEndPoint(1) * FT2MM;
                    double midX = (b0.X + b1.X) * 0.5;
                    double midY = (b0.Y + b1.Y) * 0.5;
                    return Math.Abs(midX - 550.0) < 500.0;
                })
                .Select(b => {
                    var bbb = b.get_BoundingBox(null);
                    var bLvl = doc.GetElement(b.LevelId)?.Name;
                    return new {
                        id = b.Id.Value,
                        name = b.Name,
                        level = bLvl,
                        bboxMinZ = bbb != null ? bbb.Min.Z * FT2MM : 0,
                        bboxMaxZ = bbb != null ? bbb.Max.Z * FT2MM : 0
                    };
                })
                .ToList();

            return new
            {
                wall = new
                {
                    id = wall.Id.Value,
                    name = wall.Name,
                    wallType = wall.WallType.Name,
                    p0 = p0 != null ? $"({p0.X * FT2MM:F1}, {p0.Y * FT2MM:F1}, {p0.Z * FT2MM:F1})" : "None",
                    p1 = p1 != null ? $"({p1.X * FT2MM:F1}, {p1.Y * FT2MM:F1}, {p1.Z * FT2MM:F1})" : "None",
                    baseConstraint = pBase,
                    baseOffsetMm = pBaseOff,
                    topConstraint = pTop,
                    topOffsetMm = pTopOff,
                    heightMm = pHeight
                },
                inserts,
                deps,
                allLevels,
                similarWalls,
                beams
            };
        }
    }
}

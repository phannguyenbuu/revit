using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDetailedElements
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Floors
            var floors = new FilteredElementCollector(doc)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .Select(f => {
                    var lvl = doc.GetElement(f.LevelId) as Level;
                    var bb = f.get_BoundingBox(null);
                    return new {
                        id = f.Id.Value,
                        name = f.Name,
                        level = lvl?.Name,
                        elevM = (lvl?.Elevation ?? 0) * FT2M,
                        minX = Math.Round((bb?.Min.X ?? 0) * FT2M * 1000, 1),
                        maxX = Math.Round((bb?.Max.X ?? 0) * FT2M * 1000, 1),
                        minY = Math.Round((bb?.Min.Y ?? 0) * FT2M * 1000, 1),
                        maxY = Math.Round((bb?.Max.Y ?? 0) * FT2M * 1000, 1),
                        minZ = Math.Round((bb?.Min.Z ?? 0) * FT2M, 3),
                        maxZ = Math.Round((bb?.Max.Z ?? 0) * FT2M, 3)
                    };
                })
                .OrderBy(f => f.elevM)
                .ToList();

            // 2. Beams
            var beams = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralFraming)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(b => {
                    var lvl = doc.GetElement(b.LevelId) as Level;
                    var lc = b.Location as LocationCurve;
                    var p0 = lc?.Curve.GetEndPoint(0);
                    var p1 = lc?.Curve.GetEndPoint(1);
                    return new {
                        id = b.Id.Value,
                        name = b.Name,
                        level = lvl?.Name,
                        p0x = Math.Round((p0?.X ?? 0) * FT2M * 1000, 1),
                        p0y = Math.Round((p0?.Y ?? 0) * FT2M * 1000, 1),
                        p1x = Math.Round((p1?.X ?? 0) * FT2M * 1000, 1),
                        p1y = Math.Round((p1?.Y ?? 0) * FT2M * 1000, 1)
                    };
                })
                .ToList();

            // 3. Walls summary by level & orientation
            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Select(w => {
                    var bLvl = doc.GetElement(w.LevelId) as Level;
                    var tLvlId = w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE)?.AsElementId();
                    var tLvl = tLvlId != null && tLvlId != ElementId.InvalidElementId ? doc.GetElement(tLvlId) as Level : null;
                    var topOff = w.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)?.AsDouble() * FT2M * 1000 ?? 0;
                    var lc = w.Location as LocationCurve;
                    var p0 = lc?.Curve.GetEndPoint(0);
                    var p1 = lc?.Curve.GetEndPoint(1);
                    double x0 = Math.Round((p0?.X ?? 0) * FT2M * 1000, 1);
                    double y0 = Math.Round((p0?.Y ?? 0) * FT2M * 1000, 1);
                    double x1 = Math.Round((p1?.X ?? 0) * FT2M * 1000, 1);
                    double y1 = Math.Round((p1?.Y ?? 0) * FT2M * 1000, 1);
                    double dx = Math.Abs(x1 - x0);
                    double dy = Math.Abs(y1 - y0);
                    string dir = dx > dy ? "X" : "Y";
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        baseLevel = bLvl?.Name,
                        topLevel = tLvl?.Name,
                        topOffMm = Math.Round(topOff, 1),
                        dir,
                        x0, y0, x1, y1,
                        midX = Math.Round((x0 + x1) / 2.0, 1),
                        midY = Math.Round((y0 + y1) / 2.0, 1)
                    };
                })
                .ToList();

            return new { floors, beams, wallsCount = walls.Count, walls };
        }
    }
}

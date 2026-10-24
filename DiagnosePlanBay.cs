using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DiagnosePlanBay
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                // Get the elements selected by user or inspect all 3 Window_K2_Stack instances
                var selIds = uidoc.Selection.GetElementIds();
                var selList = selIds.Select(id =>
                {
                    var e = doc.GetElement(id);
                    var bb = e.get_BoundingBox(null);
                    return new
                    {
                        id = id.Value,
                        name = e.Name,
                        category = e.Category?.Name,
                        type = e.GetType().Name,
                        minZ = bb != null ? bb.Min.Z * FT2M : 0,
                        maxZ = bb != null ? bb.Max.Z * FT2M : 0,
                        minY = bb != null ? bb.Min.Y * FT2M : 0,
                        maxY = bb != null ? bb.Max.Y * FT2M : 0
                    };
                }).ToList();

                // Inspect all walls around Y[11.5, 13.5]
                var walls = new FilteredElementCollector(doc)
                    .OfClass(typeof(Wall))
                    .Cast<Wall>()
                    .Where(w =>
                    {
                        var bb = w.get_BoundingBox(null);
                        return bb != null && bb.Min.Y * FT2M < 13.5 && bb.Max.Y * FT2M > 11.5 && bb.Min.X * FT2M < 2.0;
                    })
                    .Select(w =>
                    {
                        var lc = (w.Location as LocationCurve)?.Curve;
                        var bb = w.get_BoundingBox(null);
                        return new
                        {
                            id = w.Id.Value,
                            name = w.Name,
                            wallType = w.WallType.Name,
                            baseElev = (doc.GetElement(w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT).AsElementId()) as Level)?.Elevation * FT2M,
                            baseOffset = w.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)?.AsDouble() * FT2M,
                            unconnectedHeight = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble() * FT2M,
                            start = lc != null ? $"{lc.GetEndPoint(0).X * FT2M:F2}, {lc.GetEndPoint(0).Y * FT2M:F2}, {lc.GetEndPoint(0).Z * FT2M:F2}" : "",
                            end = lc != null ? $"{lc.GetEndPoint(1).X * FT2M:F2}, {lc.GetEndPoint(1).Y * FT2M:F2}, {lc.GetEndPoint(1).Z * FT2M:F2}" : "",
                            minZ = bb != null ? bb.Min.Z * FT2M : 0,
                            maxZ = bb != null ? bb.Max.Z * FT2M : 0
                        };
                    })
                    .ToList();

                // Inspect all Window_K2_Stack instances
                var stacks = new FilteredElementCollector(doc)
                    .OfClass(typeof(FamilyInstance))
                    .Cast<FamilyInstance>()
                    .Where(f => f.Symbol.FamilyName.Contains("Window_K2_Stack"))
                    .Select(f =>
                    {
                        var bb = f.get_BoundingBox(null);
                        var lp = (f.Location as LocationPoint)?.Point;
                        return new
                        {
                            id = f.Id.Value,
                            name = f.Name,
                            loc = lp != null ? $"{lp.X * FT2M:F3}, {lp.Y * FT2M:F3}, {lp.Z * FT2M:F3}" : "",
                            minZ = bb != null ? bb.Min.Z * FT2M : 0,
                            maxZ = bb != null ? bb.Max.Z * FT2M : 0,
                            minY = bb != null ? bb.Min.Y * FT2M : 0,
                            maxY = bb != null ? bb.Max.Y * FT2M : 0,
                            minX = bb != null ? bb.Min.X * FT2M : 0,
                            maxX = bb != null ? bb.Max.X * FT2M : 0
                        };
                    })
                    .ToList();

                return new
                {
                    selected = selList,
                    stacks,
                    walls
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

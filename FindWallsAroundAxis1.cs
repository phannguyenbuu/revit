using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FindWallsAroundAxis1
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var walls = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Select(w => {
                    var bb = w.get_BoundingBox(null);
                    if (bb == null) return null;
                    double minX = bb.Min.X * FT2MM;
                    double maxX = bb.Max.X * FT2MM;
                    double minY = bb.Min.Y * FT2MM;
                    double maxY = bb.Max.Y * FT2MM;
                    double minZ = bb.Min.Z * FT2MM;
                    double maxZ = bb.Max.Z * FT2MM;
                    var lvl = doc.GetElement(w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsElementId())?.Name;
                    var inserts = w.FindInserts(true, true, true, true).Select(id => {
                        var elem = doc.GetElement(id);
                        return $"{elem?.Name} ({elem?.Category?.Name}, ID {id.Value})";
                    }).ToList();

                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        level = lvl,
                        bboxMin = $"({minX:F1}, {minY:F1}, {minZ:F1})",
                        bboxMax = $"({maxX:F1}, {maxY:F1}, {maxZ:F1})",
                        minX, maxX, minY, maxY, minZ, maxZ,
                        inserts
                    };
                })
                .Where(w => w != null && w.minX < 2000.0 && w.minY > 2000.0 && w.maxY < 11000.0)
                .OrderBy(w => w.minZ)
                .ToList();

            // Also get all Windows in the project and their hosts
            var allWindows = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(wi => {
                    var wbb = wi.get_BoundingBox(null);
                    var wlp = wi.Location as LocationPoint;
                    return new {
                        id = wi.Id.Value,
                        name = wi.Name,
                        symbolName = wi.Symbol.Name,
                        host = wi.Host?.Name + " (ID " + wi.Host?.Id.Value + ")",
                        point = wlp != null ? $"({wlp.Point.X * FT2MM:F1}, {wlp.Point.Y * FT2MM:F1}, {wlp.Point.Z * FT2MM:F1})" : "None",
                        minZ = wbb != null ? wbb.Min.Z * FT2MM : 0
                    };
                })
                .ToList();

            return new { count = walls.Count, walls, allWindowsCount = allWindows.Count, allWindows };
        }
    }
}

import urllib.request, json

code = """
using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ListAllProjectWalls
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
                    var lvl = doc.GetElement(w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsElementId())?.Name;
                    var inserts = w.FindInserts(true, true, true, true).Select(id => doc.GetElement(id)?.Name).ToList();
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        level = lvl,
                        minZ = bb != null ? bb.Min.Z * FT2MM : 0,
                        maxZ = bb != null ? bb.Max.Z * FT2MM : 0,
                        insertsCount = inserts.Count,
                        inserts
                    };
                })
                .ToList();

            var wallsWithInserts = walls.Where(w => w.insertsCount > 0).ToList();

            return new {
                totalWalls = walls.Count,
                wallsWithInsertsCount = wallsWithInserts.Count,
                wallsWithInserts
            };
        }
    }
}
"""
print("ListAllProjectWalls ready")

using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDoorHostAndSelection
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var selIds = uidoc.Selection.GetElementIds();
            var list = new List<object>();

            foreach (var id in selIds)
            {
                var elem = doc.GetElement(id);
                if (elem == null) continue;

                var lp = elem.Location as LocationPoint;
                var lc = elem.Location as LocationCurve;
                var bb = elem.get_BoundingBox(null);

                // Host
                Element host = null;
                if (elem is FamilyInstance fi) host = fi.Host;

                // Level
                var lvl = doc.GetElement(elem.LevelId)?.Name;

                list.Add(new
                {
                    id = elem.Id.Value,
                    name = elem.Name,
                    cat = elem.Category?.Name,
                    type = elem.GetType().Name,
                    level = lvl,
                    host = host != null ? $"{host.Name} (ID {host.Id.Value}, {host.GetType().Name})" : "None",
                    bboxMin = bb != null ? $"({bb.Min.X * FT2MM:F1}, {bb.Min.Y * FT2MM:F1}, {bb.Min.Z * FT2MM:F1})" : "None",
                    bboxMax = bb != null ? $"({bb.Max.X * FT2MM:F1}, {bb.Max.Y * FT2MM:F1}, {bb.Max.Z * FT2MM:F1})" : "None"
                });
            }

            // Also check 2369928
            var e2369928 = doc.GetElement(new ElementId(2369928L));

            // Also find all walls that host doors or windows around Axis 1 or Axis A/B/C/D
            var wallsWithInserts = new FilteredElementCollector(doc)
                .OfClass(typeof(Wall))
                .Cast<Wall>()
                .Where(w => w.FindInserts(true, true, true, true).Count > 0)
                .Select(w => {
                    var wbb = w.get_BoundingBox(null);
                    var ins = w.FindInserts(true, true, true, true).Select(i => {
                        var ie = doc.GetElement(i);
                        return $"{ie?.Name} ({ie?.Category?.Name}, ID {i.Value})";
                    }).ToList();
                    var bLvl = doc.GetElement(w.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT)?.AsElementId())?.Name;
                    return new {
                        id = w.Id.Value,
                        name = w.Name,
                        level = bLvl,
                        bboxMin = wbb != null ? $"({wbb.Min.X * FT2MM:F1}, {wbb.Min.Y * FT2MM:F1}, {wbb.Min.Z * FT2MM:F1})" : "None",
                        bboxMax = wbb != null ? $"({wbb.Max.X * FT2MM:F1}, {wbb.Max.Y * FT2MM:F1}, {wbb.Max.Z * FT2MM:F1})" : "None",
                        inserts = ins
                    };
                })
                .ToList();

            return new {
                selection = list,
                e2369928 = e2369928 != null ? new { id = e2369928.Id.Value, name = e2369928.Name, type = e2369928.GetType().Name } : null,
                wallsWithInsertsCount = wallsWithInserts.Count,
                wallsWithInserts
            };
        }
    }
}

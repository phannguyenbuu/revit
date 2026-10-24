using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectSelectedColumns
    {
        private static double ToM(double ft) => ft * 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var selIds = uidoc.Selection.GetElementIds();
            var cols = new List<object>();

            foreach (var id in selIds)
            {
                var el = doc.GetElement(id);
                if (el == null) continue;

                var baseLevelParam = el.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                var baseOffsetParam = el.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM);
                var topLevelParam = el.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                var topOffsetParam = el.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);

                string baseLevelName = baseLevelParam != null ? (doc.GetElement(baseLevelParam.AsElementId())?.Name ?? "none") : "null";
                string topLevelName = topLevelParam != null ? (doc.GetElement(topLevelParam.AsElementId())?.Name ?? "none") : "null";

                double baseOffset_m = baseOffsetParam != null ? ToM(baseOffsetParam.AsDouble()) : 0;
                double topOffset_m = topOffsetParam != null ? ToM(topOffsetParam.AsDouble()) : 0;

                XYZ loc = null;
                if (el.Location is LocationPoint lp) loc = lp.Point;

                var bb = el.get_BoundingBox(null);
                double zMin = bb != null ? ToM(bb.Min.Z) : 0;
                double zMax = bb != null ? ToM(bb.Max.Z) : 0;
                double height = zMax - zMin;

                cols.Add(new
                {
                    id = id.Value,
                    name = el.Name,
                    category = el.Category?.Name,
                    locX = loc != null ? ToM(loc.X) : 0,
                    locY = loc != null ? ToM(loc.Y) : 0,
                    baseLevel = baseLevelName,
                    baseLevelId = baseLevelParam?.AsElementId().Value,
                    baseOffset_m,
                    topLevel = topLevelName,
                    topLevelId = topLevelParam?.AsElementId().Value,
                    topOffset_m,
                    zMin,
                    zMax,
                    height
                });
            }

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new { id = l.Id.Value, name = l.Name, elevation_m = ToM(l.Elevation) })
                .ToList();

            return new { count = cols.Count, columns = cols, levels };
        }
    }
}

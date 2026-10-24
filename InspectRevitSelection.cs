using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectRevitSelection
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active project document" };

            var selIds = uidoc.Selection.GetElementIds();
            var list = new List<object>();

            foreach (var id in selIds)
            {
                var elem = doc.GetElement(id);
                if (elem == null) continue;

                var bb = elem.get_BoundingBox(null);
                var lp = elem.Location as LocationPoint;
                var lc = elem.Location as LocationCurve;

                // Level parameter
                var pLevel = elem.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM) 
                          ?? elem.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)
                          ?? elem.get_Parameter(BuiltInParameter.WALL_BASE_CONSTRAINT);
                var levelName = pLevel != null ? doc.GetElement(pLevel.AsElementId())?.Name : "N/A";

                var pOffset = elem.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
                           ?? elem.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET);
                var offsetVal = pOffset != null ? pOffset.AsDouble() * FT2MM : 0.0;

                list.Add(new
                {
                    id = id.Value,
                    name = elem.Name,
                    category = elem.Category?.Name,
                    type = elem.GetType().Name,
                    level = levelName,
                    offset = offsetVal,
                    point = lp != null ? $"({lp.Point.X * FT2MM:F1}, {lp.Point.Y * FT2MM:F1}, {lp.Point.Z * FT2MM:F1}) mm" : "None",
                    bboxMin = bb != null ? $"({bb.Min.X * FT2MM:F1}, {bb.Min.Y * FT2MM:F1}, {bb.Min.Z * FT2MM:F1}) mm" : "None",
                    bboxMax = bb != null ? $"({bb.Max.X * FT2MM:F1}, {bb.Max.Y * FT2MM:F1}, {bb.Max.Z * FT2MM:F1}) mm" : "None",
                });
            }

            return new { count = selIds.Count, selection = list };
        }
    }
}

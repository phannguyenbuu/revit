using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectMatTienInstance
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active project document" };

            var insts = new FilteredElementCollector(doc)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Where(fi => fi.Symbol.Family.Name.IndexOf("Mat_Tien", StringComparison.OrdinalIgnoreCase) >= 0
                          || fi.Symbol.Family.Name.IndexOf("MatTien", StringComparison.OrdinalIgnoreCase))
                .ToList();

            var list = new List<object>();
            foreach (var inst in insts)
            {
                var lp = inst.Location as LocationPoint;
                var bb = inst.get_BoundingBox(null);
                list.Add(new
                {
                    id = inst.Id.Value,
                    name = inst.Name,
                    family = inst.Symbol.Family.Name,
                    symbol = inst.Symbol.Name,
                    point = lp != null ? $"({lp.Point.X * FT2MM:F1}, {lp.Point.Y * FT2MM:F1}, {lp.Point.Z * FT2MM:F1}) mm" : "None",
                    rotation = lp != null ? $"{lp.Rotation * 180 / Math.PI:F1} deg" : "None",
                    bboxMin = bb != null ? $"({bb.Min.X * FT2MM:F1}, {bb.Min.Y * FT2MM:F1}, {bb.Min.Z * FT2MM:F1}) mm" : "None",
                    bboxMax = bb != null ? $"({bb.Max.X * FT2MM:F1}, {bb.Max.Y * FT2MM:F1}, {bb.Max.Z * FT2MM:F1}) mm" : "None",
                });
            }

            return new { count = insts.Count, instances = list };
        }
    }
}

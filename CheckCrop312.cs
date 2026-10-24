using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckCrop312
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var v = doc.GetElement(new ElementId(312L)) as ViewPlan;
            var cb = v.CropBox;
            var orig = cb.Transform.Origin;

            return new {
                origin = new { x = orig.X * 304.8, y = orig.Y * 304.8, z = orig.Z * 304.8 },
                min = new { x = cb.Min.X * 304.8, y = cb.Min.Y * 304.8 },
                max = new { x = cb.Max.X * 304.8, y = cb.Max.Y * 304.8 },
                cropActive = v.CropBoxActive,
                cropVisible = v.CropBoxVisible
            };
        }
    }
}
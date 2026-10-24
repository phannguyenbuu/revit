using System;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectTransforms
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument.Document;
            var v2 = doc.GetElement(new ElementId(695L)) as ViewPlan;
            var v3 = doc.GetElement(new ElementId(1727632L)) as ViewPlan;

            var t2 = v2.CropBox.Transform;
            var t3 = v3.CropBox.Transform;

            return new
            {
                v2_origin = new { x = t2.Origin.X * 0.3048, y = t2.Origin.Y * 0.3048, z = t2.Origin.Z * 0.3048 },
                v2_basisX = new { x = t2.BasisX.X, y = t2.BasisX.Y, z = t2.BasisX.Z },
                v2_basisY = new { x = t2.BasisY.X, y = t2.BasisY.Y, z = t2.BasisY.Z },
                v2_min = new { x = v2.CropBox.Min.X * 0.3048, y = v2.CropBox.Min.Y * 0.3048 },
                v2_max = new { x = v2.CropBox.Max.X * 0.3048, y = v2.CropBox.Max.Y * 0.3048 },

                v3_origin = new { x = t3.Origin.X * 0.3048, y = t3.Origin.Y * 0.3048, z = t3.Origin.Z * 0.3048 },
                v3_basisX = new { x = t3.BasisX.X, y = t3.BasisX.Y, z = t3.BasisX.Z },
                v3_basisY = new { x = t3.BasisY.X, y = t3.BasisY.Y, z = t3.BasisY.Z },
                v3_min = new { x = v3.CropBox.Min.X * 0.3048, y = v3.CropBox.Min.Y * 0.3048, z = v3.CropBox.Min.Z * 0.3048 },
                v3_max = new { x = v3.CropBox.Max.X * 0.3048, y = v3.CropBox.Max.Y * 0.3048, z = v3.CropBox.Max.Z * 0.3048 },
                v3_cropActive = v3.CropBoxActive,

                v4_origin = new { x = (doc.GetElement(new ElementId(931687L)) as ViewPlan).CropBox.Transform.Origin.X * 0.3048, y = (doc.GetElement(new ElementId(931687L)) as ViewPlan).CropBox.Transform.Origin.Y * 0.3048, z = (doc.GetElement(new ElementId(931687L)) as ViewPlan).CropBox.Transform.Origin.Z * 0.3048 },
                v4_min = new { x = (doc.GetElement(new ElementId(931687L)) as ViewPlan).CropBox.Min.X * 0.3048, y = (doc.GetElement(new ElementId(931687L)) as ViewPlan).CropBox.Min.Y * 0.3048, z = (doc.GetElement(new ElementId(931687L)) as ViewPlan).CropBox.Min.Z * 0.3048 },
                v4_max = new { x = (doc.GetElement(new ElementId(931687L)) as ViewPlan).CropBox.Max.X * 0.3048, y = (doc.GetElement(new ElementId(931687L)) as ViewPlan).CropBox.Max.Y * 0.3048, z = (doc.GetElement(new ElementId(931687L)) as ViewPlan).CropBox.Max.Z * 0.3048 }
            };
        }
    }
}

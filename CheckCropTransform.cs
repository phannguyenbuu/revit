using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CheckCropTransform
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var v2 = doc.GetElement(new ElementId(695L)) as ViewPlan;
            if (v2 == null) return new { error = "No view" };

            var cb = v2.CropBox;
            var orig = cb.Transform.Origin;
            var basisX = cb.Transform.BasisX;
            var basisY = cb.Transform.BasisY;

            var paramInfo = new List<object>();
            foreach (Parameter p in v2.Parameters)
            {
                string name = p.Definition.Name;
                if (name.IndexOf("Crop", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    name.IndexOf("Scope", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    name.IndexOf("Annotation", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    paramInfo.Add(new { name = name, value = p.AsValueString() ?? p.AsString() ?? p.AsInteger().ToString() });
                }
            }

            return new {
                origin = new { x = orig.X * 304.8, y = orig.Y * 304.8, z = orig.Z * 304.8 },
                basisX = new { x = basisX.X, y = basisX.Y, z = basisX.Z },
                basisY = new { x = basisY.X, y = basisY.Y, z = basisY.Z },
                min = new { x = cb.Min.X * 304.8, y = cb.Min.Y * 304.8 },
                max = new { x = cb.Max.X * 304.8, y = cb.Max.Y * 304.8 },
                paramsList = paramInfo
            };
        }
    }
}
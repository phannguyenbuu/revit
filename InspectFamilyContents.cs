using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyContents
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var sym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (sym == null) return new { error = "Symbol 104895 not found" };

            var famDoc = doc.EditFamily(sym.Family);

            // 1. Check forms/extrusions
            var forms = new FilteredElementCollector(famDoc)
                .OfClass(typeof(GenericForm))
                .Cast<GenericForm>()
                .Select(f =>
                {
                    var bb = f.get_BoundingBox(null);
                    return new
                    {
                        name = f.Name,
                        type = f.GetType().Name,
                        isSolid = f.IsSolid,
                        min = bb != null ? new { x = bb.Min.X * 304.8, y = bb.Min.Y * 304.8, z = bb.Min.Z * 304.8 } : null,
                        max = bb != null ? new { x = bb.Max.X * 304.8, y = bb.Max.Y * 304.8, z = bb.Max.Z * 304.8 } : null
                    };
                })
                .ToList();

            // 2. Check model/symbolic lines
            var curves = new FilteredElementCollector(famDoc)
                .OfClass(typeof(CurveElement))
                .Cast<CurveElement>()
                .Select(c => new
                {
                    type = c.GetType().Name,
                    subCat = c.LineStyle?.Name
                })
                .ToList();

            var refPlanes = new FilteredElementCollector(famDoc)
                .OfClass(typeof(ReferencePlane))
                .Cast<ReferencePlane>()
                .Select(rp => new
                {
                    name = rp.Name,
                    origin = new { x = rp.FreeEnd.X * 304.8, y = rp.FreeEnd.Y * 304.8, z = rp.FreeEnd.Z * 304.8 },
                    dir = new { x = rp.Direction.X, y = rp.Direction.Y, z = rp.Direction.Z },
                    normal = new { x = rp.Normal.X, y = rp.Normal.Y, z = rp.Normal.Z }
                })
                .ToList();

            famDoc.Close(false);

            return new
            {
                forms = forms,
                curveCount = curves.Count,
                refPlanes = refPlanes
            };
        }
    }
}

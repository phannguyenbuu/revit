using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectGlassConstraints
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var fam = new FilteredElementCollector(doc)
                    .OfClass(typeof(Family))
                    .Cast<Family>()
                    .FirstOrDefault(f => f.Name.Equals("CUA SO 2 CANH NHOM KINH O O THOANG", StringComparison.OrdinalIgnoreCase));

                if (fam == null) return new { error = "Family not found" };

                var famDoc = doc.EditFamily(fam);
                if (famDoc == null) return new { error = "Cannot edit family" };

                var glassExt = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(Extrusion))
                    .Cast<Extrusion>()
                    .FirstOrDefault(e => e.Subcategory != null && e.Subcategory.Name.Equals("Glass", StringComparison.OrdinalIgnoreCase));

                if (glassExt == null) return new { error = "No glass ext" };

                var sketch = glassExt.Sketch;
                var sketchPlane = sketch.SketchPlane;
                var plane = sketchPlane.GetPlane();

                // Check parameters of glassExt
                var pInfo = new List<object>();
                foreach (Parameter p in glassExt.Parameters)
                {
                    if (p.HasValue)
                    {
                        var famParam = famDoc.FamilyManager.GetAssociatedFamilyParameter(p);
                        pInfo.Add(new
                        {
                            name = p.Definition.Name,
                            val = p.AsValueString(),
                            associatedParam = famParam?.Definition.Name
                        });
                    }
                }

                // Check all dimensions in famDoc
                var dims = new FilteredElementCollector(famDoc)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .Select(d =>
                    {
                        FamilyParameter fp = null;
                        try { fp = d.FamilyLabel; } catch { }
                        bool locked = false;
                        try { locked = d.IsLocked; } catch { }
                        return new
                        {
                            id = d.Id.Value,
                            label = fp?.Definition.Name,
                            isLocked = locked,
                            val = d.Value.HasValue ? d.Value.Value * 304.8 : 0
                        };
                    })
                    .ToList();

                famDoc.Close(false);

                return new
                {
                    sketchPlane = new
                    {
                        origin = new { x = plane.Origin.X * 304.8, y = plane.Origin.Y * 304.8, z = plane.Origin.Z * 304.8 },
                        normal = new { x = plane.Normal.X, y = plane.Normal.Y, z = plane.Normal.Z }
                    },
                    startOffset = glassExt.StartOffset * 304.8,
                    endOffset = glassExt.EndOffset * 304.8,
                    materialId = glassExt.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)?.AsElementId()?.Value,
                    subCatId = glassExt.Subcategory?.Id.Value,
                    subCatName = glassExt.Subcategory?.Name,
                    parameters = pInfo,
                    dims
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

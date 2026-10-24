using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFamilyGeometrySize
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var sym = doc.GetElement(new ElementId(104895L)) as FamilySymbol;
            if (sym == null) return new { error = "Symbol 104895 not found" };

            var famDoc = doc.EditFamily(sym.Family);
            
            // Check all solid/form elements in family
            var solids = new FilteredElementCollector(famDoc)
                .OfClass(typeof(GenericForm))
                .Cast<GenericForm>()
                .Select(f =>
                {
                    var bbox = f.get_BoundingBox(null);
                    return new
                    {
                        name = f.Name,
                        min = bbox != null ? new { x = bbox.Min.X * 304.8, y = bbox.Min.Y * 304.8, z = bbox.Min.Z * 304.8 } : null,
                        max = bbox != null ? new { x = bbox.Max.X * 304.8, y = bbox.Max.Y * 304.8, z = bbox.Max.Z * 304.8 } : null
                    };
                })
                .ToList();

            // Also check dimensions in family
            var dims = new FilteredElementCollector(famDoc)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .Select(d => new
                {
                    val = d.Value.HasValue ? d.Value.Value * 304.8 : 0,
                    param = d.FamilyLabel?.Definition?.Name
                })
                .ToList();

            famDoc.Close(false);

            return new
            {
                solids = solids,
                dimensions = dims
            };
        }
    }
}

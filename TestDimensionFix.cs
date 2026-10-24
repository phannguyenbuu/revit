using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestDimensionFix
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Let's test on Dim 2409100 on Tầng 1 (View 312), which has a 0 at index 0
            var d = doc.GetElement(new ElementId(2409100L)) as Dimension;
            if (d == null) return new { error = "Dim 2409100 not found" };

            var refs = d.References;
            var refList = new List<object>();

            if (refs != null)
            {
                foreach (Reference r in refs)
                {
                    var elem = doc.GetElement(r.ElementId);
                    refList.Add(new
                    {
                        elemId = r.ElementId?.Value,
                        elemCat = elem?.Category?.Name,
                        elemName = elem?.Name,
                        stableRepresentation = r.ConvertToStableRepresentation(doc)
                    });
                }
            }

            return new
            {
                success = true,
                dimId = d.Id.Value,
                numSegments = d.NumberOfSegments,
                refCount = refs?.Size,
                references = refList
            };
        }
    }
}

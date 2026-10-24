using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectDim2409102
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var dim = doc.GetElement(new ElementId(2409102)) as Dimension;
                if (dim == null) return new { error = "Dim not found" };

                var refs = new List<object>();
                foreach (Reference r in dim.References)
                {
                    var elem = doc.GetElement(r.ElementId);
                    refs.Add(new {
                        elemId = r.ElementId.Value,
                        cat = elem?.Category?.Name ?? "NoCat",
                        name = elem?.Name ?? "",
                        repr = r.ConvertToStableRepresentation(doc)
                    });
                }

                return new {
                    id = dim.Id.Value,
                    name = dim.Name,
                    numSegs = dim.NumberOfSegments,
                    refs
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

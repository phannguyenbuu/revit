using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DebugDimRefs
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var dim = doc?.GetElement(new ElementId(2409277)) as Dimension;
            if (dim == null) return new { error = "Not found" };

            var list = new List<object>();
            foreach (Reference r in dim.References)
            {
                var el = doc.GetElement(r.ElementId);
                double? actualX = null;
                if (el is Grid g) actualX = g.Curve.GetEndPoint(0).X * FT_TO_MM;
                else
                {
                    var geo = el?.GetGeometryObjectFromReference(r);
                    if (geo is PlanarFace pf) actualX = pf.Origin.X * FT_TO_MM;
                }
                list.Add(new {
                    elId = r.ElementId.Value,
                    cat = el?.Category?.Name,
                    name = el?.Name,
                    actualX = actualX.HasValue ? Math.Round(actualX.Value, 1) : (double?)null
                });
            }
            return list;
        }
    }
}

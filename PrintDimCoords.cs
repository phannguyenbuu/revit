using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class PrintDimCoords
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            var dimIds = new long[] { 2409100, 2409101, 2409102 };
            var allDims = new List<object>();

            foreach (var dId in dimIds)
            {
                var dim = doc.GetElement(new ElementId(dId)) as Dimension;
                var coords = new List<object>();
                if (dim != null && dim.References != null)
                {
                    foreach (Reference r in dim.References)
                    {
                        var el = doc.GetElement(r.ElementId);
                        double y = -999999;
                        if (el is Grid g)
                        {
                            y = g.Curve.GetEndPoint(0).Y * FT_TO_MM;
                        }
                        else
                        {
                            var geoObj = el.GetGeometryObjectFromReference(r);
                            if (geoObj is PlanarFace pf)
                            {
                                y = pf.Origin.Y * FT_TO_MM;
                            }
                        }
                        coords.Add(new {
                            elId = r.ElementId.Value,
                            name = el?.Name,
                            cat = el?.Category?.Name,
                            y = Math.Round(y, 1)
                        });
                    }
                }
                allDims.Add(new { id = dId, coords });
            }

            return new { allDims };
        }
    }
}

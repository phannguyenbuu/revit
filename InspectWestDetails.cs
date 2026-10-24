using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWestDetails
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // Look at all elements between X = -10000 and X = 2000
            var els = new FilteredElementCollector(doc, view.Id)
                .WhereElementIsNotElementType()
                .Where(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return false;
                    double minX = bb.Min.X * FT_TO_MM;
                    double maxX = bb.Max.X * FT_TO_MM;
                    return minX < 1500 && maxX > -8000;
                })
                .Select(e => new {
                    id = e.Id.Value,
                    cat = e.Category?.Name,
                    name = e.Name,
                    type = e.GetType().Name,
                    minX = Math.Round(e.get_BoundingBox(view).Min.X * FT_TO_MM, 1),
                    maxX = Math.Round(e.get_BoundingBox(view).Max.X * FT_TO_MM, 1),
                    minY = Math.Round(e.get_BoundingBox(view).Min.Y * FT_TO_MM, 1),
                    maxY = Math.Round(e.get_BoundingBox(view).Max.Y * FT_TO_MM, 1)
                })
                .OrderBy(x => x.minY)
                .ToList();

            return new { count = els.Count, els };
        }
    }
}

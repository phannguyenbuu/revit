using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectNearbyDetails
    {
        private const double FT_TO_MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // 1. Elements at West entrance terrace / facade (X <= 0)
            var westEntranceEls = new FilteredElementCollector(doc, view.Id)
                .WhereElementIsNotElementType()
                .Where(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return false;
                    double minX = bb.Min.X * FT_TO_MM;
                    double maxX = bb.Max.X * FT_TO_MM;
                    return minX < 200 && maxX > -10000;
                })
                .Select(e => new {
                    id = e.Id.Value,
                    cat = e.Category?.Name,
                    name = e.Name,
                    minX = Math.Round(e.get_BoundingBox(view).Min.X * FT_TO_MM, 1),
                    maxX = Math.Round(e.get_BoundingBox(view).Max.X * FT_TO_MM, 1),
                    minY = Math.Round(e.get_BoundingBox(view).Min.Y * FT_TO_MM, 1),
                    maxY = Math.Round(e.get_BoundingBox(view).Max.Y * FT_TO_MM, 1)
                })
                .OrderBy(x => x.minY)
                .ToList();

            // 2. Elements at East side (X >= 36000)
            var eastEls = new FilteredElementCollector(doc, view.Id)
                .WhereElementIsNotElementType()
                .Where(e => {
                    var bb = e.get_BoundingBox(view);
                    if (bb == null) return false;
                    double minX = bb.Min.X * FT_TO_MM;
                    double maxX = bb.Max.X * FT_TO_MM;
                    return maxX > 36000;
                })
                .Select(e => new {
                    id = e.Id.Value,
                    cat = e.Category?.Name,
                    name = e.Name,
                    minX = Math.Round(e.get_BoundingBox(view).Min.X * FT_TO_MM, 1),
                    maxX = Math.Round(e.get_BoundingBox(view).Max.X * FT_TO_MM, 1),
                    minY = Math.Round(e.get_BoundingBox(view).Min.Y * FT_TO_MM, 1),
                    maxY = Math.Round(e.get_BoundingBox(view).Max.Y * FT_TO_MM, 1)
                })
                .OrderBy(x => x.minY)
                .ToList();

            return new {
                westEntranceEls,
                eastEls
            };
        }
    }
}

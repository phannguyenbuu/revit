using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloorDoors
    {
        private const double FT_TO_MM = 304.8;
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            View? view = null;
            if (args.TryGetProperty("viewId", out var pViewId))
            {
                view = doc.GetElement(new ElementId(pViewId.GetInt64())) as View;
            }
            if (view == null)
            {
                view = uiapp.ActiveUIDocument?.ActiveView;
            }
            if (view == null) return new { error = "No view found" };

            var doors = new FilteredElementCollector(doc, view.Id)
                .OfCategory(BuiltInCategory.OST_Doors)
                .OfClass(typeof(FamilyInstance))
                .Cast<FamilyInstance>()
                .Select(d => {
                    var lp = d.Location as LocationPoint;
                    var bb = d.get_BoundingBox(view);
                    double x = lp != null ? Math.Round(lp.Point.X * FT_TO_MM, 1) : 0;
                    double y = lp != null ? Math.Round(lp.Point.Y * FT_TO_MM, 1) : 0;
                    double bbMinX = bb != null ? Math.Round(bb.Min.X * FT_TO_MM, 1) : 0;
                    double bbMaxX = bb != null ? Math.Round(bb.Max.X * FT_TO_MM, 1) : 0;
                    double bbMinY = bb != null ? Math.Round(bb.Min.Y * FT_TO_MM, 1) : 0;
                    double bbMaxY = bb != null ? Math.Round(bb.Max.Y * FT_TO_MM, 1) : 0;

                    // Get type name & mark
                    var mark = d.get_Parameter(BuiltInParameter.DOOR_NUMBER)?.AsString() ?? d.Name;
                    var symName = d.Symbol?.Name ?? "";
                    var host = d.Host as Wall;

                    return new {
                        id = d.Id.Value,
                        name = d.Name,
                        symName,
                        mark,
                        x, y,
                        bbMinX, bbMaxX,
                        bbMinY, bbMaxY,
                        width = Math.Round(bbMaxX - bbMinX, 1),
                        hostId = host?.Id.Value
                    };
                })
                .OrderBy(d => d.y)
                .ThenBy(d => d.x)
                .ToList();

            return new { count = doors.Count, doors };
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectGridsAndColumns
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Select(g =>
                {
                    var c = g.Curve;
                    var p1 = c.GetEndPoint(0);
                    var p2 = c.GetEndPoint(1);
                    return new
                    {
                        name = g.Name,
                        id = g.Id.Value,
                        isVertical = Math.Abs(p1.X - p2.X) < 0.01,
                        xM = p1.X * 0.3048,
                        yM = p1.Y * 0.3048,
                        p1 = new { x = p1.X * 0.3048, y = p1.Y * 0.3048 },
                        p2 = new { x = p2.X * 0.3048, y = p2.Y * 0.3048 }
                    };
                })
                .OrderBy(g => g.name)
                .ToList();

            var columns = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .Select(col =>
                {
                    var lp = col.Location as LocationPoint;
                    var pt = lp?.Point;
                    return new
                    {
                        id = col.Id.Value,
                        name = col.Name,
                        x = pt != null ? pt.X * 0.3048 : 0,
                        y = pt != null ? pt.Y * 0.3048 : 0
                    };
                })
                .OrderBy(c => c.x)
                .ToList();

            return new
            {
                grids = grids,
                columnsCount = columns.Count,
                columnXValues = columns.Select(c => Math.Round(c.x, 3)).Distinct().OrderBy(x => x).ToList()
            };
        }
    }
}

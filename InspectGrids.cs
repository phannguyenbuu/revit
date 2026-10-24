using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectGrids
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "no doc" };

            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Select(g => {
                    var line = g.Curve as Line;
                    var pt = line != null ? line.GetEndPoint(0) : XYZ.Zero;
                    var dir = line != null ? line.Direction : XYZ.Zero;
                    return new {
                        name = g.Name,
                        ptX = pt.X * 304.8,
                        ptY = pt.Y * 304.8,
                        dirX = dir.X,
                        dirY = dir.Y
                    };
                })
                .OrderBy(g => g.name)
                .ToList();

            return new { count = grids.Count, grids };
        }
    }
}

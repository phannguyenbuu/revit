using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DumpRevitGrids
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .Select(g => {
                    var l = g.Curve as Line;
                    return new {
                        name = g.Name,
                        p0 = l != null ? new { x = Math.Round(l.GetEndPoint(0).X * 304.8, 1), y = Math.Round(l.GetEndPoint(0).Y * 304.8, 1) } : null,
                        p1 = l != null ? new { x = Math.Round(l.GetEndPoint(1).X * 304.8, 1), y = Math.Round(l.GetEndPoint(1).Y * 304.8, 1) } : null
                    };
                }).OrderBy(g => g.name).ToList();
            return new { grids };
        }
    }
}

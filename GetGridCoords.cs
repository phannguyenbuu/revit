using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class GetGridCoords
    {
        private const double FT_TO_MM = 304.8;
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .OrderBy(g => g.Curve.GetEndPoint(0).Y)
                .Select(g => new {
                    name = g.Name,
                    y = Math.Round(g.Curve.GetEndPoint(0).Y * FT_TO_MM, 1),
                    x = Math.Round(g.Curve.GetEndPoint(0).X * FT_TO_MM, 1)
                })
                .ToList();
            return new { grids };
        }
    }
}

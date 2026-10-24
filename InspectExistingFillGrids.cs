using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectExistingFillGrids
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            var pats = new FilteredElementCollector(doc)
                .OfClass(typeof(FillPatternElement))
                .Cast<FillPatternElement>()
                .Where(p => p.Name == "Crosshatch" || p.Name == "Diagonal cross-hatch" || p.Name == "300X300" || p.Name.Contains("Square"))
                .Select(p => {
                    var fp = p.GetFillPattern();
                    var grids = fp.GetFillGrids().Select(g => new {
                        angle = g.Angle * 180.0 / Math.PI,
                        offset = g.Offset * 304.8,
                        origin = new { u = g.Origin.U * 304.8, v = g.Origin.V * 304.8 },
                        shift = g.Shift * 304.8,
                        segments = g.GetSegments().Select(s => s * 304.8).ToList()
                    }).ToList();
                    return new {
                        id = p.Id.Value,
                        name = p.Name,
                        target = fp.Target.ToString(),
                        grids
                    };
                })
                .ToList();

            return pats;
        }
    }
}

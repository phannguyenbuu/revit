using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloorExtents
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var floors = new FilteredElementCollector(doc)
                .OfClass(typeof(Floor))
                .Cast<Floor>()
                .Select(f => {
                    var l = doc.GetElement(f.LevelId) as Level;
                    var bb = f.get_BoundingBox(null);
                    return new {
                        id = f.Id.Value,
                        level = l?.Name,
                        elevM = (l?.Elevation ?? 0) * FT2M,
                        areaM2 = Math.Round(f.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() * FT2M * FT2M ?? 0, 2),
                        minX = Math.Round(bb.Min.X * FT2M * 1000, 0),
                        minY = Math.Round(bb.Min.Y * FT2M * 1000, 0),
                        maxX = Math.Round(bb.Max.X * FT2M * 1000, 0),
                        maxY = Math.Round(bb.Max.Y * FT2M * 1000, 0)
                    };
                })
                .OrderBy(f => f.elevM)
                .ToList();

            return new { floors };
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWallTypes
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active Revit document" };

            var wallTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .Select(wt => new
                {
                    id = wt.Id.Value,
                    name = wt.Name,
                    kind = wt.Kind.ToString(),
                    widthMm = wt.Width * FT2MM
                })
                .OrderBy(wt => wt.name)
                .ToList();

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .Select(l => new
                {
                    id = l.Id.Value,
                    name = l.Name,
                    elevM = l.Elevation * 0.3048
                })
                .OrderBy(l => l.elevM)
                .ToList();

            return new
            {
                wallTypes = wallTypes,
                levels = levels
            };
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectCompoundStructure
    {
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No active Revit document" };

            var wt = new FilteredElementCollector(doc)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(w => w.Name == "gach200_xay moi");

            if (wt == null) return new { error = "WallType gach200_xay moi not found" };

            var cs = wt.GetCompoundStructure();
            var layers = cs.GetLayers().Select((l, i) => new
            {
                index = i,
                function = l.Function.ToString(),
                widthMm = l.Width * FT2MM,
                materialId = l.MaterialId.Value
            }).ToList();

            return new
            {
                wallTypeName = wt.Name,
                totalWidthMm = wt.Width * FT2MM,
                layers = layers
            };
        }
    }
}

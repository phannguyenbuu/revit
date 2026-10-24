using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectFloorAndHatch
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Floor Types
            var floorTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(FloorType))
                .Cast<FloorType>()
                .Select(ft => new {
                    id = ft.Id.Value,
                    name = ft.Name
                })
                .ToList();

            // 2. Fill Patterns (looking for ANGLE)
            var fillPatterns = new FilteredElementCollector(doc)
                .OfClass(typeof(FillPatternElement))
                .Cast<FillPatternElement>()
                .Select(fp => new {
                    id = fp.Id.Value,
                    name = fp.Name,
                    target = fp.GetFillPattern().Target.ToString()
                })
                .Where(fp => fp.name.ToLower().Contains("angle") || fp.name.ToLower().Contains("gạch") || fp.name.ToLower().Contains("hatch") || fp.name.ToLower().Contains("caro") || fp.name.ToLower().Contains("wc") || fp.name.ToLower().Contains("cross"))
                .ToList();

            // 3. Spot Elevation Types / Text Note Types
            var spotTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(SpotDimensionType))
                .Cast<SpotDimensionType>()
                .Select(st => new {
                    id = st.Id.Value,
                    name = st.Name
                })
                .ToList();

            var textTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(TextNoteType))
                .Cast<TextNoteType>()
                .Select(tt => new {
                    id = tt.Id.Value,
                    name = tt.Name
                })
                .ToList();

            return new { floorTypes, fillPatterns, spotTypes, textTypes };
        }
    }
}

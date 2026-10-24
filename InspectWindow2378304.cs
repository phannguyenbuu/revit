using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class InspectWindow2378304
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var w = doc.GetElement(new ElementId(2378304L)) as FamilyInstance;
            if (w == null) return new { error = "Window not found" };

            var sym = w.Symbol;
            var lp = w.Location as LocationPoint;
            var pt = lp?.Point;
            var sill = w.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)?.AsDouble() * FT2MM;

            return new {
                id = w.Id.Value,
                name = w.Name,
                family = sym?.Family?.Name,
                symbol = sym?.Name,
                symbolId = sym?.Id.Value,
                sillMm = sill,
                pt = pt != null ? $"({pt.X * FT2MM:F1}, {pt.Y * FT2MM:F1}, {pt.Z * FT2MM:F1})" : "None"
            };
        }
    }
}

using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestLowerOneBeam
    {
        private const double FT2MM = 304.8;
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var beam = doc.GetElement(new ElementId(2382666L)) as FamilyInstance;
            if (beam == null) return new { error = "Beam not found" };

            double beforeTop = beam.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_TOP)?.AsDouble() * FT2MM ?? 0;
            double beforeBottom = beam.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_BOTTOM)?.AsDouble() * FT2MM ?? 0;

            using (var tx = new Transaction(doc, "Test Lower Beam 100mm"))
            {
                tx.Start();
                var pZOff = beam.get_Parameter(BuiltInParameter.Z_OFFSET_VALUE);
                pZOff?.Set(-100.0 / FT2MM);
                tx.Commit();
            }

            double afterTop = beam.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_TOP)?.AsDouble() * FT2MM ?? 0;
            double afterBottom = beam.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_BOTTOM)?.AsDouble() * FT2MM ?? 0;
            var bb = beam.get_BoundingBox(null);

            return new {
                id = beam.Id.Value,
                before = new { top = beforeTop, bottom = beforeBottom },
                after = new { top = afterTop, bottom = afterBottom, bbMinZ = bb.Min.Z * FT2MM, bbMaxZ = bb.Max.Z * FT2MM }
            };
        }
    }
}

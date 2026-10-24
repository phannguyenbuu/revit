using System;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestChangeParam25
    {
        public static object Run(UIApplication app, System.Text.Json.JsonElement args)
        {
            var doc = app.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };
            var win = doc.GetElement(new ElementId(2361245L)) as FamilyInstance;
            if (win == null) return new { error = "No win" };

            var sym = win.Symbol;
            var p25 = sym.LookupParameter("25");
            if (p25 == null) return new { error = "Param 25 not found" };

            double origVal = p25.AsDouble();

            // Try changing to 0.0 in a transaction and see what happens to solids
            var opt = new Options { DetailLevel = ViewDetailLevel.Fine };
            
            using var t = new Transaction(doc, "Test Change 25");
            var failureOptions = t.GetFailureHandlingOptions();
            failureOptions.SetFailuresPreprocessor(new WarningSwallower());
            t.SetFailureHandlingOptions(failureOptions);

            t.Start();
            p25.Set(0.0);
            doc.Regenerate();

            var geom = win.get_Geometry(opt);
            var solids = new List<object>();
            if (geom != null)
            {
                foreach (var obj in geom)
                {
                    if (obj is GeometryInstance gi)
                    {
                        foreach (var so in gi.GetInstanceGeometry())
                        {
                            if (so is Solid s && s.Volume > 0.00001)
                            {
                                var bb = s.GetBoundingBox();
                                solids.Add(new
                                {
                                    vol = s.Volume * Math.Pow(304.8, 3) / 1e6,
                                    min = $"[{bb.Min.X * 304.8:F1}, {bb.Min.Y * 304.8:F1}, {bb.Min.Z * 304.8:F1}]",
                                    max = $"[{bb.Max.X * 304.8:F1}, {bb.Max.Y * 304.8:F1}, {bb.Max.Z * 304.8:F1}]",
                                    widthX = (bb.Max.X - bb.Min.X) * 304.8,
                                    thickY = (bb.Max.Y - bb.Min.Y) * 304.8,
                                    heightZ = (bb.Max.Z - bb.Min.Z) * 304.8
                                });
                            }
                        }
                    }
                }
            }

            // Rollback test
            t.RollBack();

            return new
            {
                origValMm = origVal * 304.8,
                solidsWhenZero = solids
            };
        }

        private class WarningSwallower : IFailuresPreprocessor
        {
            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                var msgs = failuresAccessor.GetFailureMessages();
                foreach (var msg in msgs)
                {
                    if (msg.GetSeverity() == FailureSeverity.Warning)
                    {
                        failuresAccessor.DeleteWarning(msg);
                    }
                }
                return FailureProcessingResult.Continue;
            }
        }
    }
}

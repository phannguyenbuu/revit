using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestAdjustDimTextPosition
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        private const double FT_TO_MM = 304.8;

        public class WarningSwallower : IFailuresPreprocessor
        {
            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                failuresAccessor.DeleteAllWarnings();
                return FailureProcessingResult.Continue;
            }
        }

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No view" };

            // Find dim at Y = 3000
            var dims = new FilteredElementCollector(doc, view.Id)
                .OfClass(typeof(Dimension))
                .Cast<Dimension>()
                .Where(d => d.Curve is Line l && Math.Abs(Math.Abs(l.Direction.X) - 1.0) < 0.1 && Math.Abs(l.Origin.Y * FT_TO_MM - 3000) < 100)
                .ToList();

            var dim = dims.FirstOrDefault();
            if (dim == null) return new { error = "Dim at 3000 not found" };

            var segResults = new List<object>();

            using (var tx = new Transaction(doc, "Test Adjust Text Position"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);
                tx.Start();

                if (dim.Segments != null)
                {
                    bool up = true;
                    foreach (DimensionSegment seg in dim.Segments)
                    {
                        double valMm = seg.Value.HasValue ? Math.Round(seg.Value.Value * FT_TO_MM, 0) : 0;
                        bool adjustable = seg.IsTextPositionAdjustable();
                        var oldPos = seg.TextPosition;

                        if (valMm <= 250 && adjustable && oldPos != null)
                        {
                            double offsetMm = up ? 600.0 : -600.0;
                            up = !up; // alternate

                            XYZ newPos = new XYZ(oldPos.X, oldPos.Y + offsetMm * MM_TO_FT, oldPos.Z);
                            seg.TextPosition = newPos;

                            segResults.Add(new {
                                valMm,
                                oldY = Math.Round(oldPos.Y * FT_TO_MM, 1),
                                newY = Math.Round(seg.TextPosition.Y * FT_TO_MM, 1),
                                direction = offsetMm > 0 ? "UP" : "DOWN"
                            });
                        }
                    }
                }

                tx.Commit();
            }

            return new { dimId = dim.Id.Value, adjustedCount = segResults.Count, details = segResults.Take(10) };
        }
    }
}

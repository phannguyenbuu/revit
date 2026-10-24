using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class DetailedFailureCapture : IFailuresPreprocessor
    {
        public List<string> Messages { get; } = new List<string>();

        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            foreach (var m in failuresAccessor.GetFailureMessages())
            {
                Messages.Add($"{m.GetSeverity()}: {m.GetDescriptionText()}");
                if (m.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(m);
                }
            }
            return FailureProcessingResult.ProceedWithCommit;
        }
    }

    public static class TestMoveLevel2Only
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var lvl1 = levels.FirstOrDefault(l => l.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase));
            var lvl2 = levels.FirstOrDefault(l => l.Name.Equals("MẶT BẰNG TẦNG 2", StringComparison.OrdinalIgnoreCase));

            if (lvl1 == null || lvl2 == null) return new { error = "Levels not found" };

            double l1Before = Math.Round(lvl1.Elevation * FT2M, 4);
            double l2Before = Math.Round(lvl2.Elevation * FT2M, 4);

            var failCapture = new DetailedFailureCapture();

            using (var tx = new Transaction(doc, "Test Move Level 2"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(failCapture);
                opt.SetClearAfterRollback(true);
                tx.SetFailureHandlingOptions(opt);

                tx.Start();
                lvl2.Elevation = 3.900 * M2FT;
                doc.Regenerate();
                tx.Commit();
            }

            double l1After = Math.Round(lvl1.Elevation * FT2M, 4);
            double l2After = Math.Round(lvl2.Elevation * FT2M, 4);

            return new
            {
                l1Before,
                l2Before,
                l1After,
                l2After,
                messages = failCapture.Messages
            };
        }
    }
}

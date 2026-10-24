using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DiagnoseMoveLevel2
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            var lvl2 = doc.GetElement(new ElementId(694L)) as Level;
            if (lvl2 == null) return new { error = "Level 2 not found" };

            double elevBefore = lvl2.Elevation * FT2M;

            var log = new List<string>();
            log.Add($"Before: {elevBefore}m");

            TransactionStatus commitStatus;
            var failMessages = new List<string>();

            using (var tx = new Transaction(doc, "Diagnose Move Level 2"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new DiagnosticPreprocessor(failMessages));
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                lvl2.Elevation = 3.900 * M2FT;
                log.Add($"After set, before regen: {lvl2.Elevation * FT2M}m");

                try
                {
                    doc.Regenerate();
                    log.Add($"After regen, before commit: {lvl2.Elevation * FT2M}m");
                }
                catch (Exception ex)
                {
                    log.Add($"Regen threw: {ex.Message}");
                }

                commitStatus = tx.Commit();
                log.Add($"Commit status: {commitStatus}");
            }

            double elevAfter = lvl2.Elevation * FT2M;
            log.Add($"After transaction: {elevAfter}m");

            return new
            {
                elevBefore,
                elevAfter,
                commitStatus = commitStatus.ToString(),
                log,
                failMessages
            };
        }

        private class DiagnosticPreprocessor : IFailuresPreprocessor
        {
            private List<string> _messages;
            public DiagnosticPreprocessor(List<string> messages) => _messages = messages;

            public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
            {
                foreach (var f in failuresAccessor.GetFailureMessages())
                {
                    _messages.Add($"{f.GetSeverity()}: {f.GetDescriptionText()}");
                    if (f.GetSeverity() == FailureSeverity.Warning)
                    {
                        failuresAccessor.DeleteWarning(f);
                    }
                }
                return FailureProcessingResult.Continue;
            }
        }
    }
}

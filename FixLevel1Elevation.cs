using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FixLevel1Elevation
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var lvl1 = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => l.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase));

            if (lvl1 == null) return new { error = "Level 1 not found" };

            double oldElevM = lvl1.Elevation * FT2M;

            using (var tx = new Transaction(doc, "Reset Level 1 to 0.0"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new LevelAdjustmentWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();
                lvl1.Elevation = 0.0;
                doc.Regenerate();
                tx.Commit();
            }

            double newElevM = lvl1.Elevation * FT2M;

            // Also check all levels now
            var allLevels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .Select(l => new
                {
                    id = l.Id.Value,
                    name = l.Name,
                    elevM = Math.Round(l.Elevation * FT2M, 3),
                    elevMm = Math.Round(l.Elevation * FT2M * 1000.0, 1)
                })
                .ToList();

            return new { oldElevM, newElevM, allLevels };
        }
    }
}

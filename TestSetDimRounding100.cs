using System;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestSetDimRounding100
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

            try
            {
                var dimTypes = new FilteredElementCollector(doc)
                    .OfClass(typeof(DimensionType))
                    .Cast<DimensionType>()
                    .Where(dt => dt.StyleType == DimensionStyleType.Linear)
                    .ToList();

                var targetDt = dimTypes.FirstOrDefault(dt => dt.Name == "Linear Dimension Style") ?? dimTypes.First();
                var fo = targetDt.GetUnitsFormatOptions();
                bool beforeUseDef = fo.UseDefault;

                using (var tx = new Transaction(doc, "Set Dim Rounding 100mm"))
                {
                    var options = tx.GetFailureHandlingOptions();
                    options.SetFailuresPreprocessor(new WarningSwallower());
                    tx.SetFailureHandlingOptions(options);
                    tx.Start();

                    fo.UseDefault = false;
                    fo.Accuracy = 100.0 * MM_TO_FT; // 100 mm accuracy!
                    targetDt.SetUnitsFormatOptions(fo);

                    tx.Commit();
                }

                var afterFo = targetDt.GetUnitsFormatOptions();
                double afterAcc = afterFo.Accuracy;

                return new {
                    dtName = targetDt.Name,
                    beforeUseDef,
                    afterAccMm = afterAcc * FT_TO_MM,
                    afterUseDef = afterFo.UseDefault
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

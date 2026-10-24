using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FixDimUnitsToMillimeters100
    {
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
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var dimTypes = new FilteredElementCollector(doc)
                .OfClass(typeof(DimensionType))
                .Cast<DimensionType>()
                .Where(dt => dt.StyleType == DimensionStyleType.Linear)
                .ToList();

            var targetDt = dimTypes.FirstOrDefault(dt => dt.Name == "Linear Dimension Style") ?? dimTypes.First();

            using (var tx = new Transaction(doc, "Fix Dim Format to Millimeters 100"))
            {
                var options = tx.GetFailureHandlingOptions();
                options.SetFailuresPreprocessor(new WarningSwallower());
                tx.SetFailureHandlingOptions(options);
                tx.Start();

                var fo = new FormatOptions(UnitTypeId.Millimeters);
                fo.UseDefault = false;
                fo.Accuracy = 100.0;
                targetDt.SetUnitsFormatOptions(fo);

                tx.Commit();
            }

            var afterFo = targetDt.GetUnitsFormatOptions();
            return new {
                dtName = targetDt.Name,
                unitType = afterFo.GetUnitTypeId().TypeId,
                accuracy = afterFo.Accuracy,
                useDefault = afterFo.UseDefault
            };
        }
    }
}

import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding='utf-8')

code = """
using System;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FixLevel1Elevation
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var doc = uiapp.ActiveUIDocument?.Document;
            if (doc == null) return new { error = "No doc" };

            var lvl1 = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .FirstOrDefault(l => l.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase));

            if (lvl1 == null) return new { error = "Level 1 not found" };

            double oldElevM = lvl1.Elevation * 0.3048;

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

            double newElevM = lvl1.Elevation * 0.3048;

            return new { oldElevM, newElevM };
        }
    }
}
"""
print("FixLevel1 ready")

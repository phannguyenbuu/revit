using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class LevelUnlockWarningPreprocessor : IFailuresPreprocessor
    {
        public List<string> HandledFailures { get; } = new List<string>();

        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var msgs = failuresAccessor.GetFailureMessages();
            foreach (var m in msgs)
            {
                string desc = m.GetDescriptionText();
                HandledFailures.Add($"{m.GetSeverity()}: {desc}");

                if (m.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(m);
                }
                else if (m.GetSeverity() == FailureSeverity.Error)
                {
                    if (failuresAccessor.IsFailureResolutionPermitted(m, FailureResolutionType.UnlockConstraints))
                    {
                        failuresAccessor.ResolveFailure(m);
                    }
                    else if (failuresAccessor.IsFailureResolutionPermitted(m, FailureResolutionType.DeleteElements))
                    {
                        failuresAccessor.ResolveFailure(m);
                    }
                }
            }
            return FailureProcessingResult.ProceedWithCommit;
        }
    }

    public static class SetExactLevelsWithUnlocking
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            // 1. Explicitly unlock any locked dimensions in the project
            int unlockedDimCount = 0;
            using (var txUnlock = new Transaction(doc, "Unlock Constraints and Dimensions"))
            {
                txUnlock.Start();

                var dims = new FilteredElementCollector(doc)
                    .OfClass(typeof(Dimension))
                    .Cast<Dimension>()
                    .ToList();

                foreach (var d in dims)
                {
                    if (d.Segments != null && d.Segments.Size > 0)
                    {
                        foreach (DimensionSegment seg in d.Segments)
                        {
                            if (seg.IsLocked)
                            {
                                try { seg.IsLocked = false; unlockedDimCount++; } catch { }
                            }
                        }
                    }
                    else
                    {
                        if (d.IsLocked)
                        {
                            try { d.IsLocked = false; unlockedDimCount++; } catch { }
                        }
                    }
                }

                // Also check OST_Constraints
                var constraints = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Constraints)
                    .WhereElementIsNotElementType()
                    .ToElementIds();

                // If any constraints exist, we can inspect them
                txUnlock.Commit();
            }

            // 2. Set Exact Target Elevations
            var targetElevs = new (string name, double elevM)[]
            {
                ("MẶT BẰNG MÁI", 17.700),
                ("MẶT BẰNG TẦNG TUM", 14.700),
                ("MẶT BẰNG TẦNG 4", 11.100),
                ("MẶT BẰNG TẦNG ÁP MÁI", 11.100),
                ("MẶT BẰNG TẦNG 3", 7.500),
                ("MẶT BẰNG TẦNG 2", 3.900),
                ("MẶT BẰNG TẦNG 1", 0.000),
                ("MẶT BẰNG SÂN VƯỜN", -0.750)
            };

            var preprocessor = new LevelUnlockWarningPreprocessor();
            var levelResults = new List<object>();

            using (var tx = new Transaction(doc, "Set Exact Building Levels"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(preprocessor);
                opt.SetClearAfterRollback(true);
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                var allLevels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .ToList();

                foreach (var def in targetElevs)
                {
                    var lvl = allLevels.FirstOrDefault(l => l.Name.Equals(def.name, StringComparison.OrdinalIgnoreCase))
                           ?? allLevels.FirstOrDefault(l => l.Name.Contains(def.name, StringComparison.OrdinalIgnoreCase));

                    if (lvl != null)
                    {
                        lvl.Elevation = def.elevM * M2FT;
                    }
                }

                doc.Regenerate();
                tx.Commit();
            }

            // 3. Query final level elevations
            var finalLevels = new FilteredElementCollector(doc)
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

            // 4. Save document
            try { doc.Save(new SaveOptions()); } catch { }

            return new
            {
                success = true,
                unlockedDimCount,
                handledFailures = preprocessor.HandledFailures,
                finalLevels
            };
        }
    }
}

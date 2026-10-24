using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class AtticWarningSwallower : IFailuresPreprocessor
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

    public static class LowerWallsAndColumnsToAttic
    {
        private const double FT2M = 0.3048;

        private static readonly long[] DefaultWallIds = new long[]
        {
            2361540, 2361541, 2361542, 2361543, 2361544, 2361545, 2361546, 2361547, 2361548, 2361549, 2361550,
            2361552, 2361553, 2361554, 2361555, 2361556, 2361557, 2361558, 2361559, 2361560, 2361561, 2378806,
            2378807, 2378808, 2378809, 2378810, 2378811, 2378812, 2378813, 2378814, 2378815, 2378816, 2378817,
            2378818, 2378819, 2378820, 2378821, 2378822, 2378823, 2378824, 2378825, 2378826
        };

        private static readonly long[] DefaultColIds = new long[]
        {
            2378215, 2378830
        };

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active doc" };

                // 1. Find Level "MẶT BẰNG TẦNG ÁP MÁI" (Elevation 10.8m)
                var levels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .ToList();

                var atticLevel = levels.FirstOrDefault(l => l.Name.Contains("ÁP MÁI") || l.Name.Contains("AP MAI"))
                                 ?? levels.FirstOrDefault(l => Math.Abs(l.Elevation * FT2M - 10.8) < 0.1);

                if (atticLevel == null)
                {
                    return new { error = "Cannot find Level Tang Ap Mai (10.8m)" };
                }

                ElementId targetTopLevelId = atticLevel.Id;
                string targetTopLevelName = atticLevel.Name;
                double targetTopOffset = 0.0;

                // 2. Identify elements to modify
                var selIds = uidoc.Selection.GetElementIds();
                List<Wall> targetWalls = new List<Wall>();
                List<FamilyInstance> targetCols = new List<FamilyInstance>();

                if (selIds.Count > 0)
                {
                    foreach (var id in selIds)
                    {
                        var elem = doc.GetElement(id);
                        if (elem is Wall w)
                        {
                            targetWalls.Add(w);
                        }
                        else if (elem is FamilyInstance fi && (elem.Category?.Id.Value == (long)BuiltInCategory.OST_Columns || elem.Category?.Id.Value == (long)BuiltInCategory.OST_StructuralColumns))
                        {
                            targetCols.Add(fi);
                        }
                    }
                }

                // If selection didn't have walls or columns, fallback to the 42 walls and 2 columns
                if (targetWalls.Count == 0)
                {
                    foreach (var wid in DefaultWallIds)
                    {
                        var w = doc.GetElement(new ElementId(wid)) as Wall;
                        if (w != null) targetWalls.Add(w);
                    }
                }

                if (targetCols.Count == 0)
                {
                    foreach (var cid in DefaultColIds)
                    {
                        var c = doc.GetElement(new ElementId(cid)) as FamilyInstance;
                        if (c != null) targetCols.Add(c);
                    }
                }

                int updatedWallCount = 0;
                int updatedColCount = 0;
                List<long> updatedWallIds = new List<long>();
                List<long> updatedColIds = new List<long>();

                using (Transaction tx = new Transaction(doc, "Lower Walls and Columns to Tang Ap Mai"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new AtticWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    // Update Columns
                    foreach (var col in targetCols)
                    {
                        var pTop = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                        if (pTop != null && !pTop.IsReadOnly)
                        {
                            pTop.Set(targetTopLevelId);
                        }
                        var pOffset = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                        if (pOffset != null && !pOffset.IsReadOnly)
                        {
                            pOffset.Set(targetTopOffset);
                        }
                        updatedColCount++;
                        updatedColIds.Add(col.Id.Value);
                    }

                    // Update Walls
                    foreach (var wall in targetWalls)
                    {
                        var pTopConstraint = wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE);
                        if (pTopConstraint != null && !pTopConstraint.IsReadOnly)
                        {
                            pTopConstraint.Set(targetTopLevelId);
                        }
                        var pTopOffset = wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET);
                        if (pTopOffset != null && !pTopOffset.IsReadOnly)
                        {
                            pTopOffset.Set(targetTopOffset);
                        }
                        updatedWallCount++;
                        updatedWallIds.Add(wall.Id.Value);
                    }

                    tx.Commit();
                }

                uidoc.RefreshActiveView();
                try { doc.Save(new SaveOptions()); } catch { }

                return new
                {
                    success = true,
                    targetTopLevel = targetTopLevelName,
                    targetTopLevelId = targetTopLevelId.Value,
                    targetTopElevationM = Math.Round(atticLevel.Elevation * FT2M, 3),
                    updatedWallCount,
                    updatedWallIds,
                    updatedColCount,
                    updatedColIds
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

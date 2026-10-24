using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class OffsetWarningSwallower : IFailuresPreprocessor
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

    public static class AddTopOffsetToWallsAndColumns
    {
        private const double FT2M = 0.3048;
        private const double M2FT = 1.0 / 0.3048;

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

                double deltaOffsetM = 1.5; // 1500 mm
                if (args.ValueKind == JsonValueKind.Object && args.TryGetProperty("deltaOffsetM", out var pDelta))
                {
                    deltaOffsetM = pDelta.GetDouble();
                }
                double deltaOffsetFt = deltaOffsetM * M2FT;

                var selIds = uidoc.Selection.GetElementIds();
                List<Wall> targetWalls = new List<Wall>();
                List<FamilyInstance> targetCols = new List<FamilyInstance>();

                if (selIds.Count > 0)
                {
                    foreach (var id in selIds)
                    {
                        var elem = doc.GetElement(id);
                        if (elem is Wall w) targetWalls.Add(w);
                        else if (elem is FamilyInstance fi && (elem.Category?.Id.Value == (long)BuiltInCategory.OST_Columns || elem.Category?.Id.Value == (long)BuiltInCategory.OST_StructuralColumns))
                        {
                            targetCols.Add(fi);
                        }
                    }
                }

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
                List<object> updatedWallsInfo = new List<object>();
                List<object> updatedColsInfo = new List<object>();

                using (Transaction tx = new Transaction(doc, "Add 1500mm Top Offset to Walls and Columns"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new OffsetWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    // Columns
                    foreach (var col in targetCols)
                    {
                        var pOffset = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                        if (pOffset != null && !pOffset.IsReadOnly)
                        {
                            double currentOffset = pOffset.AsDouble();
                            // If current offset is 0, set to deltaOffsetFt (1.5m). If already has offset, add deltaOffsetFt
                            double newOffset = currentOffset + deltaOffsetFt;
                            pOffset.Set(newOffset);

                            updatedColsInfo.Add(new
                            {
                                id = col.Id.Value,
                                oldOffsetMm = Math.Round(currentOffset * FT2M * 1000, 1),
                                newOffsetMm = Math.Round(newOffset * FT2M * 1000, 1)
                            });
                            updatedColCount++;
                        }
                    }

                    // Walls
                    foreach (var wall in targetWalls)
                    {
                        var pOffset = wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET);
                        if (pOffset != null && !pOffset.IsReadOnly)
                        {
                            double currentOffset = pOffset.AsDouble();
                            double newOffset = currentOffset + deltaOffsetFt;
                            pOffset.Set(newOffset);

                            updatedWallsInfo.Add(new
                            {
                                id = wall.Id.Value,
                                oldOffsetMm = Math.Round(currentOffset * FT2M * 1000, 1),
                                newOffsetMm = Math.Round(newOffset * FT2M * 1000, 1)
                            });
                            updatedWallCount++;
                        }
                    }

                    tx.Commit();
                }

                uidoc.RefreshActiveView();
                try { doc.Save(new SaveOptions()); } catch { }

                return new
                {
                    success = true,
                    deltaOffsetMm = deltaOffsetM * 1000,
                    updatedWallCount,
                    updatedColCount,
                    sampleWall = updatedWallsInfo.FirstOrDefault(),
                    sampleCol = updatedColsInfo.FirstOrDefault()
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

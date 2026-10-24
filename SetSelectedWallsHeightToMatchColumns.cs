using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class WallWarningSwallower : IFailuresPreprocessor
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

    public static class SetSelectedWallsHeightToMatchColumns
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active doc" };

                var selIds = uidoc.Selection.GetElementIds();
                if (selIds.Count == 0) return new { error = "Selection is empty" };

                // 1. Find column(s) in selection
                ElementId targetTopLevelId = null;
                double targetTopOffset = 0.0;
                string targetTopLevelName = "";

                var cols = selIds
                    .Select(id => doc.GetElement(id))
                    .Where(e => e != null && (e.Category?.Id.Value == (long)BuiltInCategory.OST_Columns || e.Category?.Id.Value == (long)BuiltInCategory.OST_StructuralColumns))
                    .ToList();

                if (cols.Count > 0)
                {
                    var col = cols.First();
                    var pTop = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                    if (pTop != null && pTop.HasValue)
                    {
                        targetTopLevelId = pTop.AsElementId();
                        var lvl = doc.GetElement(targetTopLevelId) as Level;
                        targetTopLevelName = lvl?.Name ?? targetTopLevelId.Value.ToString();
                    }
                    var pOffset = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                    if (pOffset != null && pOffset.HasValue)
                    {
                        targetTopOffset = pOffset.AsDouble();
                    }
                }

                if (targetTopLevelId == null)
                {
                    // Fallback to Tang Tum level (14.4m)
                    var lvlTum = new FilteredElementCollector(doc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .FirstOrDefault(l => Math.Abs(l.Elevation * FT2M - 14.4) < 0.1);
                    if (lvlTum != null)
                    {
                        targetTopLevelId = lvlTum.Id;
                        targetTopLevelName = lvlTum.Name;
                    }
                }

                if (targetTopLevelId == null) return new { error = "Could not determine target top level from columns" };

                // 2. Find all walls in selection
                var walls = selIds
                    .Select(id => doc.GetElement(id) as Wall)
                    .Where(w => w != null)
                    .ToList();

                if (walls.Count == 0) return new { error = "No walls found in selection" };

                int updatedCount = 0;
                List<long> updatedWallIds = new List<long>();

                using (Transaction tx = new Transaction(doc, "Match Walls Height to Columns"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new WallWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    foreach (var wall in walls)
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

                        updatedCount++;
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
                    targetTopOffsetM = targetTopOffset * FT2M,
                    updatedWallCount = updatedCount,
                    updatedWallIds
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

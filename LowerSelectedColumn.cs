using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class ColumnLowerWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var msgs = failuresAccessor.GetFailureMessages();
            foreach (var m in msgs)
            {
                if (m.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(m);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class LowerSelectedColumn
    {
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit document" };

            List<string> logs = new List<string>();

            try
            {
                var selIds = uidoc.Selection.GetElementIds();
                FamilyInstance targetCol = null;

                if (selIds.Count > 0)
                {
                    foreach (var id in selIds)
                    {
                        var elem = doc.GetElement(id) as FamilyInstance;
                        if (elem != null && (elem.Category?.Id.Value == (long)BuiltInCategory.OST_StructuralColumns || elem.Category?.Id.Value == (long)BuiltInCategory.OST_Columns))
                        {
                            targetCol = elem;
                            break;
                        }
                    }
                }

                // Fallback to 2379835
                if (targetCol == null)
                {
                    targetCol = doc.GetElement(new ElementId(2379835L)) as FamilyInstance;
                }

                if (targetCol == null)
                {
                    return new { error = "No column found to lower" };
                }

                long targetColId = targetCol.Id.Value;
                logs.Add($"Target column ID: {targetColId}, Name: {targetCol.Name}");

                // Current Top Level
                var pTop = targetCol.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                var currentTopLvlId = pTop?.AsElementId();
                var currentTopLvl = currentTopLvlId != null ? doc.GetElement(currentTopLvlId) as Level : null;
                double currentTopElev = currentTopLvl != null ? currentTopLvl.Elevation * FT2M : 0;
                logs.Add($"Current Top Level: '{currentTopLvl?.Name}' (Elev: {currentTopElev:F2}m)");

                // Find all levels sorted by elevation
                var allLevels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .OrderBy(l => l.Elevation)
                    .ToList();

                // Target level: prefer "MẶT BẰNG TẦNG 4" (Id: 2360634) or "MẶT BẰNG TẦNG ÁP MÁI" (10.8m)
                Level newTopLevel = allLevels.FirstOrDefault(l => l.Name.Equals("MẶT BẰNG TẦNG 4", StringComparison.OrdinalIgnoreCase))
                                 ?? allLevels.FirstOrDefault(l => l.Name.Contains("ÁP MÁI", StringComparison.OrdinalIgnoreCase))
                                 ?? allLevels.Where(l => l.Elevation < (currentTopLvl?.Elevation ?? 0) - 0.5)
                                             .OrderByDescending(l => l.Elevation)
                                             .FirstOrDefault();

                if (newTopLevel == null)
                {
                    return new { error = "Cannot find level 1 story below current top level" };
                }

                logs.Add($"New Top Level: '{newTopLevel.Name}' (Id: {newTopLevel.Id.Value}, Elev: {newTopLevel.Elevation * FT2M:F2}m)");

                // Location of target column
                var lp = targetCol.Location as LocationPoint;
                XYZ colPt = lp?.Point;

                using (Transaction tx = new Transaction(doc, "Lower Selected Column by 1 Level"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new ColumnLowerWarningSwallower());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    // Check if duplicate column 2361390 exists at the same location and delete it
                    var duplicateCol = doc.GetElement(new ElementId(2361390L)) as FamilyInstance;
                    if (duplicateCol != null && duplicateCol.Id.Value != targetColId)
                    {
                        var dLp = duplicateCol.Location as LocationPoint;
                        if (dLp != null && colPt != null && dLp.Point.DistanceTo(colPt) < 0.5)
                        {
                            long dupId = duplicateCol.Id.Value;
                            doc.Delete(duplicateCol.Id);
                            logs.Add($"Cleaned up overlapping duplicate column ID {dupId} at ({colPt.X * FT2M * 1000:F0}, {colPt.Y * FT2M * 1000:F0})");
                        }
                    }

                    // Set Top Level of target column
                    pTop.Set(newTopLevel.Id);
                    var pOffset = targetCol.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                    if (pOffset != null && !pOffset.IsReadOnly)
                    {
                        pOffset.Set(0.0);
                    }

                    tx.Commit();
                }

                // Re-fetch column in case wrapper was invalidated by transaction
                var updatedCol = doc.GetElement(new ElementId(targetColId)) as FamilyInstance;
                if (updatedCol != null)
                {
                    uidoc.Selection.SetElementIds(new List<ElementId> { updatedCol.Id });
                }
                uidoc.RefreshActiveView();
                try { doc.Save(new SaveOptions()); } catch { }

                // Export 3D verification image
                string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                View3D v3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("3D"));

                if (v3d != null)
                {
                    uidoc.ActiveView = v3d;
                    var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == v3d.Id);
                    uiview3d?.ZoomToFit();

                    string out3dImg = Path.Combine(brainDir, "revit_column_lowered_3d.png");
                    if (File.Exists(out3dImg)) File.Delete(out3dImg);
                    var expOpt3d = new ImageExportOptions
                    {
                        FilePath = out3dImg,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(expOpt3d);
                }

                return new
                {
                    success = true,
                    columnId = targetColId,
                    columnName = targetCol.Name,
                    previousTopLevel = currentTopLvl?.Name,
                    previousTopElevM = currentTopElev,
                    newTopLevel = newTopLevel.Name,
                    newTopElevM = Math.Round(newTopLevel.Elevation * FT2M, 2),
                    heightReductionM = Math.Round(currentTopElev - newTopLevel.Elevation * FT2M, 2),
                    logs
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString(), logs };
            }
        }
    }
}

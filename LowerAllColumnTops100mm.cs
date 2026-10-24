using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class ColumnLowerFailurePreprocessor : IFailuresPreprocessor
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

    public static class LowerAllColumnTops100mm
    {
        private const double MM2FT = 1.0 / 304.8;
        private const double FT2MM = 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active Revit document" };

            List<string> logs = new List<string>();
            List<string> exportedFiles = new List<string>();

            try
            {
                var structCols = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_StructuralColumns)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .ToList();

                var archCols = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Columns)
                    .WhereElementIsNotElementType()
                    .Cast<FamilyInstance>()
                    .ToList();

                var allCols = structCols.Concat(archCols).ToList();
                int modifiedCount = 0;
                var levelChanges = new Dictionary<string, int>();

                using (var tx = new Transaction(doc, "Lower All Column Tops 100mm"))
                {
                    var opt = tx.GetFailureHandlingOptions();
                    opt.SetFailuresPreprocessor(new ColumnLowerFailurePreprocessor());
                    tx.SetFailureHandlingOptions(opt);

                    tx.Start();

                    foreach (var col in allCols)
                    {
                        var pTopOff = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                        if (pTopOff != null && !pTopOff.IsReadOnly)
                        {
                            double currentOffsetMm = pTopOff.AsDouble() * FT2MM;
                            double newOffsetMm = currentOffsetMm - 100.0;
                            pTopOff.Set(newOffsetMm * MM2FT);
                            modifiedCount++;

                            var pTopLvl = col.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                            string topName = pTopLvl != null && pTopLvl.AsElementId() != ElementId.InvalidElementId
                                ? (doc.GetElement(pTopLvl.AsElementId())?.Name ?? "Unknown")
                                : "Unknown";

                            string key = $"{topName} (From {Math.Round(currentOffsetMm)}mm -> {Math.Round(newOffsetMm)}mm)";
                            if (!levelChanges.ContainsKey(key)) levelChanges[key] = 0;
                            levelChanges[key]++;
                        }
                    }

                    tx.Commit();
                }

                logs.Add($"Successfully lowered {modifiedCount} column tops by 100mm.");
                foreach (var kvp in levelChanges)
                {
                    logs.Add($"  {kvp.Key}: {kvp.Value} columns");
                }

                // Export verification images
                string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

                // 1. Export Section View MẶT CẮT 1-1 (ID 2388045)
                var secView = doc.GetElement(new ElementId(2388045L)) as ViewSection ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewSection))
                    .Cast<ViewSection>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("1-1"));

                if (secView != null)
                {
                    try { uidoc.ActiveView = secView; } catch {}
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == secView.Id);
                    uiview?.ZoomToFit();

                    string secPath = Path.Combine(outDir, "revit_section_1_1_columns_lowered.png");
                    if (File.Exists(secPath)) try { File.Delete(secPath); } catch {}

                    var secOpt = new ImageExportOptions
                    {
                        FilePath = secPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ShadowViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3200
                    };
                    doc.ExportImage(secOpt);
                    exportedFiles.Add(secPath);
                    logs.Add("Exported section view: " + secPath);
                }

                // 2. Export 3D View
                var view3D = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

                if (view3D != null)
                {
                    try { uidoc.ActiveView = view3D; } catch {}
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3D.Id);
                    uiview?.ZoomToFit();

                    string path3D = Path.Combine(outDir, "revit_3d_columns_lowered.png");
                    if (File.Exists(path3D)) try { File.Delete(path3D); } catch {}

                    var opt3D = new ImageExportOptions
                    {
                        FilePath = path3D,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ShadowViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(opt3D);
                    exportedFiles.Add(path3D);
                    logs.Add("Exported 3D view: " + path3D);
                }

                return new
                {
                    success = true,
                    modifiedCount,
                    levelChanges,
                    logs,
                    exportedFiles
                };
            }
            catch (Exception ex)
            {
                return new
                {
                    success = false,
                    error = ex.Message,
                    stackTrace = ex.StackTrace,
                    logs
                };
            }
        }
    }
}

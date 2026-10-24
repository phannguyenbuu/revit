using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class WhiteWarningSwallower : IFailuresPreprocessor
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

    public static class SetSanhWhiteStyle
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            List<string> logs = new List<string>();

            // 1. Transaction in Active Document to create/find pure white material and update project categories
            using (var tx = new Transaction(doc, "Set Sanh Style White Face Black Edge"))
            {
                var opt = tx.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(new WhiteWarningSwallower());
                tx.SetFailureHandlingOptions(opt);

                tx.Start();

                // Find or create pure white wall-style material
                Material whiteMat = new FilteredElementCollector(doc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .FirstOrDefault(m => m.Name.Equals("Vật liệu Tường Trắng (Sảnh)", StringComparison.OrdinalIgnoreCase));

                if (whiteMat == null)
                {
                    var id = Material.Create(doc, "Vật liệu Tường Trắng (Sảnh)");
                    whiteMat = (Material)doc.GetElement(id);
                }

                whiteMat.Color = new Color(255, 255, 255);
                whiteMat.Transparency = 0;
                whiteMat.Shininess = 0;
                whiteMat.Smoothness = 0;
                logs.Add($"White material ready: {whiteMat.Name} (RGB 255,255,255)");

                // Traverse all categories in project doc
                void ProcessCategory(Category cat, string prefix = "")
                {
                    if (cat == null) return;
                    string fullPath = string.IsNullOrEmpty(prefix) ? cat.Name : $"{prefix} > {cat.Name}";

                    // Check if relevant to Sanh
                    bool isSanh = fullPath.IndexOf("sanh", StringComparison.OrdinalIgnoreCase) >= 0
                               || fullPath.IndexOf("mai", StringComparison.OrdinalIgnoreCase) >= 0
                               || fullPath.IndexOf("bac", StringComparison.OrdinalIgnoreCase) >= 0
                               || fullPath.IndexOf("cot", StringComparison.OrdinalIgnoreCase) >= 0;

                    if (isSanh)
                    {
                        try
                        {
                            cat.LineColor = new Color(0, 0, 0);
                            cat.Material = whiteMat;
                            logs.Add($"Updated category: {fullPath} -> White face, Black line");
                        }
                        catch (Exception ex)
                        {
                            logs.Add($"Could not update {fullPath}: {ex.Message}");
                        }
                    }

                    foreach (Category sub in cat.SubCategories)
                    {
                        ProcessCategory(sub, fullPath);
                    }
                }

                foreach (Category c in doc.Settings.Categories)
                {
                    if (c.Name.IndexOf("Import", StringComparison.OrdinalIgnoreCase) >= 0
                        || c.Name.IndexOf("Generic", StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        ProcessCategory(c);
                    }
                }

                // 2. Also apply View Element Override on instance 2385103 for the active 3D view
                var inst = doc.GetElement(new ElementId(2385103)) as FamilyInstance;
                var v3d = uidoc.ActiveView as View3D ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

                if (inst != null && v3d != null)
                {
                    // Find solid fill pattern
                    var solidPattern = new FilteredElementCollector(doc)
                        .OfClass(typeof(FillPatternElement))
                        .Cast<FillPatternElement>()
                        .FirstOrDefault(f => f.GetFillPattern().IsSolidFill);

                    var ogs = new OverrideGraphicSettings();
                    ogs.SetProjectionLineColor(new Color(0, 0, 0));
                    ogs.SetProjectionLineWeight(1);
                    if (solidPattern != null)
                    {
                        ogs.SetSurfaceForegroundPatternId(solidPattern.Id);
                        ogs.SetSurfaceForegroundPatternColor(new Color(255, 255, 255));
                        ogs.SetSurfaceForegroundPatternVisible(true);
                    }
                    v3d.SetElementOverrides(inst.Id, ogs);
                    logs.Add($"Applied View Override on instance 2385103: Solid White fill + Black edges");
                }

                tx.Commit();
            }

            // 3. Export closeup and overview images to verify
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            List<string> exportedFiles = new List<string>();

            var view3D = uidoc.ActiveView as View3D ?? new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("{3D}"));

            if (view3D != null)
            {
                uidoc.ActiveView = view3D;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3D.Id);

                // Section box closeup
                using (var txBox = new Transaction(doc, "Porch Section Box"))
                {
                    txBox.Start();
                    view3D.DisplayStyle = DisplayStyle.FlatColors;
                    view3D.DetailLevel = ViewDetailLevel.Fine;
                    BoundingBoxXYZ sb = new BoundingBoxXYZ();
                    sb.Min = new XYZ(-7.5 * M2FT, 0.5 * M2FT, -1.0 * M2FT);
                    sb.Max = new XYZ(4.0 * M2FT, 12.5 * M2FT, 6.5 * M2FT);
                    view3D.SetSectionBox(sb);
                    view3D.IsSectionBoxActive = true;
                    txBox.Commit();
                }

                uiview?.ZoomToFit();

                string pathCloseup = Path.Combine(outDir, "revit_sanh_white_style_closeup.png");
                if (File.Exists(pathCloseup)) try { File.Delete(pathCloseup); } catch {}

                var opt = new ImageExportOptions
                {
                    FilePath = pathCloseup,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ShadowViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    ExportRange = ExportRange.CurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2560
                };
                doc.ExportImage(opt);
                exportedFiles.Add(pathCloseup);

                // Overview with section box off
                using (var txNoBox = new Transaction(doc, "Turn Off Section Box"))
                {
                    txNoBox.Start();
                    view3D.IsSectionBoxActive = false;
                    txNoBox.Commit();
                }

                uiview?.ZoomToFit();

                string pathOverview = Path.Combine(outDir, "revit_sanh_white_style_overview.png");
                if (File.Exists(pathOverview)) try { File.Delete(pathOverview); } catch {}

                opt.FilePath = pathOverview;
                doc.ExportImage(opt);
                exportedFiles.Add(pathOverview);
            }

            return new {
                success = true,
                logs,
                exportedFiles
            };
        }
    }
}

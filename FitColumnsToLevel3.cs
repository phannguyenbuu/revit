using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public class FitColumnWarningSwallower : IFailuresPreprocessor
    {
        public FailureProcessingResult PreprocessFailures(FailuresAccessor failuresAccessor)
        {
            var failures = failuresAccessor.GetFailureMessages();
            foreach (var f in failures)
            {
                if (f.GetSeverity() == FailureSeverity.Warning)
                {
                    failuresAccessor.DeleteWarning(f);
                }
            }
            return FailureProcessingResult.Continue;
        }
    }

    public static class FitColumnsToLevel3
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Find Level 4 (top of Level 3 walls, elevation 10.8m)
            Level level4 = doc.GetElement(new ElementId(2360634L)) as Level
                ?? doc.GetElement(new ElementId(931615L)) as Level
                ?? new FilteredElementCollector(doc).OfClass(typeof(Level)).Cast<Level>().FirstOrDefault(l => l.Name.Contains("TẦNG 4") || l.Name.Contains("ÁP MÁI"));

            if (level4 == null) return new { error = "Target level (Level 4 / Áp Mái) not found" };

            var cols = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_StructuralColumns)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>()
                .ToList();

            int updatedCount = 0;
            var errors = new List<string>();

            using (Transaction t = new Transaction(doc, "Fit Columns to Level 3 Top"))
            {
                var prep = new FitColumnWarningSwallower();
                var opt = t.GetFailureHandlingOptions();
                opt.SetFailuresPreprocessor(prep);
                t.SetFailureHandlingOptions(opt);

                t.Start();

                foreach (var c in cols)
                {
                    try
                    {
                        var pTop = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                        var pTopOff = c.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);

                        if (pTop != null && !pTop.IsReadOnly)
                        {
                            pTop.Set(level4.Id);
                            if (pTopOff != null && !pTopOff.IsReadOnly)
                            {
                                pTopOff.Set(0.0);
                            }
                            updatedCount++;
                        }
                        else
                        {
                            errors.Add($"Col {c.Id.Value}: pTop is null or read-only");
                        }
                    }
                    catch (Exception ex)
                    {
                        errors.Add($"Col {c.Id.Value}: {ex.Message}");
                    }
                }

                t.Commit();
            }

            // Export updated 3D view and Tang 3 plan view
            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string plan3dImgPath = Path.Combine(folder, "revit_3d_tang123.jpg");
            string plan3ImgPath = Path.Combine(folder, "plan_tang3_perfect.png");

            var view3d = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

            if (view3d != null)
            {
                uidoc.ActiveView = view3d;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                uiview?.ZoomToFit();

                try
                {
                    if (File.Exists(plan3dImgPath)) File.Delete(plan3dImgPath);
                    var expOpt3d = new ImageExportOptions
                    {
                        FilePath = plan3dImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2800
                    };
                    doc.ExportImage(expOpt3d);
                }
                catch { }
            }

            ViewPlan planTang3 = doc.GetElement(new ElementId(1727632L)) as ViewPlan;
            if (planTang3 != null)
            {
                uidoc.ActiveView = planTang3;
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTang3.Id);
                uiview?.ZoomToFit();

                try
                {
                    if (File.Exists(plan3ImgPath)) File.Delete(plan3ImgPath);
                    var expOptPlan = new ImageExportOptions
                    {
                        FilePath = plan3ImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3800
                    };
                    doc.ExportImage(expOptPlan);
                }
                catch { }
            }

            // Save document
            bool docSaved = false;
            try
            {
                doc.Save(new SaveOptions());
                docSaved = true;
            }
            catch { }

            return new
            {
                success = true,
                targetLevelName = level4.Name,
                targetElevationMeters = Math.Round(level4.Elevation * 0.3048, 3),
                totalCols = cols.Count,
                updatedCount,
                errors,
                docSaved,
                plan3dImgPath,
                plan3ImgPath
            };
        }
    }
}

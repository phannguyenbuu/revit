using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetToiletHatchStraight
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                var view = uidoc?.ActiveView as ViewPlan;
                if (doc == null || view == null) return new { error = "No active ViewPlan" };

                double spacing200 = 200.0 * MM_TO_FT;

                using (var tx = new Transaction(doc, "Set Toilet Hatch Straight 200x200"))
                {
                    var failOpt = tx.GetFailureHandlingOptions();
                    failOpt.SetFailuresPreprocessor(new WarningSwallower());
                    tx.SetFailureHandlingOptions(failOpt);

                    tx.Start();

                    // 1. Get or create straight 200x200 Model pattern
                    FillPatternElement? fpe200 = doc.GetElement(new ElementId(459L)) as FillPatternElement
                        ?? FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Model, "200mm Squares");

                    // Also update pattern 2406226 (ANGLE) to straight angle = 0.0 so both are straight
                    var fpeAngle = doc.GetElement(new ElementId(2406226L)) as FillPatternElement
                        ?? FillPatternElement.GetFillPatternElementByName(doc, FillPatternTarget.Model, "ANGLE");

                    var fpStraight = new FillPattern("200 x 200 thẳng", FillPatternTarget.Model, FillPatternHostOrientation.ToHost, 0.0, spacing200, spacing200);

                    if (fpeAngle != null)
                    {
                        fpeAngle.SetFillPattern(fpStraight);
                    }

                    FillPatternElement targetPat = fpe200 ?? fpeAngle;
                    if (targetPat == null)
                    {
                        targetPat = FillPatternElement.Create(doc, fpStraight);
                    }

                    // 2. Assign to Material WC
                    var matWc = doc.GetElement(new ElementId(107066L)) as Material
                        ?? new FilteredElementCollector(doc).OfClass(typeof(Material)).Cast<Material>()
                            .FirstOrDefault(m => m.Name.Equals("WC", StringComparison.OrdinalIgnoreCase));

                    if (matWc != null && targetPat != null)
                    {
                        matWc.SurfaceForegroundPatternId = targetPat.Id;
                        matWc.SurfaceForegroundPatternColor = new Color(120, 120, 120);
                    }

                    tx.Commit();
                }

                // 3. Export detailed zoom of WC area
                string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
                if (uiview != null)
                {
                    XYZ p3 = new XYZ(31000.0 * MM_TO_FT, 5000.0 * MM_TO_FT, 0);
                    XYZ p4 = new XYZ(38500.0 * MM_TO_FT, 14500.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(p3, p4);
                }

                string imgZoom = Path.Combine(outDir, "revit_zoom_wc_straight_verified.png");
                var optZoom = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = imgZoom,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 1800,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(optZoom);

                // Reset view to full plan and export
                if (uiview != null)
                {
                    XYZ pAll1 = new XYZ(-2000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                    XYZ pAll2 = new XYZ(39000.0 * MM_TO_FT, 16000.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(pAll1, pAll2);
                }

                string planImg = Path.Combine(outDir, "revit_tang1_floor_final_straight_verified.png");
                var optPlan = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = planImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 3000,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(optPlan);

                return new
                {
                    success = true,
                    pattern = "200mm Squares (thẳng, 0 độ)",
                    zoomWcImage = "revit_zoom_wc_straight_verified.png",
                    planImage = "revit_tang1_floor_final_straight_verified.png"
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportUpdatedViews
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            if (doc == null || view == null) return new { error = "No active ViewPlan" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);

            // 1. Zoom Band AB
            if (uiview != null)
            {
                XYZ p1 = new XYZ(-1000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                XYZ p2 = new XYZ(39000.0 * MM_TO_FT, 6000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p1, p2);
            }
            string imgAB = Path.Combine(outDir, "revit_zoom_band_ab_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgAB,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 2. Zoom Band CD with Stairs
            if (uiview != null)
            {
                XYZ p3 = new XYZ(-1000.0 * MM_TO_FT, 7000.0 * MM_TO_FT, 0);
                XYZ p4 = new XYZ(39000.0 * MM_TO_FT, 15000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p3, p4);
            }
            string imgCD = Path.Combine(outDir, "revit_zoom_band_cd_stairs_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgCD,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2500,
                ZoomType = ZoomFitType.FitToPage
            });

            // 3. Full floor plan overview
            if (uiview != null)
            {
                XYZ p5 = new XYZ(-12000.0 * MM_TO_FT, -6000.0 * MM_TO_FT, 0);
                XYZ p6 = new XYZ(46000.0 * MM_TO_FT, 21000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p5, p6);
            }
            string imgFull = Path.Combine(outDir, "revit_full_tang1_all_horizontal_and_exterior_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgFull,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 3000,
                ZoomType = ZoomFitType.FitToPage
            });

            return new { success = true, imgAB, imgCD, imgFull };
        }
    }
}

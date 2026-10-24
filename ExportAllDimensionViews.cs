using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportAllDimensionViews
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

            // 1. Zoom Tam Cap with arrow and step dims
            if (uiview != null)
            {
                XYZ p1 = new XYZ(36500.0 * MM_TO_FT, 3800.0 * MM_TO_FT, 0);
                XYZ p2 = new XYZ(41500.0 * MM_TO_FT, 9000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p1, p2);
            }
            string img1 = Path.Combine(outDir, "revit_zoom_tam_cap_with_dims_and_arrow.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = img1,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2000,
                ZoomType = ZoomFitType.FitToPage
            });

            // 2. Zoom West Sảnh chính & Facade dims
            if (uiview != null)
            {
                XYZ p3 = new XYZ(-10500.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                XYZ p4 = new XYZ(6000.0 * MM_TO_FT, 16000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p3, p4);
            }
            string img2 = Path.Combine(outDir, "revit_zoom_west_sanh_chinh_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = img2,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2000,
                ZoomType = ZoomFitType.FitToPage
            });

            // 3. Zoom South Facade dims (Trục 1 -> 11)
            if (uiview != null)
            {
                XYZ p5 = new XYZ(-2000.0 * MM_TO_FT, -5000.0 * MM_TO_FT, 0);
                XYZ p6 = new XYZ(39000.0 * MM_TO_FT, 5000.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p5, p6);
            }
            string img3 = Path.Combine(outDir, "revit_zoom_south_facade_dims.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = img3,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2400,
                ZoomType = ZoomFitType.FitToPage
            });

            // 4. Full Overview of Tang 1 with all 4 sides of 3-layer dimensions
            if (uiview != null)
            {
                XYZ p7 = new XYZ(-11000.0 * MM_TO_FT, -5000.0 * MM_TO_FT, 0);
                XYZ p8 = new XYZ(44500.0 * MM_TO_FT, 20500.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p7, p8);
            }
            string img4 = Path.Combine(outDir, "revit_full_tang1_3layer_dimensions.png");
            doc.ExportImage(new ImageExportOptions {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = img4,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 3000,
                ZoomType = ZoomFitType.FitToPage
            });

            return new {
                status = "Success",
                images = new[] { img1, img2, img3, img4 }
            };
        }
    }
}

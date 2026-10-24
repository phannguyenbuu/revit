using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportDetailZooms
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

                string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);

                // Zoom 1: Door D7-1 and P. Y Tế / Sảnh Chờ
                if (uiview != null)
                {
                    XYZ p1 = new XYZ(2000.0 * MM_TO_FT, 5000.0 * MM_TO_FT, 0);
                    XYZ p2 = new XYZ(12000.0 * MM_TO_FT, 14000.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(p1, p2);
                }

                string img1 = Path.Combine(outDir, "revit_zoom_d7_and_tile600.png");
                var opt1 = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = img1,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 1800,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(opt1);

                // Zoom 2: WC area (WC Nam, WC Nữ, tags D5, D2, S4, Angle hatch & 600x600 tile)
                if (uiview != null)
                {
                    XYZ p3 = new XYZ(31000.0 * MM_TO_FT, 5000.0 * MM_TO_FT, 0);
                    XYZ p4 = new XYZ(38500.0 * MM_TO_FT, 14500.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(p3, p4);
                }

                string img2 = Path.Combine(outDir, "revit_zoom_wc_angle_and_tags.png");
                var opt2 = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = img2,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 1800,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(opt2);

                // Reset view to full plan
                if (uiview != null)
                {
                    XYZ pAll1 = new XYZ(-2000.0 * MM_TO_FT, -2000.0 * MM_TO_FT, 0);
                    XYZ pAll2 = new XYZ(39000.0 * MM_TO_FT, 16000.0 * MM_TO_FT, 0);
                    uiview.ZoomAndCenterRectangle(pAll1, pAll2);
                }

                return new
                {
                    success = true,
                    zoomD7 = "revit_zoom_d7_and_tile600.png",
                    zoomWc = "revit_zoom_wc_angle_and_tags.png"
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

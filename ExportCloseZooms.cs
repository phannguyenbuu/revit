using System;
using System.IO;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportCloseZooms
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            var uiview = uidoc?.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view?.Id);
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            // 1. Close zoom South Facade axis 1 to 3
            if (uiview != null && doc != null)
            {
                uiview.ZoomAndCenterRectangle(new XYZ(-1500 * MM_TO_FT, -3000 * MM_TO_FT, 0), new XYZ(9000 * MM_TO_FT, 1000 * MM_TO_FT, 0));
                string imgSouthClose = Path.Combine(outDir, "revit_zoom_south_axis1_3.png");
                doc.ExportImage(new ImageExportOptions {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = imgSouthClose,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 2000,
                    ZoomType = ZoomFitType.FitToPage
                });

                // 2. Close zoom Band CD Stair 1 (axis 1 to 4)
                uiview.ZoomAndCenterRectangle(new XYZ(-1500 * MM_TO_FT, 8500 * MM_TO_FT, 0), new XYZ(12000 * MM_TO_FT, 17500 * MM_TO_FT, 0));
                string imgStairClose = Path.Combine(outDir, "revit_zoom_stair1_close.png");
                doc.ExportImage(new ImageExportOptions {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = imgStairClose,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 2000,
                    ZoomType = ZoomFitType.FitToPage
                });

                return new { success = true, imgSouthClose, imgStairClose };
            }

            return new { success = false };
        }
    }
}

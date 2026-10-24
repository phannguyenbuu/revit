using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportTamCapZoom
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

            if (uiview != null)
            {
                XYZ p1 = new XYZ(36000.0 * MM_TO_FT, 4500.0 * MM_TO_FT, 0);
                XYZ p2 = new XYZ(40500.0 * MM_TO_FT, 8700.0 * MM_TO_FT, 0);
                uiview.ZoomAndCenterRectangle(p1, p2);
            }

            string imgPath = Path.Combine(outDir, "revit_zoom_tam_cap_arrow.png");
            var opt = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 1800,
                ZoomType = ZoomFitType.FitToPage
            };
            doc.ExportImage(opt);

            return new { status = "Success", image = imgPath };
        }
    }
}

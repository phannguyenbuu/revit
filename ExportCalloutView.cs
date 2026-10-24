using System;
using System.IO;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportCalloutView
    {
        private const double MM_TO_FT = 1.0 / 304.8;
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView as ViewPlan;
            var uiview = uidoc?.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view?.Id);
            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            if (uiview != null && doc != null)
            {
                // Zoom around Stair 1 (callout 1)
                uiview.ZoomAndCenterRectangle(new XYZ(1000 * MM_TO_FT, 5000 * MM_TO_FT, 0), new XYZ(11000 * MM_TO_FT, 17500 * MM_TO_FT, 0));
                string imgCallout1 = Path.Combine(outDir, "revit_callout1_on_plan.png");
                doc.ExportImage(new ImageExportOptions {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = imgCallout1,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    PixelSize = 2000,
                    ZoomType = ZoomFitType.FitToPage
                });

                return new { success = true, imgCallout1 };
            }

            return new { success = false };
        }
    }
}

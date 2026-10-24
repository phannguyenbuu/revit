using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportK4Verification
    {
        private const double MM_TO_FT = 1.0 / 304.8;

        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            var viewsToZoom = new List<(long id, string name)>
            {
                (695L, "zoom_window_k4_tang2.png"),
                (1727632L, "zoom_window_k4_tang3.png"),
                (2409349L, "zoom_window_k4_tang4.png"),
            };

            var exported = new List<object>();

            // Bounding box around window K4 (X: 37150, Y: 6602)
            XYZ p1 = new XYZ(34000.0 * MM_TO_FT, 4500.0 * MM_TO_FT, 0);
            XYZ p2 = new XYZ(40000.0 * MM_TO_FT, 9000.0 * MM_TO_FT, 0);

            foreach (var item in viewsToZoom)
            {
                var v = doc.GetElement(new ElementId(item.id)) as ViewPlan;
                if (v == null) continue;

                // Temporarily activate view in UI to zoom
                try
                {
                    uidoc.ActiveView = v;
                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == v.Id);
                    if (uiview != null)
                    {
                        uiview.ZoomAndCenterRectangle(p1, p2);
                    }

                    string filePath = Path.Combine(outDir, item.name);
                    var opt = new ImageExportOptions
                    {
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        FilePath = filePath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        PixelSize = 2000,
                        ZoomType = ZoomFitType.FitToPage
                    };

                    doc.ExportImage(opt);
                    exported.Add(new { view = v.Name, filePath, status = "Success" });
                }
                catch (Exception ex)
                {
                    exported.Add(new { view = v.Name, error = ex.Message });
                }
            }

            return new { success = true, exported };
        }
    }
}

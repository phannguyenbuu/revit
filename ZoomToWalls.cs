using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ZoomToWalls
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var viewTang1 = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

            if (viewTang1 == null) return new { error = "No Tang 1 view" };

            uidoc.ActiveView = viewTang1;
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == viewTang1.Id);

            // Zoom to target area: X in [23m, 30m], Y in [6m, 16m]
            var minPt = new XYZ(23.0 * M2FT, 6.0 * M2FT, 0.0);
            var maxPt = new XYZ(30.0 * M2FT, 16.0 * M2FT, 0.0);
            uiview?.ZoomAndCenterRectangle(minPt, maxPt);

            string outPlan = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_walls_detail.png";
            if (File.Exists(outPlan)) { try { File.Delete(outPlan); } catch { } }

            var opt = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = outPlan,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 1920,
                ZoomType = ZoomFitType.FitToPage
            };

            doc.ExportImage(opt);

            return new
            {
                success = true,
                exported = outPlan
            };
        }
    }
}

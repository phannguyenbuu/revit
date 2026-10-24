using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportSquatCubicleZoom
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No view" };

            // Elements to focus on
            long[] ids = new long[] { 2405970, 2405971, 2405972, 2405973 };
            var elemIds = ids.Select(id => new ElementId(id)).ToList();
            var elems = elemIds.Select(id => doc.GetElement(id)).Where(e => e != null).ToList();

            double minX = (19900.0 - 1500.0) / 304.8;
            double maxX = (23000.0 + 1500.0) / 304.8;
            double minY = (12050.0 - 2500.0) / 304.8;
            double maxY = (12600.0 + 2000.0) / 304.8;

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
            if (uiview != null)
            {
                XYZ p1 = new XYZ(minX, minY, 0);
                XYZ p2 = new XYZ(maxX, maxY, 0);
                uiview.ZoomAndCenterRectangle(p1, p2);
            }

            try
            {
                uidoc.Selection.SetElementIds(elemIds);
            }
            catch { }

            string outPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_squat_cubicle_zoom.png";

            var opt = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = outPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                PixelSize = 2048,
                ShadowViewsFileType = ImageFileType.PNG,
                ZoomType = ZoomFitType.FitToPage
            };

            doc.ExportImage(opt);

            string actualPath = outPath;
            if (!File.Exists(actualPath))
            {
                string dir = Path.GetDirectoryName(outPath)!;
                string baseName = Path.GetFileNameWithoutExtension(outPath);
                var files = Directory.GetFiles(dir, baseName + "*.png");
                if (files.Length > 0) actualPath = files[0];
            }

            return new { success = true, path = actualPath };
        }
    }
}

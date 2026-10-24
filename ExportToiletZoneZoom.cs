using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportToiletZoneZoom
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No view" };

            // Find the placed fixtures
            long[] ids = new long[] {
                2405143, 2405144, 2405145, 2405146, 2405147,
                2405148, 2405149, 2405150, 2405151, 2405152
            };

            var elemIds = ids.Select(id => new ElementId(id)).ToList();
            var elems = elemIds.Select(id => doc.GetElement(id)).Where(e => e != null).ToList();

            double minX = elems.Min(e => (e.Location as LocationPoint).Point.X) - 2000 / 304.8;
            double maxX = elems.Max(e => (e.Location as LocationPoint).Point.X) + 2000 / 304.8;
            double minY = elems.Min(e => (e.Location as LocationPoint).Point.Y) - 2000 / 304.8;
            double maxY = elems.Max(e => (e.Location as LocationPoint).Point.Y) + 2000 / 304.8;

            // Zoom the active UI view to this area
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view.Id);
            if (uiview != null)
            {
                XYZ p1 = new XYZ(minX, minY, 0);
                XYZ p2 = new XYZ(maxX, maxY, 0);
                uiview.ZoomAndCenterRectangle(p1, p2);
            }

            string outPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_toilet_fixtures_plan_zoom.png";

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

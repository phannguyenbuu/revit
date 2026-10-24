using System;
using System.IO;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportActiveViewNow
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (doc == null || view == null) return new { error = "No view" };

            string outPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_current_screen_now.png";

            var opt = new ImageExportOptions
            {
                ExportRange = ExportRange.CurrentView,
                FilePath = outPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 1600,
                ShadowViewsFileType = ImageFileType.PNG,
                ZoomType = ZoomFitType.FitToPage
            };

            doc.ExportImage(opt);

            // Revit appends " - {3D}" or similar to FilePath if multiple or view name
            string actualPath = outPath;
            if (!File.Exists(actualPath))
            {
                string dir = Path.GetDirectoryName(outPath)!;
                string baseName = Path.GetFileNameWithoutExtension(outPath);
                var files = Directory.GetFiles(dir, baseName + "*.png");
                if (files.Length > 0) actualPath = files[0];
            }

            return new { success = true, path = actualPath, viewName = view.Name };
        }
    }
}

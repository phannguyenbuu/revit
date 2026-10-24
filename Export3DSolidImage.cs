using System;
using System.IO;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Export3DSolidImage
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (view == null) return new { error = "No view" };

            string outPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\6b3231cb-a162-4b81-b5ab-a8d3ad87f46e\revit_21_grids";
            if (args.ValueKind == JsonValueKind.Object && args.TryGetProperty("outPath", out var p))
            {
                outPath = p.GetString() ?? outPath;
            }

            var opts = new ImageExportOptions
            {
                FilePath = outPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ExportRange = ExportRange.CurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 1920
            };

            doc.ExportImage(opts);

            return new { success = true, path = outPath + ".png" };
        }
    }
}

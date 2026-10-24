using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FullPlanExporter
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active doc" };

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == uidoc.ActiveView.Id);
            uiview?.ZoomToFit();

            string outPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_full_plan_four_walls.png";
            var expOpt = new ImageExportOptions
            {
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 3000,
                FilePath = outPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                ExportRange = ExportRange.VisibleRegionOfCurrentView
            };
            doc.ExportImage(expOpt);
            return new { success = true, imagePath = outPath };
        }
    }
}

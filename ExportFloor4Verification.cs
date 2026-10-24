using System;
using System.IO;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportFloor4Verification
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var options = args.TryGetProperty("args", out var n) && n.ValueKind == System.Text.Json.JsonValueKind.Object ? n : args;

            long viewIdVal = 2409349L;
            if (options.TryGetProperty("viewId", out var vProp) && vProp.GetInt64() > 0)
                viewIdVal = vProp.GetInt64();

            string fileName = "floor_view_verification.png";
            if (options.TryGetProperty("fileName", out var fProp) && !string.IsNullOrWhiteSpace(fProp.GetString()))
                fileName = fProp.GetString()!;

            var view = doc.GetElement(new ElementId(viewIdVal)) as View;
            if (view == null) return new { error = $"No view {viewIdVal}" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string filePath = Path.Combine(outDir, fileName);

            var opt = new ImageExportOptions
            {
                ExportRange = ExportRange.SetOfViews,
                FilePath = filePath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 3000,
                ZoomType = ZoomFitType.FitToPage
            };
            opt.SetViewsAndSheets(new List<ElementId> { view.Id });

            try
            {
                doc.ExportImage(opt);
                return new { success = true, filePath = filePath, viewName = view.Name };
            }
            catch (Exception ex)
            {
                return new { success = false, error = ex.Message };
            }
        }
    }
}

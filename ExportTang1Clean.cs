using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportTang1Clean
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var viewTang1 = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && (v.Name.Contains("T?NG 1") || v.Name.Contains("TẦNG 1") || v.Name.Contains("Tret")));

            if (viewTang1 == null) return new { error = "Tang 1 view not found" };

            uidoc.ActiveView = viewTang1;
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == viewTang1.Id);
            uiview?.ZoomToFit();

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string path = Path.Combine(outDir, "revit_tang1_sanh_updated.png");
            if (File.Exists(path)) try { File.Delete(path); } catch {}

            var opt = new ImageExportOptions
            {
                FilePath = path,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ShadowViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ExportRange = ExportRange.CurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 2560
            };
            doc.ExportImage(opt);

            return new { success = true, viewName = viewTang1.Name, path };
        }
    }
}

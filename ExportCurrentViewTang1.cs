using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportCurrentViewTang1
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            var view = uidoc?.ActiveView;
            if (view == null) return new { error = "No active view" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string path = Path.Combine(outDir, "revit_current_active_view_tang1.png");
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
            return new { success = true, viewName = view.Name, path };
        }
    }
}

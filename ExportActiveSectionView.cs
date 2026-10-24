using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportActiveSectionView
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document" };

            var view = uidoc.ActiveView;
            if (view == null) return new { error = "No active view" };

            string outDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string path = Path.Combine(outDir, "current_active_section_view.png");
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
                PixelSize = 3000
            };
            doc.ExportImage(opt);

            return new { success = true, path, viewName = view.Name, viewId = view.Id.Value };
        }
    }
}

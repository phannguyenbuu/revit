using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Export3DViewImage
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var view3d = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate);

            if (view3d == null) return new { error = "No 3D view found" };

            // Switch to 3D view and zoom to fit
            uidoc.ActiveView = view3d;
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
            uiview?.ZoomToFit();

            string outPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_3d_new_building.jpg";
            if (File.Exists(outPath))
            {
                try { File.Delete(outPath); } catch { }
            }

            var opt = new ImageExportOptions
            {
                ExportRange = ExportRange.SetOfViews,
                FilePath = outPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 1920,
                ZoomType = ZoomFitType.FitToPage
            };
            opt.SetViewsAndSheets(new System.Collections.Generic.List<ElementId> { view3d.Id });

            doc.ExportImage(opt);

            return new
            {
                success = true,
                exportedPath = outPath,
                viewName = view3d.Name
            };
        }
    }
}

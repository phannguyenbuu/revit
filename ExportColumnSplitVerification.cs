using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportColumnSplitVerification
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            var view3d = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

            if (view3d == null) return new { error = "No 3D view" };

            uidoc.ActiveView = view3d;

            // Select ONLY the Tầng 2 column instance at Axis 5-A (Id 2383388) to showcase single floor selection
            var singleColId = new ElementId(2383388L);
            try
            {
                uidoc.Selection.SetElementIds(new List<ElementId> { singleColId });
            }
            catch { }

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
            uiview?.ZoomToFit();

            string out3d = Path.Combine(folder, "revit_single_column_level2_selected.png");
            if (File.Exists(out3d)) File.Delete(out3d);

            var opts = new ImageExportOptions
            {
                FilePath = out3d,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 3000
            };

            doc.ExportImage(opts);

            return new
            {
                success = true,
                selectedColumnId = singleColId.Value,
                image = out3d
            };
        }
    }
}

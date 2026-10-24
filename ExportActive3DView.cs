using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportActive3DView
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var view = uidoc.ActiveView as View3D ?? new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .FirstOrDefault(v => !v.IsTemplate);

            if (view == null) return new { error = "No 3D view" };

            using (var tx = new Transaction(doc, "Set FlatColors"))
            {
                tx.Start();
                view.DisplayStyle = DisplayStyle.FlatColors;
                var vdm = view.GetViewDisplayModel();
                vdm.SmoothEdges = true;
                view.SetViewDisplayModel(vdm);
                tx.Commit();
            }

            try { doc.Save(); } catch { }

            uidoc.ActiveView = view;
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == view.Id);
            uiview?.ZoomToFit();

            string outPath = args.GetProperty("outputPath").GetString()!;
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
            opt.SetViewsAndSheets(new List<ElementId> { view.Id });

            doc.ExportImage(opt);

            return new
            {
                success = true,
                outputPath = outPath,
                viewName = view.Name,
                displayStyle = view.DisplayStyle.ToString()
            };
        }
    }
}

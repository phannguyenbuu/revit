using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ZoomToWindow2361245
    {
        public static object Run(UIApplication uiapp, System.Text.Json.JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var win = doc.GetElement(new ElementId(2361245L)) as FamilyInstance;
            if (win == null) return new { error = "Window not found" };

            // Find floor plan MẶT BẰNG TẦNG 1
            var planView = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && (v.Name.Contains("TẦNG 1") || v.Name.Contains("T?NG 1") || v.Id.Value == 312L));

            if (planView != null && uidoc.ActiveView.Id != planView.Id)
            {
                uidoc.ActiveView = planView;
            }

            // Select it and zoom
            uidoc.Selection.SetElementIds(new List<ElementId> { win.Id });
            
            var uiView = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == planView.Id);
            if (uiView != null)
            {
                double x = 6300.0 / 304.8;
                double y = 0.0 / 304.8;
                double dx = 1500.0 / 304.8;
                double dy = 800.0 / 304.8;
                uiView.ZoomAndCenterRectangle(new XYZ(x - dx, y - dy, 0), new XYZ(x + dx, y + dy, 0));
            }

            // Export active view to image
            var view = uidoc.ActiveView;
            string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string imgPath = Path.Combine(brainDir, "window_zoom_plan.png");
            if (File.Exists(imgPath)) File.Delete(imgPath);

            var opt = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = imgPath,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ZoomType = ZoomFitType.Zoom,
                PixelSize = 1600
            };

            doc.ExportImage(opt);

            return new
            {
                success = true,
                path = imgPath,
                viewName = view.Name
            };
        }
    }
}

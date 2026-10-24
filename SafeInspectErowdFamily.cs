using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SafeInspectErowdFamily
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // Switch to MẶT BẰNG TẦNG 1
            var plan = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase));
            if (plan != null && uidoc.ActiveView.Id != plan.Id)
            {
                uidoc.ActiveView = plan;
            }

            // Zoom to D1
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == (plan != null ? plan.Id : uidoc.ActiveView.Id));
            if (uiview != null)
            {
                var minPt = new XYZ(-1.5 * M2FT, 3.5 * M2FT, 0.0);
                var maxPt = new XYZ(4.0 * M2FT, 9.5 * M2FT, 0.0);
                uiview.ZoomAndCenterRectangle(minPt, maxPt);
            }

            // Clear selection
            uidoc.Selection.SetElementIds(new List<ElementId>());

            string outImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_d1_glass_hinge_clean.png";
            if (File.Exists(outImgPath)) File.Delete(outImgPath);

            var expOpt = new ImageExportOptions
            {
                FilePath = outImgPath,
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 2048,
                ImageResolution = ImageResolution.DPI_300,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG
            };
            doc.ExportImage(expOpt);

            string actualPath = outImgPath.Replace(".png", " - Floor Plan - MẶT BẰNG TẦNG 1.png");
            if (File.Exists(actualPath))
            {
                if (File.Exists(outImgPath)) File.Delete(outImgPath);
                File.Move(actualPath, outImgPath);
            }

            var d = doc.GetElement(new ElementId(2364731L)) as FamilyInstance;

            return new
            {
                success = true,
                doorId = d?.Id.Value,
                sym = d?.Symbol.Name,
                fam = d?.Symbol.FamilyName,
                img = outImgPath
            };
        }
    }
}

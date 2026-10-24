using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportPerfectTang2Plan
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            ViewPlan planTang2 = doc.GetElement(new ElementId(695L)) as ViewPlan;
            if (planTang2 == null) return new { error = "View 695 not found" };

            using (Transaction t = new Transaction(doc, "Set Perfect Crop Box"))
            {
                t.Start();

                // Building bounds:
                // X: 0.55m to 37.15m -> padded [-2.5m, 39.5m]
                // Y: 0.0m to 13.20m -> padded [-3.5m, 16.5m]
                var bb = planTang2.CropBox;
                var tr = bb.Transform;
                var inv = tr.Inverse;

                var pMinWorld = new XYZ(-2.5 * M2FT, -3.5 * M2FT, 0.0);
                var pMaxWorld = new XYZ(39.5 * M2FT, 16.5 * M2FT, 0.0);

                var pMinLocal = inv.OfPoint(pMinWorld);
                var pMaxLocal = inv.OfPoint(pMaxWorld);

                bb.Min = new XYZ(Math.Min(pMinLocal.X, pMaxLocal.X), Math.Min(pMinLocal.Y, pMaxLocal.Y), bb.Min.Z);
                bb.Max = new XYZ(Math.Max(pMinLocal.X, pMaxLocal.X), Math.Max(pMinLocal.Y, pMaxLocal.Y), bb.Max.Z);

                planTang2.CropBox = bb;
                planTang2.CropBoxActive = true;
                planTang2.CropBoxVisible = false;

                t.Commit();
            }

            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string planImgPath = Path.Combine(folder, "plan_tang2_perfect.png");

            uidoc.ActiveView = planTang2;
            uidoc.Selection.SetElementIds(new List<ElementId>());

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTang2.Id);
            uiview?.ZoomToFit();

            try
            {
                if (File.Exists(planImgPath)) File.Delete(planImgPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = planImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3800
                };
                doc.ExportImage(expOpt);
            }
            catch (Exception ex)
            {
                return new { error = "Export failed: " + ex.Message };
            }

            return new
            {
                success = true,
                planImgPath
            };
        }
    }
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportTang2CleanPlan
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                ViewPlan planTang2 = doc.GetElement(new ElementId(695L)) as ViewPlan;
                if (planTang2 == null) return new { error = "View 695 not found" };

                using (Transaction t = new Transaction(doc, "Adjust Tang 2 View Settings"))
                {
                    t.Start();
                    planTang2.CropBoxActive = false;
                    planTang2.CropBoxVisible = false;
                    t.Commit();
                }

                string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string planImgPath = Path.Combine(folder, "plan_tang2_clean.png");

                uidoc.ActiveView = planTang2;
                uidoc.Selection.SetElementIds(new List<ElementId>());

                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTang2.Id);
                uiview?.ZoomToFit();

                if (File.Exists(planImgPath)) File.Delete(planImgPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = planImgPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3500
                };
                doc.ExportImage(expOpt);

                return new
                {
                    success = true,
                    planImgPath
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

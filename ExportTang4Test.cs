using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportTang4Test
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            ViewPlan planTang4 = doc.GetElement(new ElementId(931687L)) as ViewPlan;
            if (planTang4 == null) return new { error = "View 931687 not found" };

            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

            // Test 1: Export with CropBoxActive = false
            using (Transaction t = new Transaction(doc, "Test Crop Off"))
            {
                t.Start();
                planTang4.CropBoxActive = false;
                t.Commit();
            }

            uidoc.ActiveView = planTang4;
            uidoc.Selection.SetElementIds(new List<ElementId>());
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTang4.Id);
            uiview?.ZoomToFit();

            string testPath1 = Path.Combine(folder, "test_tang4_nocrop.png");
            if (File.Exists(testPath1)) File.Delete(testPath1);
            var opt1 = new ImageExportOptions
            {
                FilePath = testPath1,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 3800
            };
            doc.ExportImage(opt1);

            // Test 2: Export with CurrentView
            string testPath2 = Path.Combine(folder, "test_tang4_currentview.png");
            if (File.Exists(testPath2)) File.Delete(testPath2);
            var opt2 = new ImageExportOptions
            {
                FilePath = testPath2,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_300,
                ExportRange = ExportRange.CurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 3800
            };
            doc.ExportImage(opt2);

            return new {
                success = true,
                test1 = testPath1,
                test2 = testPath2
            };
        }
    }
}

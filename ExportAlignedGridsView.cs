using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportAlignedGridsView
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var viewTang1 = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan && v.Name.Contains("TẦNG 1", StringComparison.OrdinalIgnoreCase));

            if (viewTang1 == null) return new { error = "No Tang 1 view" };

            using (var tx = new Transaction(doc, "Ensure Categories Visible"))
            {
                tx.Start();
                var cats = new[]
                {
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_StructuralColumns,
                    BuiltInCategory.OST_Grids,
                    BuiltInCategory.OST_Dimensions
                };
                foreach (var catId in cats)
                {
                    var cat = doc.Settings.Categories.get_Item(catId);
                    if (cat != null && viewTang1.GetCategoryHidden(cat.Id))
                    {
                        viewTang1.SetCategoryHidden(cat.Id, false);
                    }
                }
                tx.Commit();
            }

            uidoc.ActiveView = viewTang1;
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == viewTang1.Id);

            // 1. Full building view covering all grids (X: -2m to 40m, Y: -6m to 20m)
            var minPtFull = new XYZ(-2.0 * M2FT, -6.0 * M2FT, 0.0);
            var maxPtFull = new XYZ(40.0 * M2FT, 20.0 * M2FT, 0.0);
            uiview?.ZoomAndCenterRectangle(minPtFull, maxPtFull);

            string fullPlanImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_full_grids.png";
            if (File.Exists(fullPlanImg)) { try { File.Delete(fullPlanImg); } catch { } }

            var optFull = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = fullPlanImg,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2560,
                ZoomType = ZoomFitType.FitToPage
            };
            doc.ExportImage(optFull);

            // 2. Left side close-up (Trục 1, 2, 3, 4 with columns & walls)
            var minPtLeft = new XYZ(-1.0 * M2FT, -4.0 * M2FT, 0.0);
            var maxPtLeft = new XYZ(14.0 * M2FT, 17.0 * M2FT, 0.0);
            uiview?.ZoomAndCenterRectangle(minPtLeft, maxPtLeft);

            string leftPlanImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_left_closeup.png";
            if (File.Exists(leftPlanImg)) { try { File.Delete(leftPlanImg); } catch { } }

            var optLeft = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = leftPlanImg,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2048,
                ZoomType = ZoomFitType.FitToPage
            };
            doc.ExportImage(optLeft);

            // 3. Right side close-up (Trục 8, 9, 10, 11 with columns & walls)
            var minPtRight = new XYZ(24.0 * M2FT, -4.0 * M2FT, 0.0);
            var maxPtRight = new XYZ(39.0 * M2FT, 17.0 * M2FT, 0.0);
            uiview?.ZoomAndCenterRectangle(minPtRight, maxPtRight);

            string rightPlanImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_right_closeup.png";
            if (File.Exists(rightPlanImg)) { try { File.Delete(rightPlanImg); } catch { } }

            var optRight = new ImageExportOptions
            {
                ExportRange = ExportRange.VisibleRegionOfCurrentView,
                FilePath = rightPlanImg,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                PixelSize = 2048,
                ZoomType = ZoomFitType.FitToPage
            };
            doc.ExportImage(optRight);

            // Restore zoom to full building
            uiview?.ZoomAndCenterRectangle(minPtFull, maxPtFull);

            return new
            {
                success = true,
                fullPlan = fullPlanImg,
                leftPlan = leftPlanImg,
                rightPlan = rightPlanImg
            };
        }
    }
}

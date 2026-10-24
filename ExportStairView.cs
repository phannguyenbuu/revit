using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportStairView
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var plan = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 1", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("TẦNG 1"));

            if (plan == null) return new { error = "View MẶT BẰNG TẦNG 1 not found" };

            if (uidoc.ActiveView.Id != plan.Id)
            {
                uidoc.ActiveView = plan;
            }

            var stairs = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Stairs)
                .WhereElementIsNotElementType()
                .Cast<Stairs>()
                .FirstOrDefault();

            if (stairs != null)
            {
                uidoc.Selection.SetElementIds(new List<ElementId> { stairs.Id });
            }

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == plan.Id);
            // Stair is located at X in [4.45, 7.95], Y in [10.10, 14.80]
            var minPt = new XYZ(3.5 * M2FT, 9.0 * M2FT, 0.0);
            var maxPt = new XYZ(9.0 * M2FT, 16.0 * M2FT, 0.0);
            uiview?.ZoomAndCenterRectangle(minPt, maxPt);

            string planImgPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_stair_plan.png";
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
                    PixelSize = 3000
                };
                doc.ExportImage(expOpt);
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }

            return new { success = true, image = planImgPath, stairId = stairs?.Id.Value };
        }
    }
}

using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class DiagnoseWindowK2InPlan
    {
        private const double M2FT = 3.2808398950131235;
        private const double FT2M = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var plan = doc.GetElement(new ElementId(312)) as ViewPlan;
                if (plan == null) return new { error = "Plan 312 not found" };

                uidoc.ActiveView = plan;

                var vr = plan.GetViewRange();
                double cutM = vr.GetOffset(PlanViewPlane.CutPlane) * FT2M;
                double topM = vr.GetOffset(PlanViewPlane.TopClipPlane) * FT2M;
                double bottomM = vr.GetOffset(PlanViewPlane.BottomClipPlane) * FT2M;

                // Check Category Visibility of Windows in plan
                var winCat = doc.Settings.Categories.get_Item(BuiltInCategory.OST_Windows);
                bool winVisible = !plan.GetCategoryHidden(winCat.Id);

                // Check K2 Stack element
                var stack = doc.GetElement(new ElementId(2377860)) as FamilyInstance;
                bool stackHidden = stack != null && stack.IsHidden(plan);

                // Zoom to K2 stack
                XYZ pMin = new XYZ(-0.2 * M2FT, 11.2 * M2FT, 0);
                XYZ pMax = new XYZ(1.8 * M2FT, 13.8 * M2FT, 0);
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == plan.Id);
                uiview?.ZoomAndCenterRectangle(pMin, pMax);
                uidoc.RefreshActiveView();

                string outImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_k2_diagnose.png";
                if (File.Exists(outImg)) try { File.Delete(outImg); } catch { }

                var expOpt = new ImageExportOptions
                {
                    ExportRange = ExportRange.VisibleRegionOfCurrentView,
                    FilePath = outImg,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    PixelSize = 2500,
                    ZoomType = ZoomFitType.FitToPage
                };
                doc.ExportImage(expOpt);

                return new
                {
                    success = true,
                    planName = plan.Name,
                    cutM,
                    topM,
                    bottomM,
                    winVisible,
                    stackHidden,
                    stackLoc = (stack?.Location as LocationPoint)?.Point.ToString(),
                    outImg
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

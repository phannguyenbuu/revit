using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestExportPlanAndInspectK2
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

                var plan = uidoc.ActiveView as ViewPlan;
                if (plan == null) return new { error = "Active view is not plan" };

                var vr = plan.GetViewRange();
                double cutM = vr.GetOffset(PlanViewPlane.CutPlane) * FT2M;
                double topM = vr.GetOffset(PlanViewPlane.TopClipPlane) * FT2M;
                double bottomM = vr.GetOffset(PlanViewPlane.BottomClipPlane) * FT2M;
                double depthM = vr.GetOffset(PlanViewPlane.ViewDepthPlane) * FT2M;

                // Find stack element
                var stack = doc.GetElement(new ElementId(2377860));
                var bb = stack?.get_BoundingBox(plan);

                // Zoom to Truc 1 K2 location
                // X: [0, 2], Y: [11.5, 13.5]
                XYZ pMin = new XYZ(-0.5 * M2FT, 11.0 * M2FT, 0);
                XYZ pMax = new XYZ(2.5 * M2FT, 14.0 * M2FT, 0);
                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(uv => uv.ViewId == plan.Id);
                uiview?.ZoomAndCenterRectangle(pMin, pMax);
                uidoc.RefreshActiveView();

                string outImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_k2_zoom.png";
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
                    viewName = plan.Name,
                    cutM,
                    topM,
                    bottomM,
                    depthM,
                    stackFound = stack != null,
                    bbMinX = bb != null ? bb.Min.X * FT2M : 0,
                    bbMaxX = bb != null ? bb.Max.X * FT2M : 0,
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

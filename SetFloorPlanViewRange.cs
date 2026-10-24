using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class SetFloorPlanViewRange
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var activeView = uidoc.ActiveView as ViewPlan;
                if (activeView == null) return new { error = "Active view is not a Plan View" };

                // Desired Cut Plane Z offset (default 2.0m) and Top (default 2.5m)
                double newCutM = 2.0; // 2000 mm
                double newTopM = 2.5; // 2500 mm

                if (args.ValueKind == JsonValueKind.Object)
                {
                    if (args.TryGetProperty("cutM", out var cVal)) newCutM = cVal.GetDouble();
                    if (args.TryGetProperty("topM", out var tVal)) newTopM = tVal.GetDouble();
                }

                using (Transaction tx = new Transaction(doc, "Adjust Plan View Range Cut Plane"))
                {
                    tx.Start();

                    var vr = activeView.GetViewRange();
                    // Set Top first so Cut is always <= Top
                    vr.SetOffset(PlanViewPlane.TopClipPlane, newTopM * M2FT);
                    vr.SetOffset(PlanViewPlane.CutPlane, newCutM * M2FT);
                    activeView.SetViewRange(vr);

                    tx.Commit();
                }

                uidoc.RefreshActiveView();

                // Export an image of the updated floor plan around the K2 stack
                string outImg = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_tang1_k2_cut2000.png";
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
                    viewName = activeView.Name,
                    newCutM,
                    newTopM,
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

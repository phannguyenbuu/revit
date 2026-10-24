using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FixPlanTumVisibility
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var planTum = doc.GetElement(new ElementId(2370740)) as ViewPlan;
            if (planTum == null) return new { error = "PlanTum not found" };

            var floor = doc.GetElement(new ElementId(2381771)) as Floor;
            if (floor == null) return new { error = "Floor not found" };

            List<string> logs = new List<string>();

            using (Transaction t = new Transaction(doc, "Fix Tum View Visibility"))
            {
                t.Start();

                // 1. Unhide Floors category
                var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
                if (floorCat != null && planTum.CanCategoryBeHidden(floorCat.Id))
                {
                    bool isHidden = planTum.GetCategoryHidden(floorCat.Id);
                    logs.Add($"Floors category isHidden: {isHidden}");
                    if (isHidden) planTum.SetCategoryHidden(floorCat.Id, false);
                }

                // 2. Check if floor element is specifically hidden
                bool isElHidden = floor.IsHidden(planTum);
                logs.Add($"Floor element 2381771 IsHidden: {isElHidden}");
                if (isElHidden && floor.CanBeHidden(planTum))
                {
                    planTum.UnhideElements(new List<ElementId> { floor.Id });
                    logs.Add("Unhid floor element");
                }

                // 3. View Range
                var vr = planTum.GetViewRange();
                logs.Add($"ViewRange Bottom offset: {vr.GetOffset(PlanViewPlane.BottomClipPlane)} ft");
                logs.Add($"ViewRange ViewDepth offset: {vr.GetOffset(PlanViewPlane.ViewDepthPlane)} ft");
                logs.Add($"ViewRange CutPlane offset: {vr.GetOffset(PlanViewPlane.CutPlane)} ft");

                // Set bottom and view depth to -1.0 ft (-0.3m) so floor at -0.1m is well within view range
                vr.SetOffset(PlanViewPlane.BottomClipPlane, -1.0);
                vr.SetOffset(PlanViewPlane.ViewDepthPlane, -1.0);
                planTum.SetViewRange(vr);
                logs.Add("Updated ViewRange Bottom and ViewDepth to -1.0 ft");

                // 4. Ensure CropBox encompasses floor (X: 3m to 39m, Y: -2m to 16m)
                var bb = planTum.CropBox;
                var tr = bb.Transform;
                var inv = tr.Inverse;

                var pMinWorld = new XYZ(-2.0 * M2FT, -2.5 * M2FT, tr.Origin.Z);
                var pMaxWorld = new XYZ(39.5 * M2FT, 16.5 * M2FT, tr.Origin.Z);

                var pMinLocal = inv.OfPoint(pMinWorld);
                var pMaxLocal = inv.OfPoint(pMaxWorld);

                bb.Min = new XYZ(Math.Min(pMinLocal.X, pMaxLocal.X), Math.Min(pMinLocal.Y, pMaxLocal.Y), bb.Min.Z);
                bb.Max = new XYZ(Math.Max(pMinLocal.X, pMaxLocal.X), Math.Max(pMinLocal.Y, pMaxLocal.Y), bb.Max.Z);

                planTum.CropBox = bb;
                planTum.CropBoxActive = true;
                planTum.CropBoxVisible = false;

                t.Commit();
            }

            uidoc.ActiveView = planTum;
            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTum.Id);
            uiview?.ZoomToFit();

            string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string outPlanOverview = Path.Combine(brainDir, "revit_tum_slab_plan_overview.png");
            if (File.Exists(outPlanOverview)) File.Delete(outPlanOverview);

            var expOpt = new ImageExportOptions
            {
                FilePath = outPlanOverview,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ExportRange = ExportRange.CurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 2560
            };
            doc.ExportImage(expOpt);

            // Export close-up on hole (X: [4m, 9m], Y: [8m, 15m])
            using (Transaction t2 = new Transaction(doc, "Close Up Plan Tum Hole"))
            {
                t2.Start();

                var bb = planTum.CropBox;
                var tr = bb.Transform;
                var inv = tr.Inverse;

                var pMinWorld = new XYZ(3.5 * M2FT, 7.5 * M2FT, tr.Origin.Z);
                var pMaxWorld = new XYZ(10.5 * M2FT, 15.5 * M2FT, tr.Origin.Z);

                var pMinLocal = inv.OfPoint(pMinWorld);
                var pMaxLocal = inv.OfPoint(pMaxWorld);

                bb.Min = new XYZ(Math.Min(pMinLocal.X, pMaxLocal.X), Math.Min(pMinLocal.Y, pMaxLocal.Y), bb.Min.Z);
                bb.Max = new XYZ(Math.Max(pMinLocal.X, pMaxLocal.X), Math.Max(pMinLocal.Y, pMaxLocal.Y), bb.Max.Z);

                planTum.CropBox = bb;
                planTum.CropBoxActive = true;
                planTum.CropBoxVisible = false;

                t2.Commit();
            }

            uiview?.ZoomToFit();

            string outPlanClose = Path.Combine(brainDir, "revit_tum_slab_hole_closeup.png");
            if (File.Exists(outPlanClose)) File.Delete(outPlanClose);
            var expOptClose = new ImageExportOptions
            {
                FilePath = outPlanClose,
                FitDirection = FitDirectionType.Horizontal,
                HLRandWFViewsFileType = ImageFileType.PNG,
                ImageResolution = ImageResolution.DPI_150,
                ExportRange = ExportRange.CurrentView,
                ZoomType = ZoomFitType.FitToPage,
                PixelSize = 2000
            };
            doc.ExportImage(expOptClose);

            // Restore overview crop
            using (Transaction t3 = new Transaction(doc, "Restore Plan Tum Crop"))
            {
                t3.Start();

                var bb = planTum.CropBox;
                var tr = bb.Transform;
                var inv = tr.Inverse;

                var pMinWorld = new XYZ(-2.0 * M2FT, -2.5 * M2FT, tr.Origin.Z);
                var pMaxWorld = new XYZ(39.5 * M2FT, 16.5 * M2FT, tr.Origin.Z);

                var pMinLocal = inv.OfPoint(pMinWorld);
                var pMaxLocal = inv.OfPoint(pMaxWorld);

                bb.Min = new XYZ(Math.Min(pMinLocal.X, pMaxLocal.X), Math.Min(pMinLocal.Y, pMaxLocal.Y), bb.Min.Z);
                bb.Max = new XYZ(Math.Max(pMinLocal.X, pMaxLocal.X), Math.Max(pMinLocal.Y, pMaxLocal.Y), bb.Max.Z);

                planTum.CropBox = bb;
                planTum.CropBoxActive = true;
                planTum.CropBoxVisible = false;

                t3.Commit();
            }

            return new { success = true, logs };
        }
    }
}

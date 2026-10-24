using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ExportTumSlabViews
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No active document" };

                string brainDir = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";

                // 1. Find ViewPlan for Tầng Tum
                ViewPlan planTum = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && (v.Name.Contains("TUM", StringComparison.OrdinalIgnoreCase) || (v.GenLevel != null && v.GenLevel.Name.Contains("TUM", StringComparison.OrdinalIgnoreCase))));

                if (planTum != null)
                {
                    uidoc.ActiveView = planTum;

                    using (Transaction t = new Transaction(doc, "Adjust Plan Tum Crop"))
                    {
                        t.Start();

                        // Ensure floor category is visible
                        var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
                        if (floorCat != null && planTum.CanCategoryBeHidden(floorCat.Id))
                        {
                            if (planTum.GetCategoryHidden(floorCat.Id)) planTum.SetCategoryHidden(floorCat.Id, false);
                        }

                        // Set CropBox to encompass whole building
                        var bb = planTum.CropBox;
                        var tr = bb.Transform;
                        var inv = tr.Inverse;

                        var pMinWorld = new XYZ(-2.0 * M2FT, -2.0 * M2FT, tr.Origin.Z);
                        var pMaxWorld = new XYZ(40.0 * M2FT, 17.0 * M2FT, tr.Origin.Z);

                        var pMinLocal = inv.OfPoint(pMinWorld);
                        var pMaxLocal = inv.OfPoint(pMaxWorld);

                        bb.Min = new XYZ(Math.Min(pMinLocal.X, pMaxLocal.X), Math.Min(pMinLocal.Y, pMaxLocal.Y), bb.Min.Z);
                        bb.Max = new XYZ(Math.Max(pMinLocal.X, pMaxLocal.X), Math.Max(pMinLocal.Y, pMaxLocal.Y), bb.Max.Z);

                        planTum.CropBox = bb;
                        planTum.CropBoxActive = true;
                        planTum.CropBoxVisible = false;

                        t.Commit();
                    }

                    var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTum.Id);
                    uiview?.ZoomToFit();

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

                    // Crop close-up around the hole (X: [3m, 10m], Y: [7m, 16m])
                    using (Transaction t2 = new Transaction(doc, "Close Up Plan Tum Hole"))
                    {
                        t2.Start();

                        var bb = planTum.CropBox;
                        var tr = bb.Transform;
                        var inv = tr.Inverse;

                        var pMinWorld = new XYZ(3.0 * M2FT, 7.0 * M2FT, tr.Origin.Z);
                        var pMaxWorld = new XYZ(10.0 * M2FT, 16.0 * M2FT, tr.Origin.Z);

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
                        ImageResolution = ImageResolution.DPI_300,
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

                        var pMinWorld = new XYZ(-2.0 * M2FT, -2.0 * M2FT, tr.Origin.Z);
                        var pMaxWorld = new XYZ(40.0 * M2FT, 17.0 * M2FT, tr.Origin.Z);

                        var pMinLocal = inv.OfPoint(pMinWorld);
                        var pMaxLocal = inv.OfPoint(pMaxWorld);

                        bb.Min = new XYZ(Math.Min(pMinLocal.X, pMaxLocal.X), Math.Min(pMinLocal.Y, pMaxLocal.Y), bb.Min.Z);
                        bb.Max = new XYZ(Math.Max(pMinLocal.X, pMaxLocal.X), Math.Max(pMinLocal.Y, pMaxLocal.Y), bb.Max.Z);

                        planTum.CropBox = bb;
                        planTum.CropBoxActive = true;
                        planTum.CropBoxVisible = false;

                        t3.Commit();
                    }
                }

                // 2. 3D View close-up on Tum and Hole
                View3D v3d = new FilteredElementCollector(doc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Contains("3D"));

                if (v3d != null)
                {
                    uidoc.ActiveView = v3d;
                    var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == v3d.Id);
                    uiview3d?.ZoomToFit();

                    string out3dClose = Path.Combine(brainDir, "revit_tum_slab_3d_overview.png");
                    if (File.Exists(out3dClose)) File.Delete(out3dClose);
                    var expOpt3d = new ImageExportOptions
                    {
                        FilePath = out3dClose,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.PNG,
                        ImageResolution = ImageResolution.DPI_150,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2560
                    };
                    doc.ExportImage(expOpt3d);
                }

                return new { success = true };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

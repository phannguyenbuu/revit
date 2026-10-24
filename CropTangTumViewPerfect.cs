using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CropTangTumViewPerfect
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                ViewPlan planTum = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .FirstOrDefault(v => !v.IsTemplate && (v.Name.IndexOf("TUM", StringComparison.OrdinalIgnoreCase) >= 0 || v.Name.IndexOf("TẦNG TUM", StringComparison.OrdinalIgnoreCase) >= 0));

                if (planTum == null) return new { error = "View Tầng Tum not found" };

                using (Transaction t = new Transaction(doc, "Perfect Crop and Elements for Tang Tum"))
                {
                    t.Start();

                    // 1. Unhide Grids category
                    var gridCat = Category.GetCategory(doc, BuiltInCategory.OST_Grids);
                    if (gridCat != null && planTum.CanCategoryBeHidden(gridCat.Id))
                    {
                        if (planTum.GetCategoryHidden(gridCat.Id)) planTum.SetCategoryHidden(gridCat.Id, false);
                    }

                    // 2. Hide section markers and elevation markers
                    var hideList = new List<ElementId>();

                    var extraViewers = new FilteredElementCollector(doc, planTum.Id)
                        .OfCategory(BuiltInCategory.OST_Viewers)
                        .WhereElementIsNotElementType()
                        .Select(e => e.Id)
                        .ToList();
                    hideList.AddRange(extraViewers);

                    var extraElevs = new FilteredElementCollector(doc, planTum.Id)
                        .OfCategory(BuiltInCategory.OST_Elev)
                        .WhereElementIsNotElementType()
                        .Select(e => e.Id)
                        .ToList();
                    hideList.AddRange(extraElevs);

                    var extraCameras = new FilteredElementCollector(doc, planTum.Id)
                        .OfCategory(BuiltInCategory.OST_Cameras)
                        .WhereElementIsNotElementType()
                        .Select(e => e.Id)
                        .ToList();
                    hideList.AddRange(extraCameras);

                    var extraSectionBoxes = new FilteredElementCollector(doc, planTum.Id)
                        .OfCategory(BuiltInCategory.OST_SectionBox)
                        .WhereElementIsNotElementType()
                        .Select(e => e.Id)
                        .ToList();
                    hideList.AddRange(extraSectionBoxes);

                    var canHide = hideList.Distinct().Where(id =>
                    {
                        var el = doc.GetElement(id);
                        return el != null && el.CanBeHidden(planTum);
                    }).ToList();

                    if (canHide.Count > 0)
                    {
                        try { planTum.HideElements(canHide); } catch { }
                    }

                    // 3. Set Perfect Crop Box around entire building grid
                    var bb = planTum.CropBox;
                    var tr = bb.Transform;
                    var inv = tr.Inverse;

                    var pMinWorld = new XYZ(-2.5 * M2FT, -3.5 * M2FT, tr.Origin.Z);
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

                string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string planOverviewPath = Path.Combine(folder, "plan_tang_tum_perfect.png");
                string planDetailPath = Path.Combine(folder, "plan_tang_tum_detail.png");
                string plan3dImgPath = Path.Combine(folder, "revit_3d_tang1234_with_tum.jpg");

                uidoc.ActiveView = planTum;
                uidoc.Selection.SetElementIds(new List<ElementId>());

                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTum.Id);
                uiview?.ZoomToFit();

                // Export Overview Plan
                if (File.Exists(planOverviewPath)) File.Delete(planOverviewPath);
                var expOpt = new ImageExportOptions
                {
                    FilePath = planOverviewPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.CurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 3800
                };
                doc.ExportImage(expOpt);

                // Now adjust crop box to close-up around Tum tower (Grids 8-11, C-E)
                using (Transaction t2 = new Transaction(doc, "Detail Crop Tang Tum"))
                {
                    t2.Start();
                    var bb = planTum.CropBox;
                    var tr = bb.Transform;
                    var inv = tr.Inverse;

                    // X from 26m to 35.5m, Y from 6m to 16.5m
                    var pMinWorld = new XYZ(26.0 * M2FT, 6.0 * M2FT, tr.Origin.Z);
                    var pMaxWorld = new XYZ(36.0 * M2FT, 16.5 * M2FT, tr.Origin.Z);

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

                if (File.Exists(planDetailPath)) File.Delete(planDetailPath);
                var expOptDetail = new ImageExportOptions
                {
                    FilePath = planDetailPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_300,
                    ExportRange = ExportRange.CurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 2500
                };
                doc.ExportImage(expOptDetail);

                // Restore overview crop box
                using (Transaction t3 = new Transaction(doc, "Restore Overview Crop Tang Tum"))
                {
                    t3.Start();
                    var bb = planTum.CropBox;
                    var tr = bb.Transform;
                    var inv = tr.Inverse;

                    var pMinWorld = new XYZ(-2.5 * M2FT, -3.5 * M2FT, tr.Origin.Z);
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

                // Export 3D view
                var view3d = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

                if (view3d != null)
                {
                    uidoc.ActiveView = view3d;
                    var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                    uiview3d?.ZoomToFit();

                    if (File.Exists(plan3dImgPath)) File.Delete(plan3dImgPath);
                    var expOpt3d = new ImageExportOptions
                    {
                        FilePath = plan3dImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.CurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 3000
                    };
                    doc.ExportImage(expOpt3d);

                    uidoc.ActiveView = planTum;
                }

                // Save Document
                bool docSaved = false;
                try
                {
                    doc.Save(new SaveOptions());
                    docSaved = true;
                }
                catch { }

                return new
                {
                    success = true,
                    planOverviewPath,
                    planDetailPath,
                    plan3dImgPath,
                    docSaved
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

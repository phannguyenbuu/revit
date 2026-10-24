using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class CropTang3ViewPerfect
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            ViewPlan planTang3 = doc.GetElement(new ElementId(1727632L)) as ViewPlan;
            if (planTang3 == null) return new { error = "View 1727632 not found" };

            using (Transaction t = new Transaction(doc, "Perfect View Tang 3 and Grids"))
            {
                t.Start();

                // 1. Extend Grids vertically to span Level 3 (Z = 7.2m)
                var grids = new FilteredElementCollector(doc).OfClass(typeof(Grid)).Cast<Grid>().ToList();
                foreach (var g in grids)
                {
                    try
                    {
                        g.SetVerticalExtents(-10.0 * M2FT, 30.0 * M2FT);
                    }
                    catch { }
                }

                // Unhide Grids category
                var gridCat = Category.GetCategory(doc, BuiltInCategory.OST_Grids);
                if (gridCat != null && planTang3.CanCategoryBeHidden(gridCat.Id))
                {
                    if (planTang3.GetCategoryHidden(gridCat.Id)) planTang3.SetCategoryHidden(gridCat.Id, false);
                }

                // 2. Hide section markers and elevation markers specifically by ElementId
                var hideList = new List<ElementId>
                {
                    new ElementId(749995L),
                    new ElementId(8142L),
                    new ElementId(8174L),
                    new ElementId(8208L),
                    new ElementId(98746L)
                };

                var extraViewers = new FilteredElementCollector(doc, planTang3.Id)
                    .OfCategory(BuiltInCategory.OST_Viewers)
                    .WhereElementIsNotElementType()
                    .Select(e => e.Id)
                    .ToList();
                hideList.AddRange(extraViewers);

                var extraElevs = new FilteredElementCollector(doc, planTang3.Id)
                    .OfCategory(BuiltInCategory.OST_Elev)
                    .WhereElementIsNotElementType()
                    .Select(e => e.Id)
                    .ToList();
                hideList.AddRange(extraElevs);

                var canHide = hideList.Distinct().Where(id =>
                {
                    var el = doc.GetElement(id);
                    return el != null && el.CanBeHidden(planTang3);
                }).ToList();

                if (canHide.Count > 0)
                {
                    try { planTang3.HideElements(canHide); } catch { }
                }

                // 3. Set Perfect Crop Box around building + grid bubbles
                // Building: X in [0.55, 37.15], Y in [0, 13.2]
                // Grids: X in [-1, 39], Y in [-2.5, 15.5]
                var bb = planTang3.CropBox;
                var tr = bb.Transform;
                var inv = tr.Inverse;

                var pMinWorld = new XYZ(-2.5 * M2FT, -3.5 * M2FT, 0.0);
                var pMaxWorld = new XYZ(39.5 * M2FT, 16.5 * M2FT, 0.0);

                var pMinLocal = inv.OfPoint(pMinWorld);
                var pMaxLocal = inv.OfPoint(pMaxWorld);

                bb.Min = new XYZ(Math.Min(pMinLocal.X, pMaxLocal.X), Math.Min(pMinLocal.Y, pMaxLocal.Y), bb.Min.Z);
                bb.Max = new XYZ(Math.Max(pMinLocal.X, pMaxLocal.X), Math.Max(pMinLocal.Y, pMaxLocal.Y), bb.Max.Z);

                planTang3.CropBox = bb;
                planTang3.CropBoxActive = true;
                planTang3.CropBoxVisible = false;

                t.Commit();
            }

            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string planImgPath = Path.Combine(folder, "plan_tang3_perfect.png");
            string plan3dImgPath = Path.Combine(folder, "revit_3d_tang123.jpg");

            uidoc.ActiveView = planTang3;
            uidoc.Selection.SetElementIds(new List<ElementId>());

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTang3.Id);
            uiview?.ZoomToFit();

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
                    PixelSize = 3800
                };
                doc.ExportImage(expOpt);
            }
            catch (Exception ex)
            {
                return new { error = "Plan export failed: " + ex.Message };
            }

            // Export 3D view
            var view3d = new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                ?? new FilteredElementCollector(doc).OfClass(typeof(View3D)).Cast<View3D>().FirstOrDefault(v => !v.IsTemplate);

            if (view3d != null)
            {
                uidoc.ActiveView = view3d;
                var uiview3d = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == view3d.Id);
                uiview3d?.ZoomToFit();

                try
                {
                    if (File.Exists(plan3dImgPath)) File.Delete(plan3dImgPath);
                    var expOpt3d = new ImageExportOptions
                    {
                        FilePath = plan3dImgPath,
                        FitDirection = FitDirectionType.Horizontal,
                        HLRandWFViewsFileType = ImageFileType.JPEGLossless,
                        ImageResolution = ImageResolution.DPI_300,
                        ExportRange = ExportRange.VisibleRegionOfCurrentView,
                        ZoomType = ZoomFitType.FitToPage,
                        PixelSize = 2800
                    };
                    doc.ExportImage(expOpt3d);
                }
                catch { }

                uidoc.ActiveView = planTang3;
            }

            // Also save the document
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
                docSaved,
                planImgPath,
                plan3dImgPath
            };
        }
    }
}

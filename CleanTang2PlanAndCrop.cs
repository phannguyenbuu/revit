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
    public static class CleanTang2PlanAndCrop
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            ViewPlan planTang2 = doc.GetElement(new ElementId(695L)) as ViewPlan;
            if (planTang2 == null) return new { error = "View 695 not found" };

            // Find unplaced rooms or stray room tags in the view
            var unplacedRooms = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .Cast<Room>()
                .Where(r => r.Area < 0.001 || r.Location == null)
                .Select(r => r.Id)
                .ToList();

            using (Transaction t = new Transaction(doc, "Delete Unplaced Template Rooms & Set Crop"))
            {
                t.Start();

                if (unplacedRooms.Count > 0)
                {
                    try { doc.Delete(unplacedRooms); } catch { }
                }

                // Delete any unplaced room tags
                var strayTags = new FilteredElementCollector(doc, planTang2.Id)
                    .OfCategory(BuiltInCategory.OST_RoomTags)
                    .Cast<RoomTag>()
                    .Where(rt => rt.Room == null || rt.TagHeadPosition.X < 0)
                    .Select(rt => rt.Id)
                    .ToList();

                if (strayTags.Count > 0)
                {
                    try { doc.Delete(strayTags); } catch { }
                }

                // Set Crop Box around the building + grid bubbles
                // Building: X in [0.55, 37.15], Y in [0, 13.2]
                // Grids extend to X: -1 to 39, Y: -2.5 to 15.5
                var bb = planTang2.CropBox;
                if (bb != null)
                {
                    bb.Min = new XYZ(-3.5 * M2FT, -4.5 * M2FT, bb.Min.Z);
                    bb.Max = new XYZ(41.0 * M2FT, 17.5 * M2FT, bb.Max.Z);
                    planTang2.CropBox = bb;
                }
                planTang2.CropBoxActive = true;
                planTang2.CropBoxVisible = false;

                t.Commit();
            }

            string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
            string planImgPath = Path.Combine(folder, "plan_tang2_cropped.png");
            string plan3dImgPath = Path.Combine(folder, "revit_3d_tang1_tang2.jpg");

            uidoc.ActiveView = planTang2;
            uidoc.Selection.SetElementIds(new List<ElementId>());

            var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTang2.Id);
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

                uidoc.ActiveView = planTang2;
            }

            return new
            {
                success = true,
                deletedUnplacedRooms = unplacedRooms.Count,
                planImgPath,
                plan3dImgPath
            };
        }
    }
}

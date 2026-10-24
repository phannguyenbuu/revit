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
    public static class ExportTang3CleanPlan
    {
        private const double M2FT = 3.2808398950131235;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                ViewPlan planTang3 = doc.GetElement(new ElementId(1727632L)) as ViewPlan
                    ?? new FilteredElementCollector(doc).OfClass(typeof(ViewPlan)).Cast<ViewPlan>().FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MẶT BẰNG TẦNG 3", StringComparison.OrdinalIgnoreCase));

                if (planTang3 == null) return new { error = "View MẶT BẰNG TẦNG 3 not found" };

                // Find unplaced rooms or stray room tags in the view
                var unplacedRooms = new FilteredElementCollector(doc)
                    .OfCategory(BuiltInCategory.OST_Rooms)
                    .Cast<Room>()
                    .Where(r => r.Area < 0.001 || r.Location == null)
                    .Select(r => r.Id)
                    .ToList();

                using (Transaction t = new Transaction(doc, "Adjust Tang 3 View Settings"))
                {
                    t.Start();
                    if (unplacedRooms.Count > 0)
                    {
                        try { doc.Delete(unplacedRooms); } catch { }
                    }

                    // Delete any stray room tags in Tang 3
                    var strayTags = new FilteredElementCollector(doc, planTang3.Id)
                        .OfCategory(BuiltInCategory.OST_RoomTags)
                        .Cast<RoomTag>()
                        .Where(rt => rt.Room == null || rt.TagHeadPosition.X < 0)
                        .Select(rt => rt.Id)
                        .ToList();

                    if (strayTags.Count > 0)
                    {
                        try { doc.Delete(strayTags); } catch { }
                    }

                    planTang3.CropBoxActive = false;
                    planTang3.CropBoxVisible = false;

                    // Ensure categories are visible
                    var catIds = new[]
                    {
                        BuiltInCategory.OST_Walls,
                        BuiltInCategory.OST_Doors,
                        BuiltInCategory.OST_Windows,
                        BuiltInCategory.OST_Grids,
                        BuiltInCategory.OST_Columns,
                        BuiltInCategory.OST_StructuralColumns,
                        BuiltInCategory.OST_Stairs,
                        BuiltInCategory.OST_TextNotes
                    };

                    foreach (var c in catIds)
                    {
                        var cat = Category.GetCategory(doc, c);
                        if (cat != null && planTang3.CanCategoryBeHidden(cat.Id))
                        {
                            planTang3.SetCategoryHidden(cat.Id, false);
                        }
                    }

                    t.Commit();
                }

                string folder = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697";
                string planImgPath = Path.Combine(folder, "plan_tang3_perfect.png");

                uidoc.ActiveView = planTang3;
                uidoc.Selection.SetElementIds(new List<ElementId>());

                var uiview = uidoc.GetOpenUIViews().FirstOrDefault(v => v.ViewId == planTang3.Id);
                uiview?.ZoomToFit();

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

                return new
                {
                    success = true,
                    planImgPath,
                    viewId = planTang3.Id.Value,
                    viewName = planTang3.Name
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

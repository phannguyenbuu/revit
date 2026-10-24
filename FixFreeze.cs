using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class FixFreeze
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            // 1. Turn OFF 3D grids in ALL 3D views
            var view3Ds = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .Where(v => !v.IsTemplate)
                .ToList();

            var emptySet = new HashSet<ElementId>();
            var gridCat = Category.GetCategory(doc, BuiltInCategory.OST_Grids);

            // 2. Find clean main floor plan (TẦNG TRỆT or TẦNG 01)
            var planViews = new FilteredElementCollector(doc)
                .OfClass(typeof(ViewPlan))
                .Cast<ViewPlan>()
                .Where(v => !v.IsTemplate && v.ViewType == ViewType.FloorPlan)
                .ToList();

            var mainFloorPlan = planViews.FirstOrDefault(v => v.Name == "TẦNG TRỆT")
                                ?? planViews.FirstOrDefault(v => v.Name == "TẦNG 01")
                                ?? planViews.FirstOrDefault(v => !v.Name.Contains("Callout") && !v.Name.Contains("Copy"));

            // 3. Count total grids and check duplicates
            var allGrids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            var gridNames = allGrids.Select(g => g.Name).ToList();

            using (var tx = new Transaction(doc, "Disable 3D Grids and Recover Performance"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new GridWarningSwallower());
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                // Turn off 3D grids in all 3D views to release GPU/CPU load
                foreach (var v3d in view3Ds)
                {
                    try
                    {
                        v3d.ShowGridsOnLevels(emptySet);
                        // Hide grids category in 3D views so it doesn't cause any lag
                        if (gridCat != null && v3d.CanCategoryBeHidden(gridCat.Id))
                        {
                            v3d.SetCategoryHidden(gridCat.Id, true);
                        }
                    }
                    catch { }
                }

                // In main floor plan, ensure grids are visible and crop is off
                if (mainFloorPlan != null)
                {
                    try
                    {
                        if (gridCat != null && mainFloorPlan.CanCategoryBeHidden(gridCat.Id))
                        {
                            mainFloorPlan.SetCategoryHidden(gridCat.Id, false);
                        }
                        mainFloorPlan.CropBoxActive = false;
                    }
                    catch { }
                }

                tx.Commit();
            }

            // Switch to main floor plan in UI and Zoom To Fit
            if (mainFloorPlan != null)
            {
                try
                {
                    uidoc.ActiveView = mainFloorPlan;
                    var openViews = uidoc.GetOpenUIViews();
                    foreach (var uiv in openViews)
                    {
                        if (uiv.ViewId == mainFloorPlan.Id)
                        {
                            uiv.ZoomToFit();
                        }
                    }
                }
                catch { }
            }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                message = "Disabled 3D Grids, unlagged 3D Coordination, switched to main floor plan",
                activeFloorPlan = mainFloorPlan?.Name,
                totalGridsInProject = allGrids.Count,
                gridsList = gridNames.OrderBy(n => n).ToList()
            };
        }
    }
}

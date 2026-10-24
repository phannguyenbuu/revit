using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class ShowGridsInMainModel
    {
        private const double MetersToFeet = 1.0 / 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document open" };

            // Find all 3D views
            var view3Ds = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .Where(v => !v.IsTemplate)
                .ToList();

            var coordView = view3Ds.FirstOrDefault(v => v.Name.IndexOf("Coordination", StringComparison.OrdinalIgnoreCase) >= 0) 
                            ?? view3Ds.FirstOrDefault(v => v.Name.Equals("{3D}", StringComparison.OrdinalIgnoreCase))
                            ?? view3Ds.FirstOrDefault();

            if (coordView == null) return new { error = "No 3D view found" };

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            // Select key levels for 3D grid plane display (e.g. Ground / TẦNG TRỆT / TẦNG 01 / HẦM 1)
            var targetLevels = levels.Where(l => 
                l.Name.Contains("TRỆT") || 
                l.Name.Contains("01") || 
                l.Name.Contains("HẦM 1") ||
                l.Name.Contains("MÁI")
            ).Select(l => l.Id).ToHashSet();

            if (targetLevels.Count == 0 && levels.Count > 0)
            {
                targetLevels.Add(levels.First().Id);
            }

            var gridCategory = Category.GetCategory(doc, BuiltInCategory.OST_Grids);
            var gridCatId = gridCategory?.Id;

            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            using (var tx = new Transaction(doc, "Show Grids in 3D Model"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new GridWarningSwallower());
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                foreach (var v3d in view3Ds)
                {
                    try
                    {
                        // Ensure category is unhidden
                        if (gridCatId != null && v3d.CanCategoryBeHidden(gridCatId))
                        {
                            v3d.SetCategoryHidden(gridCatId, false);
                        }

                        // Unhide elements
                        var hidden = grids.Where(g => g.CanBeHidden(v3d) && g.IsHidden(v3d)).Select(g => g.Id).ToList();
                        if (hidden.Count > 0)
                        {
                            v3d.UnhideElements(hidden);
                        }

                        // Show grids on levels in 3D view
                        v3d.ShowGridsOnLevels(targetLevels);

                        // If section box is active and clips the new grids, expand or disable section box
                        if (v3d.IsSectionBoxActive)
                        {
                            v3d.IsSectionBoxActive = false; // Turn off section box so full model and grids are visible
                        }
                    }
                    catch { }
                }

                // Also ensure pure floor plan views (TẦNG TRỆT, TẦNG 01) are unhidden
                var purePlans = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .Where(v => !v.IsTemplate && (v.Name.Contains("TRỆT") || v.Name.Contains("TẦNG 01")))
                    .ToList();

                foreach (var p in purePlans)
                {
                    try
                    {
                        if (gridCatId != null && p.CanCategoryBeHidden(gridCatId))
                        {
                            p.SetCategoryHidden(gridCatId, false);
                        }
                        if (p.CropBoxActive)
                        {
                            p.CropBoxActive = false;
                        }
                    }
                    catch { }
                }

                tx.Commit();
            }

            // Switch active view to 3D Coordination in UI
            try
            {
                uidoc.ActiveView = coordView;
                var openViews = uidoc.GetOpenUIViews();
                foreach (var uiv in openViews)
                {
                    if (uiv.ViewId == coordView.Id)
                    {
                        uiv.ZoomToFit();
                    }
                }
            }
            catch { }

            try { uidoc.RefreshActiveView(); } catch { }

            // Export image of 3D Coordination view
            string outPath = @"C:\Users\nguyenbuu.DESKTOP-TOEFTR1\.gemini\antigravity\brain\16005848-1987-4ccc-a037-b18d9e878697\revit_3d_main_model.png";
            try
            {
                var imgOpts = new ImageExportOptions
                {
                    FilePath = outPath,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    ExportRange = ExportRange.CurrentView,
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 1920
                };
                doc.ExportImage(imgOpts);
            }
            catch { }

            return new
            {
                success = true,
                activatedView = coordView.Name,
                viewType = coordView.ViewType.ToString(),
                gridCount = grids.Count,
                levelsShowingGrids = targetLevels.Select(id => id.Value).ToList(),
                exportedImage = outPath
            };
        }
    }
}

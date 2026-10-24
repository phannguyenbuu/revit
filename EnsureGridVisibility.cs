using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class EnsureGridVisibility
    {
        private const double MetersToFeet = 1.0 / 0.3048;
        private const double FeetToMeters = 0.3048;

        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No active document open" };

            var activeView = uidoc.ActiveView;
            if (activeView == null) return new { error = "No active view" };

            // 1. Get level elevation extents
            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .OrderBy(l => l.Elevation)
                .ToList();

            double minElev = levels.Count > 0 ? levels.First().Elevation - (15.0 * MetersToFeet) : -50.0 * MetersToFeet;
            double maxElev = levels.Count > 0 ? levels.Last().Elevation + (15.0 * MetersToFeet) : 100.0 * MetersToFeet;

            var grids = new FilteredElementCollector(doc)
                .OfClass(typeof(Grid))
                .Cast<Grid>()
                .ToList();

            var gridCategory = Category.GetCategory(doc, BuiltInCategory.OST_Grids);
            var gridCatId = gridCategory?.Id;

            int updatedExtentsCount = 0;
            var errors = new List<string>();

            // Target bounding box for new grids: X: -15m to 185m, Y: -15m to 165m
            double minX = -20.0 * MetersToFeet;
            double maxX = 190.0 * MetersToFeet;
            double minY = -20.0 * MetersToFeet;
            double maxY = 170.0 * MetersToFeet;

            using (var tx = new Transaction(doc, "Ensure Grids Visible On All Plans"))
            {
                var opts = tx.GetFailureHandlingOptions();
                opts.SetFailuresPreprocessor(new GridWarningSwallower());
                opts.SetClearAfterRollback(true);
                tx.SetFailureHandlingOptions(opts);

                tx.Start();

                // 2. Set vertical extents for all grids to span all levels
                foreach (var g in grids)
                {
                    try
                    {
                        g.SetVerticalExtents(minElev, maxElev);
                        updatedExtentsCount++;
                    }
                    catch (Exception ex)
                    {
                        errors.Add($"SetVerticalExtents for {g.Name}: {ex.Message}");
                    }
                }

                // 3. Process all floor plan views and the active view
                var planViews = new FilteredElementCollector(doc)
                    .OfClass(typeof(ViewPlan))
                    .Cast<ViewPlan>()
                    .Where(v => !v.IsTemplate)
                    .ToList();

                var targetViews = new List<View>(planViews);
                if (!targetViews.Any(v => v.Id == activeView.Id))
                {
                    targetViews.Add(activeView);
                }

                foreach (var v in targetViews)
                {
                    try
                    {
                        // Unhide grids category
                        if (gridCatId != null && v.CanCategoryBeHidden(gridCatId))
                        {
                            if (v.GetCategoryHidden(gridCatId))
                            {
                                v.SetCategoryHidden(gridCatId, false);
                            }
                        }

                        // Unhide individual hidden grid elements
                        var hiddenGrids = grids.Where(g => g.CanBeHidden(v) && g.IsHidden(v)).Select(g => g.Id).ToList();
                        if (hiddenGrids.Count > 0)
                        {
                            v.UnhideElements(hiddenGrids);
                        }

                        // If CropBox is active and smaller than the new grids, expand cropbox
                        if (v.CropBoxActive)
                        {
                            var box = v.CropBox;
                            if (box != null)
                            {
                                box.Min = new XYZ(Math.Min(box.Min.X, minX), Math.Min(box.Min.Y, minY), box.Min.Z);
                                box.Max = new XYZ(Math.Max(box.Max.X, maxX), Math.Max(box.Max.Y, maxY), box.Max.Z);
                                v.CropBox = box;
                            }
                        }
                    }
                    catch { }
                }

                // If active view has crop box, expand it
                if (activeView.CropBoxActive)
                {
                    try
                    {
                        var box = activeView.CropBox;
                        box.Min = new XYZ(Math.Min(box.Min.X, minX), Math.Min(box.Min.Y, minY), box.Min.Z);
                        box.Max = new XYZ(Math.Max(box.Max.X, maxX), Math.Max(box.Max.Y, maxY), box.Max.Z);
                        activeView.CropBox = box;
                    }
                    catch { }
                }

                tx.Commit();
            }

            // 4. Zoom to fit on open UI views
            try
            {
                var openViews = uidoc.GetOpenUIViews();
                foreach (var uiv in openViews)
                {
                    if (uiv.ViewId == activeView.Id)
                    {
                        uiv.ZoomToFit();
                    }
                }
            }
            catch { }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                activeView = activeView.Name,
                viewType = activeView.ViewType.ToString(),
                gridCount = grids.Count,
                updatedExtentsCount = updatedExtentsCount,
                minElevationMeters = Math.Round(minElev * FeetToMeters, 2),
                maxElevationMeters = Math.Round(maxElev * FeetToMeters, 2),
                errors = errors
            };
        }
    }
}

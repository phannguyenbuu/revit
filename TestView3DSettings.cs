using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class TestView3DSettings
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            try
            {
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null) return new { error = "No doc" };

                var view = uidoc.ActiveView as View3D;
                if (view == null) return new { error = "Active view is not 3D: " + uidoc.ActiveView?.Name };

                var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
                var gridCat = Category.GetCategory(doc, BuiltInCategory.OST_Grids);

                var levels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .ToList();

                var groundLevel = levels.FirstOrDefault(l => l.Name.Contains("TRỆT")) ?? levels.FirstOrDefault();

                using (var tx = new Transaction(doc, "Adjust 3D View"))
                {
                    tx.Start();

                    // 1. Hide Floors in this 3D view
                    if (floorCat != null && view.CanCategoryBeHidden(floorCat.Id))
                    {
                        view.SetCategoryHidden(floorCat.Id, true);
                    }

                    // 2. Unhide Grids category in this 3D view
                    if (gridCat != null && view.CanCategoryBeHidden(gridCat.Id))
                    {
                        view.SetCategoryHidden(gridCat.Id, false);
                    }

                    // 3. Show grids on TẦNG TRỆT only
                    if (groundLevel != null)
                    {
                        var singleLevelSet = new HashSet<ElementId> { groundLevel.Id };
                        view.ShowGridsOnLevels(singleLevelSet);
                    }

                    tx.Commit();
                }

                try { uidoc.RefreshActiveView(); } catch { }

                return new
                {
                    success = true,
                    viewName = view.Name,
                    floorCategoryHidden = floorCat != null && view.GetCategoryHidden(floorCat.Id),
                    gridCategoryHidden = gridCat != null && view.GetCategoryHidden(gridCat.Id),
                    levelsShowingGrids = view.GetLevelsThatShowGrids().Select(id => id.Value).ToList()
                };
            }
            catch (Exception ex)
            {
                return new { error = ex.ToString() };
            }
        }
    }
}

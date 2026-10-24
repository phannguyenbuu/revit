using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;

namespace RevitScript
{
    public static class Apply3DSettingsToAll
    {
        public static object Run(UIApplication uiapp, JsonElement args)
        {
            var uidoc = uiapp.ActiveUIDocument;
            var doc = uidoc?.Document;
            if (doc == null) return new { error = "No doc" };

            var floorCat = Category.GetCategory(doc, BuiltInCategory.OST_Floors);
            var gridCat = Category.GetCategory(doc, BuiltInCategory.OST_Grids);

            var levels = new FilteredElementCollector(doc)
                .OfClass(typeof(Level))
                .Cast<Level>()
                .ToList();

            var groundLevel = levels.FirstOrDefault(l => l.Name.Contains("TRỆT")) ?? levels.FirstOrDefault();

            var view3Ds = new FilteredElementCollector(doc)
                .OfClass(typeof(View3D))
                .Cast<View3D>()
                .Where(v => !v.IsTemplate)
                .ToList();

            int updatedViews = 0;

            using (var tx = new Transaction(doc, "Apply Clean 3D Settings"))
            {
                tx.Start();

                foreach (var v in view3Ds)
                {
                    try
                    {
                        // 1. Hide Floors in 3D
                        if (floorCat != null && v.CanCategoryBeHidden(floorCat.Id))
                        {
                            v.SetCategoryHidden(floorCat.Id, true);
                        }

                        // 2. Unhide Grids category in 3D
                        if (gridCat != null && v.CanCategoryBeHidden(gridCat.Id))
                        {
                            v.SetCategoryHidden(gridCat.Id, false);
                        }

                        // 3. Show grids on TẦNG TRỆT only
                        if (groundLevel != null)
                        {
                            var singleLevelSet = new HashSet<ElementId> { groundLevel.Id };
                            v.ShowGridsOnLevels(singleLevelSet);
                        }

                        updatedViews++;
                    }
                    catch { }
                }

                tx.Commit();
            }

            try { uidoc.RefreshActiveView(); } catch { }

            return new
            {
                success = true,
                updatedViewsCount = updatedViews,
                groundLevel = groundLevel?.Name
            };
        }
    }
}
